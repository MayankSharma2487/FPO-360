from app.database.database import Base, engine, SessionLocal

from app.models.organization import Organization
from app.models.organization_settings import OrganizationSettings
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User

from app.database.seed import seed_roles_and_permissions

Base.metadata.create_all(bind=engine)

print("✅ Tables Created Successfully")

db = SessionLocal()

try:
    seed_roles_and_permissions(db)
finally:
    db.close()