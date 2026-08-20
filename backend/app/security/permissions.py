from app.modules.users.models import UserRole

Permission = str

# Explicit permission catalogue (project spec §12). Kept as code, not a DB table:
# the role set is small and fixed, so a table would add indirection without benefit.
CUSTOMER_PERMISSIONS: set[Permission] = {
    "product.read",
    "category.read",
    "order.read.own",
    "order.create.own",
    "wallet.read.own",
    "ticket.read.own",
    "ticket.create.own",
}

SUPPORT_PERMISSIONS: set[Permission] = CUSTOMER_PERMISSIONS | {
    "ticket.read",
    "ticket.respond",
    "ticket.manage",
    "order.read",
    "user.read",
}

ADMIN_PERMISSIONS: set[Permission] = SUPPORT_PERMISSIONS | {
    "product.create",
    "product.update",
    "product.delete",
    "category.manage",
    "order.manage",
    "user.manage",
    "wallet.manage",
    "payment.read",
    "payment.manage",
    "report.read",
    "audit.read",
}

SUPER_ADMIN_PERMISSIONS: set[Permission] = ADMIN_PERMISSIONS | {
    "user.role.manage",
}

ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.customer: CUSTOMER_PERMISSIONS,
    UserRole.support: SUPPORT_PERMISSIONS,
    UserRole.admin: ADMIN_PERMISSIONS,
    UserRole.super_admin: SUPER_ADMIN_PERMISSIONS,
}


def role_has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
