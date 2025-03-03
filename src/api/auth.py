from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    id: str
    username: str
    email: str

# For testing, always return a test user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    return User(
        id="test_user_1",
        username="test_user",
        email="test@example.com"
    ) 