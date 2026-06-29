#!/usr/bin/env python3
"""
Clear all LIS business data while preserving users and the RBAC system.

Preserved tables:
  - user              (user accounts)
  - permissions       (RBAC permission definitions)
  - roles             (RBAC role definitions)
  - role_permissions  (role-to-permission assignments)
  - user_roles        (user-to-role assignments)
  - alembic_version   (migration tracking)

All other tables are deleted in FK-safe dependency order.
"""

# ruff: noqa: I001, T201

import sys

from sqlalchemy import text
from sqlmodel import SQLModel, Session

from app.core.db import engine
from app.models import *  # noqa: F403

# Deletion order: deepest leaf tables first, working up to root reference tables.
# Each phase only touches tables whose dependents have already been cleared.
TABLES_BY_PHASE: list[list[str]] = [
    # Phase 1 — deepest leaf tables (nothing depends on these)
    # Intra-phase FK order matters:
    #   order_catalog_item_analytes → catalog_item_analytes (child before parent)
    #   doctor_commission_payment_entries → doctor_commission_adjustments (child before parent)
    [
        "daily_sequences",
        "audit_logs",
        "reagent_stock_movements",
        "catalog_specimen_requirements",
        "catalog_panel_items",
        "consistency_rule_analytes",
        "order_item_specimens",
        "order_catalog_item_analytes",
        "catalog_item_analytes",
        "analyte_result_comments",
        "critical_notifications",
        "customer_credits",
        "doctor_commission_payment_entries",
        "doctor_commission_adjustments",
        "payment_refunds",
        "invoice_balance_transfers",
        "invoice_lines",
        "item",
    ],
    # Phase 2 — tables referenced only by Phase-1 tables
    [
        "doctor_commission_configs",
        "insurance_pricing",
        "notifications",
        "finance_settings",
        "lab_settings",
        "reagent_lots",
        "reagent_settings",
        "payment_transactions",
        "analyte_results",
        "reports",
        "report_settings",
        "report_component_versions",
        "report_renderer_versions",
    ],
    # Phase 3 — order sub-entities, invoices, commissions, rules
    [
        "order_items",
        "order_specimens",
        "order_revisions",
        "invoices",
        "doctor_commission_entries",
        "doctor_commission_payments",
        "validation_rules",
        "consistency_rules",
        "reflex_rules",
        "report_templates",
        "report_components",
        "report_renderers",
    ],
    # Phase 4 — orders (root of the clinical workflow)
    [
        "orders",
    ],
    # Phase 5 — reference / lookup tables
    # Child tables (FK → another Phase-5 table) must come before their parent.
    #   patient_insurance → patients, insurance_providers
    #   catalog           → categories
    #   analytes          → units
    #   doctors           → titles
    [
        "patient_insurance",
        "catalog",
        "analytes",
        "doctors",
        "patients",
        "categories",
        "units",
        "titles",
        "specimen_types",
        "patient_contexts",
        "payment_methods",
        "rejection_reasons",
        "insurance_providers",
        "instruments",
        "reagents",
    ],
]

PRESERVED_TABLES: set[str] = {
    "user",
    "permissions",
    "roles",
    "role_permissions",
    "user_roles",
    "alembic_version",
}


def validate_table_coverage() -> None:
    listed_tables = {table for phase in TABLES_BY_PHASE for table in phase}
    known_tables = set(SQLModel.metadata.tables)
    missing = known_tables - listed_tables - PRESERVED_TABLES
    if missing:
        print("ERROR: clear_data.py does not handle these tables:")
        for table in sorted(missing):
            print(f"  - {table}")
        print("Add them to TABLES_BY_PHASE or PRESERVED_TABLES before running.")
        sys.exit(1)


def main() -> None:
    validate_table_coverage()

    print("=" * 60)
    print("  Keneya Lab — Data Cleanup Script")
    print("=" * 60)
    print()
    print("The following tables will be PRESERVED:")
    for t in sorted(PRESERVED_TABLES):
        print(f"  ✓ {t}")
    print()
    print("The following tables will be CLEARED (all rows deleted):")
    for phase_num, phase in enumerate(TABLES_BY_PHASE, start=1):
        for t in phase:
            print(f"  ✗ {t}  (phase {phase_num})")
    print()

    # Safety prompt
    confirm = input("Type 'yes' to proceed with deletion: ").strip()
    if confirm.lower() != "yes":
        print("Aborted.")
        sys.exit(0)

    total_deleted = 0

    with Session(engine) as session:
        for phase_num, phase in enumerate(TABLES_BY_PHASE, start=1):
            for table in phase:
                result = session.execute(
                    text(f"DELETE FROM {table}"),
                )
                count = result.rowcount
                total_deleted += count
                print(f"  [{phase_num}] {table}: {count} row(s) deleted")

        session.commit()

    print()
    print(f"Done. {total_deleted} row(s) deleted across all phases.")
    print("Users and RBAC data have been preserved.")


if __name__ == "__main__":
    main()
