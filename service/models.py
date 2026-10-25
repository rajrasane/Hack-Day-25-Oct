"""User Profile Model - Written originally using Pydantic v1.x syntax.
Upgrading to Pydantic v2.x requires semantic refactoring by Kepler:
- `class Config` -> `model_config = ConfigDict(...)`
- `@validator` -> `@field_validator`
- `.dict()` -> `.model_dump()`
"""
from typing import Optional
from pydantic import BaseModel, validator


class UserProfile(BaseModel):
    user_id: int
    username: str
    email: str
    bio: Optional[str] = None
    is_active: bool = True

    @validator("username")
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v.lower()

    class Config:
        allow_mutation = True
        schema_extra = {
            "example": {
                "user_id": 101,
                "username": "sre_admin",
                "email": "sre@cloudnativepune.org",
                "bio": "DevOps & SRE Engineer",
                "is_active": True,
            }
        }
