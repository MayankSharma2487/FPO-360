from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_all(self, organization_id: Optional[int] = None) -> List[User]:
        query = self.db.query(User)

        if organization_id is not None:
            query = query.filter(User.organization_id == organization_id)

        return query.all()

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def toggle_active(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_role(self, user: User, role_id: int) -> User:
        user.role_id = role_id
        self.db.commit()
        self.db.refresh(user)
        return user

    def count_all(self) -> int:
        return self.db.query(User).count()

    def count_active(self) -> int:
        return (
            self.db.query(User)
            .filter(User.is_active == True)
            .count()
        )