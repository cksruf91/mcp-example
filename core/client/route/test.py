import datetime as dt

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

test_router = APIRouter(prefix='/test', tags=['test'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='test/auth/token')

SECRET_KEY = "your-secret-key"


class AuthCheckRequest(BaseModel):
    sample: str = Field(default='check?')


class AuthStatusResponse(BaseModel):
    result: bool = Field(default=False)


@test_router.post("/auth/token/")
async def issue_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # some user management step
    payload = {
        "sub": form_data.username,
        "exp": dt.datetime.now(dt.UTC) + dt.timedelta(seconds=10),  # Expiration
        "iat": dt.datetime.now(dt.UTC),  # Issued At
    }
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm='HS256')
    return {"token_type": "bearer", "access_token": token}


async def validate_token(token: str = Depends(oauth2_scheme)) -> None:
    try:
        _ = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    return None


@test_router.post('/auth/check', dependencies=[Depends(validate_token)])
async def check_auth(request: AuthCheckRequest) -> AuthStatusResponse:
    print(f'auth check, request {request}')
    return AuthStatusResponse(result=True)


@test_router.get('/stream')
async def get_chatting_message_in_stream() -> StreamingResponse:
    async def fake_stream():
        import asyncio
        data = """
if you hold a gun and I hold a gun, we can talk about the law.
If you hold a knife and I hold a knife, we can talk about rules.
If you come empty handed and I come empty handed, we can talk about reason.
But if you have a gun and I only have a knife, then the truth lies in your hands.
If you have a gun and I have nothing, what you hold isn't just a weapon, it's my life.
The concepts of laws, rules and morality only hold meaning when they are based on equality.
The harsh truth of this world is that when money speaks, truth goes silent. And when power speaks, even money takes three steps back.
Those who create the rules are often the first to break them. Rules are chains for the weak, tools for the strong.
In this world, anything good must be fought for.
The masters of the game are fiercely competing for resources while only the weak sit idly, waiting to be given a share.
"""
        buffer = []
        for char in data:
            await asyncio.sleep(0.01)
            if char == '\n':
                print(''.join(buffer))
                buffer = []
            else:
                buffer.append(char)
            yield char

    return StreamingResponse(
        fake_stream(),
        media_type="text/event-stream"
    )
