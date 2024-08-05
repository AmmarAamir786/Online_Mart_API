import datetime
from sqlmodel import Session, select
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from user_service.models import User, TokenData
from user_service.db import get_session

SECRET_KEY = "n415M6OrVnR4Dr1gyErpta0wSKQ2cMzK"  # Use the secret key from Kong setup
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_from_db(session: Session, username: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
    if username:
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        if user:
            return user
    if email:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if user:
            return user
    return None

def create_access_token(data: dict, expires_delta: Optional[int] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + datetime.timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        email: str = payload.get("email")
        if username is None or email is None:
            raise credential_exception
        token_data = TokenData(username=username, email=email)
    except JWTError:
        raise credential_exception

    user = get_user_from_db(session, username=token_data.username)
    if user is None:
        raise credential_exception
    return user
