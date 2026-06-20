"""
RBAC seed data — upserts permissions, roles, and role-permission assignments.

Derived from docs/schema.sql Section 22 (Seed Data).
Schema.sql defines the roles and permissions; this module defines which
role gets which permissions (derived from the role descriptions).
"""

from sqlmodel import Session, select

from app.models.rbac import Permission, Role, RolePermission

# ---------------------------------------------------------------------------
# Permissions (from schema.sql lines 832-886 + items)
# ---------------------------------------------------------------------------

SEED_PERMISSIONS: list[dict] = [
    # Patients
    {
        "resource": "patients",
        "action": "create",
        "description": "Register a new patient",
    },
    {
        "resource": "patients",
        "action": "view",
        "description": "Search and view patient records",
    },
    {
        "resource": "patients",
        "action": "edit",
        "description": "Update patient demographics",
    },
    {
        "resource": "patients",
        "action": "delete",
        "description": "Delete or restore patient records",
    },
    # Patient Insurance
    {
        "resource": "patient_insurance",
        "action": "create",
        "description": "Add insurance policy to patient",
    },
    {
        "resource": "patient_insurance",
        "action": "view",
        "description": "View patient insurance policies",
    },
    {
        "resource": "patient_insurance",
        "action": "edit",
        "description": "Edit insurance policy details",
    },
    # Doctors
    {"resource": "doctors", "action": "create", "description": "Create doctors"},
    {"resource": "doctors", "action": "view", "description": "Search and view doctors"},
    {"resource": "doctors", "action": "edit", "description": "Update doctor records"},
    {
        "resource": "doctors",
        "action": "delete",
        "description": "Delete or restore doctor records",
    },
    # Orders
    {"resource": "orders", "action": "create", "description": "Create a new order"},
    {
        "resource": "orders",
        "action": "view",
        "description": "View order details and status",
    },
    {
        "resource": "orders",
        "action": "edit",
        "description": "Edit order before specimen collection",
    },
    {"resource": "orders", "action": "cancel", "description": "Cancel an order"},
    # Order Items
    {
        "resource": "order_items",
        "action": "create",
        "description": "Add tests to an order",
    },
    {
        "resource": "order_items",
        "action": "view",
        "description": "View order item details",
    },
    {
        "resource": "order_items",
        "action": "edit",
        "description": "Adjust price override or sort order",
    },
    {
        "resource": "order_items",
        "action": "delete",
        "description": "Remove a test before processing",
    },
    # Specimens
    {"resource": "specimens", "action": "view", "description": "View specimen details"},
    {
        "resource": "specimens",
        "action": "collect",
        "description": "Record specimen collection",
    },
    {
        "resource": "specimens",
        "action": "reject",
        "description": "Mark specimen as rejected",
    },
    # Results
    {"resource": "results", "action": "enter", "description": "Enter result values"},
    {
        "resource": "results",
        "action": "edit",
        "description": "Correct a result before verification",
    },
    {
        "resource": "results",
        "action": "verify",
        "description": "Verify results as pathologist",
    },
    {
        "resource": "results",
        "action": "view",
        "description": "View result values and flags",
    },
    # Critical Notifications
    {
        "resource": "critical_notifications",
        "action": "view",
        "description": "View critical notifications",
    },
    {
        "resource": "critical_notifications",
        "action": "acknowledge",
        "description": "Acknowledge a critical notification",
    },
    # Reports
    {"resource": "reports", "action": "release", "description": "Release a report"},
    {
        "resource": "reports",
        "action": "void",
        "description": "Void a superseded report version",
    },
    {"resource": "reports", "action": "view", "description": "View released reports"},
    {
        "resource": "reports",
        "action": "manage_templates",
        "description": "Manage report components and category renderers",
    },
    # Invoices
    {"resource": "invoices", "action": "create", "description": "Create an invoice"},
    {"resource": "invoices", "action": "view", "description": "View invoice details"},
    {
        "resource": "invoices",
        "action": "edit",
        "description": "Adjust discount or amounts",
    },
    {
        "resource": "invoices",
        "action": "void",
        "description": "Void and reissue an invoice",
    },
    # Payments
    {"resource": "payments", "action": "view", "description": "View payment records"},
    {"resource": "payments", "action": "collect", "description": "Record a payment"},
    {"resource": "payments", "action": "refund", "description": "Issue a refund"},
    {
        "resource": "finance",
        "action": "manage",
        "description": "Manage financial configuration",
    },
    # Commissions
    {
        "resource": "commissions",
        "action": "view",
        "description": "View commission entries",
    },
    {
        "resource": "commissions",
        "action": "adjust",
        "description": "Create manual commission adjustments",
    },
    {
        "resource": "commissions",
        "action": "pay",
        "description": "Record a commission payout",
    },
    {
        "resource": "commissions",
        "action": "manage_config",
        "description": "Manage doctor commission rates",
    },
    # Catalog & Rules
    {
        "resource": "catalog",
        "action": "manage",
        "description": "Full CRUD on catalog items and panels",
    },
    {
        "resource": "rules",
        "action": "manage",
        "description": "Full CRUD on validation, consistency, reflex rules",
    },
    # Users & Roles
    {
        "resource": "users",
        "action": "manage",
        "description": "Create, edit, deactivate users",
    },
    {
        "resource": "roles",
        "action": "manage",
        "description": "Create roles and assign permissions",
    },
    # Reference data
    {
        "resource": "reference_data",
        "action": "manage",
        "description": "Full CRUD on reference/lookup data",
    },
    # Audit
    {
        "resource": "audit",
        "action": "view",
        "description": "Read-only access to audit logs",
    },
    {
        "resource": "audit",
        "action": "export",
        "description": "Export filtered audit logs",
    },
    {
        "resource": "lab_settings",
        "action": "manage",
        "description": "Manage laboratory identity and document details",
    },
    # Items (existing app resource)
    {"resource": "items", "action": "create", "description": "Create items"},
    {"resource": "items", "action": "view", "description": "View items"},
    {"resource": "items", "action": "edit", "description": "Update items"},
    {"resource": "items", "action": "delete", "description": "Delete items"},
]

