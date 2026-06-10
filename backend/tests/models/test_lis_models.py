import uuid
from datetime import date

from app.models import (
    AuditLog,
    Catalog,
    CatalogFilters,
    Order,
    Patient,
    PatientFilters,
    SortOrder,
    SQLModel,
    TriggerOperator,
)


def test_lis_tables_are_registered() -> None:
    expected_tables = {
        "titles",
        "units",
        "patient_contexts",
        "payment_methods",
        "rejection_reasons",
        "insurance_providers",
        "patients",
        "patient_insurance",
        "doctors",
        "specimen_types",
        "categories",
        "catalog",
        "catalog_specimen_requirements",
        "catalog_panel_items",
        "analytes",
        "catalog_item_analytes",
        "validation_rules",
        "consistency_rules",
        "consistency_rule_analytes",
        "reflex_rules",
        "instruments",
        "orders",
        "order_specimens",
        "order_items",
        "order_catalog_item_analytes",
        "analyte_results",
        "analyte_result_comments",
        "critical_notifications",
        "report_templates",
        "reports",
        "notifications",
        "insurance_pricing",
        "invoices",
        "doctor_commission_configs",
        "doctor_commission_entries",
        "doctor_commission_payments",
        "doctor_commission_payment_entries",
        "audit_logs",
    }

    assert expected_tables.issubset(SQLModel.metadata.tables)


def test_lis_models_keep_existing_user_table_references() -> None:
    orders = SQLModel.metadata.tables[Order.__tablename__]
    audit_logs = SQLModel.metadata.tables[AuditLog.__tablename__]

    order_fk_targets = {fk.target_fullname for fk in orders.c.created_by.foreign_keys}
    audit_fk_targets = {fk.target_fullname for fk in audit_logs.c.performed_by_id.foreign_keys}

    assert order_fk_targets == {"user.id"}
    assert audit_fk_targets == {"user.id"}


def test_key_schema_constraints_are_declared() -> None:
    patients = SQLModel.metadata.tables[Patient.__tablename__]
    catalog = SQLModel.metadata.tables[Catalog.__tablename__]
    catalog_specimen_requirements = SQLModel.metadata.tables[
        "catalog_specimen_requirements"
    ]

    assert "uq_patients_identifier" in {constraint.name for constraint in patients.constraints}
    assert "uq_catalog_code" in {constraint.name for constraint in catalog.constraints}
    assert {column.name for column in catalog_specimen_requirements.primary_key} == {
        "catalog_id",
        "specimen_type_id",
    }


def test_lis_schema_enum_values_match_database_contract() -> None:
    assert TriggerOperator.in_.value == "in"


def test_lis_filter_schemas_are_exported_with_expected_defaults() -> None:
    patient_filters = PatientFilters(search="awa")
    catalog_filters = CatalogFilters(sort_by="name", sort_order=SortOrder.desc)

    assert patient_filters.search == "awa"
    assert patient_filters.skip == 0
    assert patient_filters.limit == 100
    assert patient_filters.include_deleted is False
    assert catalog_filters.sort_by == "name"
    assert catalog_filters.sort_order == SortOrder.desc


def test_public_models_accept_uuid_identifiers() -> None:
    patient = Patient(
        id=uuid.uuid4(),
        identifier="P-0001",
        first_name="Awa",
        last_name="Traore",
        date_of_birth=date(1990, 1, 1),
        gender="female",
    )

    assert patient.identifier == "P-0001"
