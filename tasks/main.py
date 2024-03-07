import asyncio
import json
import os
from contextlib import asynccontextmanager
import jwt
import uvicorn
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Response, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from apps.tasks import crud
from apps.tasks.kafka import consume
from apps.tasks.models import Base, Tasks
from apps.tasks.db import engine, get_db

os.environ.setdefault('AUTHLIB_INSECURE_TRANSPORT', '1')


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(consume(["accounts", "accounts.updated"]))
    yield

Base.metadata.create_all(bind=engine)
app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="some-random-string")

CLIENT_ID = 'w0JhHIaIgeNUsEh2ndTMRALo'
CLIENT_SECRET = 'GvHjYnWLAmUdRl3xFbaLEwY2QnJEMMMG7C9Ijfm4XEQUKPNE'
REDIRECT_URI = 'http://127.0.0.1:8000/callback'

oauth = OAuth()
oauth.register(
    'test',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url='http://127.0.0.1:5000',
    access_token_url='http://127.0.0.1:5000/oauth/token',
    authorize_url='http://127.0.0.1:5000/oauth/authorize',
    client_kwargs={
        'scope': 'profile',
    },
)


@app.get("/login")
async def login_via_google(request: Request):
    return await oauth.test.authorize_redirect(request, REDIRECT_URI)


@app.get('/callback')
async def callback_handling(request: Request, response: Response):
    await oauth.test.authorize_access_token(request)

    res = oauth.test.get('/api/me')
    userinfo = res.json()

    token = jwt.encode(
        {
            "user_id": userinfo["public_id"],
            "role": userinfo["role"],
        },
        "secret",
        algorithm="HS256",
    )
    response.set_cookie(key="session_token", value=token)
    return "OK"


@app.get("/tasks")
def all_tasks(session_token: Cookie(), db: Session = Depends(get_db)):
    token = jwt.decode(session_token, "secret", algorithm="HS256")
    user_id = token["user_id"]
    role = token["role"]
    db_user = crud.get_user_by_id(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    if role in {"admin", "manager"}:
        return crud.get_all_tasks(db)
    return crud.get_tasks_by_assigner(db=db, user_id=user_id)


@app.post("/tasks")
def create_tasks(session_token: Cookie(), request: Request, db: Session = Depends(get_db)):
    token = jwt.decode(session_token, "secret", algorithm="HS256")
    user_id = token["user_id"]
    db_user = crud.get_user_by_id(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    assigner = crud.find_random_developer(db)
    body = request.json()
    task = Tasks(
        title=body["title"],
        assigner_id=assigner.id,
        status="new",
    )
    return crud.add_task(db, task)


@app.get("/shuffle")
def shuffle_tasks(session_token: Cookie(), db: Session = Depends(get_db)):
    token = jwt.decode(session_token, "secret", algorithm="HS256")
    user_id = token["user_id"]
    role = token["role"]
    db_user = crud.get_user_by_id(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    if role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Unauthorized")
    tasks = crud.get_all_open_tasks(db)
    for task in tasks:
        task.assigner_id = crud.find_random_developer(db).id
        producer.produce('tasks.assigned', json.dumps(task.to_dict()))
    db.commit()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
