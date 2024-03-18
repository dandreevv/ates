import asyncio
import os
from contextlib import asynccontextmanager
import jwt
import uvicorn
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Response, Depends
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from billing import crud
from billing.dependencies import get_user, get_db
from billing.kafka import consume
from billing.models import Base, User
from billing.db import engine

os.environ.setdefault('AUTHLIB_INSECURE_TRANSPORT', '1')


@asynccontextmanager
async def lifespan(_: FastAPI):
    asyncio.create_task(consume(["tasks", "tasks.assigned", "tasks.done"]))
    yield

Base.metadata.create_all(bind=engine)
app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="some-random-string")

CLIENT_ID = 'sdfDkdDFHSDfhskjf3jd8Enx'
CLIENT_SECRET = 'sdfJSDFjsdfjfjSDJF#$5J23sAasdoxFjsdVNcSDfSDJF$44'
REDIRECT_URI = 'http://127.0.0.1:9000/callback'

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


@app.get("/transactions")
def all_billing(user: User = Depends(get_user), db: Session = Depends(get_db)):
    if user.role in {"admin", "accounter"}:
        return crud.get_transactions_summary(db)
    return crud.get_transactions_by_assigner(db=db, user_id=user.id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
