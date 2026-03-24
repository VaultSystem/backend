from datetime import datetime

from pydantic import BaseModel


class UserReadLightSchema(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str


class UserProfileReadSSchema(UserReadLightSchema):
    last_login: datetime
    email_verified: bool
    mfa_enabled: bool
    date_joined: datetime