# ---------------------------------------------------------------------------
# Roles (from schema.sql lines 819-829)
# ---------------------------------------------------------------------------

SEED_ROLES: list[dict] = [
    {"name": "super_admin", "description": "Full system access", "is_default": False},
    {
        "name": "lab_manager",
        "description": "Operations, catalog, staff management",
        "is_default": False,
    },
    {
        "name": "receptionist",
        "description": "Patient registration, orders, payments",
        "is_default": True,
    },
    {"name": "phlebotomist", "description": "Specimen collection", "is_default": False},
    {
        "name": "supervisor",
        "description": "Oversight and critical notification acknowledgement",
        "is_default": False,
    },
    {"name": "technician", "description": "Result entry", "is_default": False},
    {
        "name": "pathologist",
        "description": "Result verification and report release",
        "is_default": False,
    },
    {
        "name": "finance",
        "description": "Invoices, payments, commissions",
        "is_default": False,
    },
    {
        "name": "doctor",
        "description": "View own patients results and reports",
        "is_default": False,
    },
    {
        "name": "patient",
        "description": "View own reports via portal",
        "is_default": False,
    },
]

# ---------------------------------------------------------------------------
# Role → Permission mappings
# Derived from role descriptions. Format: role_name → list of (resource, action)
# ---------------------------------------------------------------------------

