#!/usr/bin/env python3
"""
Clear catalog setup data and dependent workflow rows.

Preserved data includes users, RBAC, patients, doctors, insurance providers,
payment methods, patient contexts, report templates/components, instruments,
and other non-catalog reference data.

Deleted data includes catalog definitions, analytes, catalog categories, units,
specimen types, validation/consistency/reflex rules, insurance catalog pricing,
and order/result/invoice rows that depend on catalog or specimen definitions.
"""

# ruff: noqa: I001, T201

import sys

from sqlalchemy import text
from sqlmodel import SQLModel, Session

from app.core.db import engine
from app.models import *  # noqa: F403

# Deletion order: dependent workflow/finance rows first, then catalog setup.
# Each phase only touches tables whose dependents have already been cleared.
TABLES_BY_PHASE: list[list[str]] = [
    # Phase 1 — deepest leaf tables.
    [
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
    ],
    # Phase 2 — tables referenced only by Phase-1 tables or order roots.
    [
        "insurance_pricing",
        "notifications",
        "payment_transactions",
        "analyte_results",
        "reports",
    ],
    # Phase 3 — order sub-entities, invoices, commissions, and catalog rules.
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
    ],
    # Phase 4 — orders depend on patients/doctors, which are preserved.
    [
        "orders",
    ],
    # Phase 5 — catalog setup and lookup roots.
    [
        "catalog",
        "analytes",
        "categories",
        "units",
        "specimen_types",
    ],
]


def validate_tables_exist() -> None:
    listed_tables = {table for phase in TABLES_BY_PHASE for table in phase}
    known_tables = set(SQLModel.metadata.tables)
    missing = listed_tables - known_tables
    if missing:
        print("ERROR: clear_catalog_data.py references unknown tables:")
        for table in sorted(missing):
            print(f"  - {table}")
        print("Update TABLES_BY_PHASE before running.")
        sys.exit(1)


def main() -> None:
    validate_tables_exist()

    print("=" * 60)
    print("  Keneya Lab — Catalog Data Cleanup Script")
    print("=" * 60)
    print()
    print("The following data will be PRESERVED:")
    print("  ✓ users and RBAC")
    print("  ✓ patients, doctors, insurers, payment methods, patient contexts")
    print("  ✓ report templates/components/renderers and instruments")
    print()
    print("The following tables will be CLEARED (all rows deleted):")
    for phase_num, phase in enumerate(TABLES_BY_PHASE, start=1):
        for table in phase:
            print(f"  ✗ {table}  (phase {phase_num})")
    print()

    confirm = input("Type 'yes' to proceed with deletion: ").strip()
    if confirm.lower() != "yes":
        print("Aborted.")
        sys.exit(0)

    total_deleted = 0

    with Session(engine) as session:
        for phase_num, phase in enumerate(TABLES_BY_PHASE, start=1):
            for table in phase:
                result = session.execute(text(f"DELETE FROM {table}"))
                count = result.rowcount
                total_deleted += count
                print(f"  [{phase_num}] {table}: {count} row(s) deleted")

        session.commit()

    print()
    print(f"Done. {total_deleted} row(s) deleted across all phases.")
    print("Catalog setup and dependent workflow rows have been cleared.")


if __name__ == "__main__":
    main()
