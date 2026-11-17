import hashlib
import hmac
import secrets
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from backend.user_store import UsernameTaken
from backend.postgres_user_store import configured_user_store



router = APIRouter(prefix="/auth", tags=["Kullanıcı"])
bearer = HTTPBearer(auto_error=False)

user_store = configured_user_store()
sessions = {}
lock = Lock()


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)


def public_user(user):
    return {"user_id": user["user_id"], "username": user["username"]}


@router.post("/register", status_code=201)
def register(data: Credentials):
    username = data.username.strip()
    if not username:
        raise HTTPException(422, "Kullanıcı adı boş olamaz.")

    salt = secrets.token_bytes(16)
    password_hash = hash_password(data.password, salt)

    try:
        user = user_store.create(username, salt, password_hash)
    except UsernameTaken as error:
        raise HTTPException(409, "Bu kullanıcı adı zaten alınmış.") from error

    return public_user(user)


@router.post("/login")
def login(data: Credentials):
    user = user_store.find_by_username(data.username.strip())

    if user is None or not hmac.compare_digest(
        hash_password(data.password, user["salt"]), user["password_hash"]
    ):
        raise HTTPException(401, "Kullanıcı adı veya şifre hatalı.")

    token = secrets.token_urlsafe(32)
    with lock:
        sessions[token] = user["username"]

    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


def session_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if credentials is None:
        raise HTTPException(401, "Giriş yapmalısın.")
    return credentials.credentials


def current_user(token: str = Depends(session_token)):
    with lock:
        username = sessions.get(token)

    if username is None:
        raise HTTPException(401, "Oturum geçersiz. Tekrar giriş yap.")

    user = user_store.find_by_username(username)
    if user is None:
        raise HTTPException(401, "Oturum geçersiz. Tekrar giriş yap.")

    return public_user(user)


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return user


@router.post("/logout")
def logout(token: str = Depends(session_token)):
    with lock:
        if sessions.pop(token, None) is None:
            raise HTTPException(401, "Oturum geçersiz.")
    return {"message": "Çıkış yapıldı."}