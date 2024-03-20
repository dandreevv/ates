import asyncio
import os
import random
import uuid
from contextlib import asynccontextmanager
import jwt
import uvicorn
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Response, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from tasks import crud
from tasks.dependencies import get_user, get_db
from tasks.kafka import consume, send_cud_task, send_assigned_task, send_done_task
from tasks.models import Base, Task, User
from tasks.db import engine

os.environ.setdefault('AUTHLIB_INSECURE_TRANSPORT', '1')


@asynccontextmanager
async def lifespan(_: FastAPI):
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
async def login(request: Request):
    return await oauth.test.authorize_redirect(request, REDIRECT_URI)


@app.get('/callback')
async def callback_handling(request: Request, response: Response):
    await oauth.test.authorize_access_token(request)

    res = oauth.test.get('/api/me')
    userinfo = res.json()

    token = jwt.encode(
        {
            "user_id": userinfo["id"],
        },
        "secret",
        algorithm="HS256",
    )
    response.set_cookie(key="session_token", value=token)
    return "OK"


@app.get("/tasks")
def all_tasks(user: User = Depends(get_user), db: Session = Depends(get_db)):
    if user.role in {"admin", "manager"}:
        return crud.get_all_tasks(db)
    return crud.get_tasks_by_assigner(db=db, user_id=user.id)


@app.post("/tasks")
def create_tasks(request: Request, user: User = Depends(get_user), db: Session = Depends(get_db)):
    assigner = crud.find_random_developer(db)
    body = await request.json()
    data = {
        "public_id": uuid.uuid4(),
        "title": body["title"],
        "assigner_id": assigner.id,
        "status": "to do",
        "created_by": user.id,
    }
    task = Task(**data)
    crud.add_task(db, task)
    send_cud_task(task)
    send_assigned_task(task, assigner)
    return


@app.post("/tasks/{task_id}")
def done_tasks(task_id: int, user: User = Depends(get_user), db: Session = Depends(get_db)):
    task = crud.get_tasks_by_id(db, task_id)
    if user.id != task.assigner_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    task.status = "done"
    db.commit()
    assigner = crud.get_user_by_id(db, task.assigner_id)
    send_done_task(task, assigner)
    return


@app.get("/shuffle")
def shuffle_tasks(user: User = Depends(get_user), db: Session = Depends(get_db)):
    if user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Unauthorized")
    tasks = crud.get_all_open_tasks(db)
    for task in tasks:
        assigner = crud.find_random_developer(db)
        task.assigner_id = assigner.id
        send_assigned_task(task, assigner)
    db.commit()
    return


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
