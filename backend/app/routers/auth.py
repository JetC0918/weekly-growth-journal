from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import create_access_token, hash_password, verify_password
from ..models import AuthToken, Credentials
from ..store import JournalStore, UserRecord, get_store

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
def register(credentials: Credentials, store: JournalStore = Depends(get_store)) -> AuthToken:
    if store.user_by_username(credentials.username):
        raise HTTPException(status_code=409, detail="Username is already registered")
    password_hash = hash_password(credentials.password)
    password_salt, _ = password_hash.split("$", maxsplit=1)
    user = UserRecord(credentials.username, password_salt, password_hash)
    store.add_user(user)
    return AuthToken(accessToken=create_access_token(user.id))


@router.post("/login", response_model=AuthToken)
def login(credentials: Credentials, store: JournalStore = Depends(get_store)) -> AuthToken:
    user = store.user_by_username(credentials.username)
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    return AuthToken(accessToken=create_access_token(user.id))
