from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: str | None = None


class LoginRequest(BaseModel):
    username: str  # Can be email or username
    password: str