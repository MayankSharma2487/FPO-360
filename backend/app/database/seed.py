from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission

DEFAULT_ROLES = [
    {"name": "Super Admin", "description": "Full system access across all organizations"},
    {"name": "FPO Admin", "description": "Full access within their own organization"},
    {"name": "Manager", "description": "Manage day-to-day operations of the organization"},
    {"name": "Accountant", "description": "Manage financial records and transactions"},
    {"name": "Viewer", "description": "Read-only access to organization data"},
]

DEFAULT_PERMISSIONS = [
    {"name": "user.create", "description": "Create users"},
    {"name": "user.read", "description": "View users"},
    {"name": "user.update", "description": "Update users"},
    {"name": "user.delete", "description": "Delete users"},
    {"name": "organization.create", "description": "Create organizations"},
    {"name": "organization.read", "description": "View organizations"},
    {"name": "organization.update", "description": "Update organizations"},
    {"name": "role.manage", "description": "Manage roles and permissions"},
    {"name": "dashboard.view", "description": "View dashboard summary"},
]

ROLE_PERMISSION_MAP = {
    "Super Admin": [p["name"] for p in DEFAULT_PERMISSIONS],
    "FPO Admin": [
        "user.create",
        "user.read",
        "user.update",
        "organization.read",
        "organization.update",
        "dashboard.view"
    ],
    "Manager": [
        "user.read",
        "organization.read",
        "dashboard.view"
    ],
    "Accountant": [
        "user.read",
        "organization.read",
        "dashboard.view"
    ],
    "Viewer": [
        "user.read",
        "organization.read"
    ],
}


def seed_roles_and_permissions(db: Session):

    permission_lookup = {}

    for permission_data in DEFAULT_PERMISSIONS:

        permission = (
            db.query(Permission)
            .filter(Permission.name == permission_data["name"])
            .first()
        )

        if not permission:
            permission = Permission(**permission_data)
            db.add(permission)
            db.commit()
            db.refresh(permission)

        permission_lookup[permission.name] = permission

    for role_data in DEFAULT_ROLES:

        role = (
            db.query(Role)
            .filter(Role.name == role_data["name"])
            .first()
        )

        if not role:
            role = Role(**role_data)
            db.add(role)
            db.commit()
            db.refresh(role)

        existing_permission_ids = {
            rp.permission_id for rp in role.role_permissions
        }

        for permission_name in ROLE_PERMISSION_MAP.get(role.name, []):
            permission = permission_lookup.get(permission_name)

            if permission and permission.id not in existing_permission_ids:
                db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id
                    )
                )

        db.commit()

    print("✅ Default Roles & Permissions Seeded Successfully")