ROLE_PERMISSION_MAP: dict[str, list[tuple[str, str]]] = {
    "super_admin": [],  # special marker — gets ALL permissions at seed time
    "lab_manager": [
        ("catalog", "manage"),
        ("rules", "manage"),
        ("users", "manage"),
        ("roles", "manage"),
        ("orders", "create"),
        ("orders", "view"),
        ("orders", "edit"),
        ("orders", "cancel"),
        ("order_items", "create"),
        ("order_items", "view"),
        ("order_items", "edit"),
        ("order_items", "delete"),
        ("results", "view"),
        ("reports", "view"),
        ("reports", "manage_templates"),
        ("specimens", "view"),
        ("patients", "create"),
        ("patients", "view"),
        ("patients", "edit"),
        ("patients", "delete"),
        ("patient_insurance", "create"),
        ("patient_insurance", "view"),
        ("patient_insurance", "edit"),
        ("doctors", "create"),
        ("doctors", "view"),
        ("doctors", "edit"),
        ("doctors", "delete"),
        ("invoices", "view"),
        ("payments", "view"),
        ("commissions", "view"),
        ("commissions", "adjust"),
        ("commissions", "manage_config"),
        ("reference_data", "manage"),
        ("audit", "view"),
        ("audit", "export"),
        ("lab_settings", "manage"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "receptionist": [
        ("patients", "create"),
        ("patients", "view"),
        ("patients", "edit"),
        ("patient_insurance", "create"),
        ("patient_insurance", "view"),
        ("patient_insurance", "edit"),
        ("doctors", "create"),
        ("doctors", "view"),
        ("doctors", "edit"),
        ("orders", "create"),
        ("orders", "view"),
        ("orders", "edit"),
        ("order_items", "create"),
        ("order_items", "view"),
        ("order_items", "edit"),
        ("invoices", "create"),
        ("invoices", "view"),
        ("payments", "view"),
        ("payments", "collect"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "phlebotomist": [
        ("specimens", "view"),
        ("specimens", "collect"),
        ("specimens", "reject"),
        ("orders", "view"),
        ("patients", "view"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "supervisor": [
        ("critical_notifications", "view"),
        ("critical_notifications", "acknowledge"),
        ("results", "view"),
        ("reports", "view"),
        ("orders", "view"),
        ("specimens", "view"),
        ("patients", "view"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "technician": [
        ("results", "enter"),
        ("results", "edit"),
        ("results", "view"),
        ("orders", "view"),
        ("patients", "view"),
        ("specimens", "view"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "pathologist": [
        ("results", "enter"),
        ("results", "edit"),
        ("results", "verify"),
        ("results", "view"),
        ("reports", "release"),
        ("reports", "view"),
        ("orders", "view"),
        ("patients", "view"),
        ("specimens", "view"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "finance": [
        ("invoices", "create"),
        ("invoices", "view"),
        ("invoices", "edit"),
        ("invoices", "void"),
        ("payments", "view"),
        ("payments", "collect"),
        ("payments", "refund"),
        ("finance", "manage"),
        ("commissions", "view"),
        ("commissions", "adjust"),
        ("commissions", "pay"),
        ("commissions", "manage_config"),
        ("orders", "view"),
        ("patients", "view"),
        ("doctors", "view"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "doctor": [
        ("patients", "view"),
        ("orders", "view"),
        ("results", "view"),
        ("reports", "view"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
    "patient": [
        ("reports", "view"),
        ("items", "create"),
        ("items", "view"),
        ("items", "edit"),
        ("items", "delete"),
    ],
}


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------


def seed_permissions(session: Session) -> dict[tuple[str, str], Permission]:
    """Upsert all seed permissions. Returns a lookup map keyed by (resource, action)."""
    perm_map: dict[tuple[str, str], Permission] = {}

    for p_data in SEED_PERMISSIONS:
        key = (p_data["resource"], p_data["action"])
        existing = session.exec(
            select(Permission).where(
                Permission.resource == p_data["resource"],
                Permission.action == p_data["action"],
            )
        ).first()
        if existing:
            perm_map[key] = existing
        else:
            perm = Permission(**p_data)
            session.add(perm)
            session.flush()
            perm_map[key] = perm

    return perm_map


def seed_roles(session: Session) -> dict[str, Role]:
    """Upsert all seed roles. Returns a lookup map keyed by role name."""
    role_map: dict[str, Role] = {}

    for r_data in SEED_ROLES:
        existing = session.exec(select(Role).where(Role.name == r_data["name"])).first()
        if existing:
            # Restore soft-deleted seed roles and update attributes
            if existing.is_deleted:
                existing.is_deleted = False
            if existing.description != r_data.get("description"):
                existing.description = r_data.get("description")
            session.add(existing)
            session.flush()
            role_map[r_data["name"]] = existing
        else:
            role = Role(**r_data)
            session.add(role)
            session.flush()
            role_map[r_data["name"]] = role

    return role_map


def seed_role_permissions(
    session: Session,
    perm_map: dict[tuple[str, str], Permission],
    role_map: dict[str, Role],
) -> None:
    """Create RolePermission rows that don't already exist."""
    for role_name, perm_keys in ROLE_PERMISSION_MAP.items():
        role = role_map.get(role_name)
        if role is None:
            continue

        # super_admin gets ALL permissions
        keys_to_assign: list[tuple[str, str]]
        if role_name == "super_admin":
            keys_to_assign = list(perm_map.keys())
        else:
            keys_to_assign = perm_keys

        for key in keys_to_assign:
            perm = perm_map.get(key)
            if perm is None:
                continue

            existing = session.exec(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id,
                )
            ).first()
            if not existing:
                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                session.add(rp)
                session.flush()


def seed_rbac(session: Session) -> tuple[dict, dict[str, Role]]:
    """
    Run all RBAC seed steps: permissions, roles, role-permission assignments.
    Call this from init_db() after creating the first superuser.
    Returns (perm_map, role_map) so the caller can assign roles to users.
    """
    perm_map = seed_permissions(session)
    role_map = seed_roles(session)
    seed_role_permissions(session, perm_map, role_map)
    return perm_map, role_map
