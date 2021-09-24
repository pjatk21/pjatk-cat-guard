import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass()
class VerificationCode:
    code: str
    created: datetime
    who: str
    email: str
    user_id: int

    @property
    def has_expired(self):
        return datetime.now() - self.created > timedelta(minutes=5)

    @staticmethod
    def create(username: str, email: str, user_id: int):
        return VerificationCode(
            uuid.uuid4().__str__().split("-")[0][::-1],  # reversed first part of uuid
            datetime.now(),
            username,
            email,
            user_id,
        )
