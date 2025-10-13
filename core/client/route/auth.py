import datetime as dt

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

auth_router = APIRouter(prefix='/auth', tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')

SECRET_KEY = "your-secret-key"


class AuthCheckRequest(BaseModel):
    sample: str = Field(default='check?')


@auth_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print("access")
    print("\t", form_data.username, form_data.password, form_data.scopes)

    # some user management step

    payload = {
        "sub": form_data.username,
        "exp": dt.datetime.now(dt.UTC) + dt.timedelta(seconds=10),  # Expiration 만료 시간
        "iat": dt.datetime.now(dt.UTC),  # Issued At 발행 시간
    }
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm='HS256')
    return {"token_type": "bearer", "access_token": token}


async def validate_token(token: str = Depends(oauth2_scheme)) -> None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    print(payload)
    return None

#
# @auth_router.post('/check', dependencies=[Depends(validate_token)])
# async def check_auth(request: AuthCheckRequest) -> Token:
#     print(f'auth check, request {request}')
#     return Token(access_token='username', token_type='bearer', expires_in=3600)
