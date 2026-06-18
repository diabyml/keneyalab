# ruff: noqa

"""LIS domain models and API schemas.

These models intentionally provide the database and Pydantic foundation only.
Workflow behavior belongs in services added by later feature slices.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, cast

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import AnyHttpUrl, EmailStr, TypeAdapter, field_validator
from sqlmodel import Field, SQLModel

from .common import get_datetime_utc

TIMESTAMPTZ = cast(type[Any], DateTime(timezone=True))


def uuid_pk() -> uuid.UUID:
    return uuid.uuid4()


def utc_timestamp_field() -> datetime:
    return get_datetime_utc()


def pg_enum(enum_class: type[Enum], name: str) -> SAEnum:
    return SAEnum(
        enum_class,
        name=name,
        values_callable=lambda values: [item.value for item in values],
    )


class GenderType(str, Enum):
    male = "male"
    female = "female"


class AnalyteDataType(str, Enum):
    numeric = "numeric"
    text = "text"
    options = "options"
    image = "image"


class CatalogType(str, Enum):
    item = "item"
    panel = "panel"


class TargetGenderType(str, Enum):
    male = "male"
    female = "female"
    all = "all"


class TriggerOperator(str, Enum):
    gt = "gt"
    lt = "lt"
    eq = "eq"
    gte = "gte"
    lte = "lte"
    in_ = "in"


class RuleSeverity(str, Enum):
    warning = "warning"
    error = "error"


class FormulaResultType(str, Enum):
    number = "number"
    boolean = "boolean"


class OrderStatus(str, Enum):
    registered = "registered"
    collected = "collected"
    in_progress = "in_progress"
    partial_results = "partial_results"
    completed = "completed"
    cancelled = "cancelled"


class SpecimenStatus(str, Enum):
    pending = "pending"
    collected = "collected"
    rejected = "rejected"
    processed = "processed"


class ResultStatus(str, Enum):
    pending = "pending"
    resulted = "resulted"
    verified = "verified"
    rejected = "rejected"


class PayoutStatus(str, Enum):
    pending = "pending"
    paid = "paid"


class DiscountAllocationPolicy(str, Enum):
    proportional = "proportional"
    non_insured_first = "non_insured_first"
    insured_first = "insured_first"


class PaymentStatus(str, Enum):
    unpaid = "unpaid"
    paid = "paid"
    partial = "partial"
    refunded = "refunded"


class PaymentTransactionStatus(str, Enum):
    completed = "completed"
    refunded = "refunded"


class ReportChannel(str, Enum):
    print = "print"
    email = "email"
    whatsapp = "whatsapp"
    portal = "portal"


class DeliveryStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class NotificationType(str, Enum):
    result_ready = "result_ready"
    order_update = "order_update"
    report_released = "report_released"
    general = "general"


class NotificationChannel(str, Enum):
    sms = "sms"
    email = "email"
    whatsapp = "whatsapp"
    in_app = "in_app"


class NotificationStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class CriticalMethod(str, Enum):
    call = "call"
    sms = "sms"
    in_app = "in_app"
    email = "email"


class AuditAction(str, Enum):
    insert = "insert"
    update = "update"
    delete = "delete"
    login_success = "login_success"
    login_failed = "login_failed"
    password_recovery = "password_recovery"
    password_reset = "password_reset"


class AuditCategory(str, Enum):
    clinical = "clinical"
    workflow = "workflow"
    finance = "finance"
    configuration = "configuration"
    security = "security"
    system = "system"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class DailySequence(SQLModel, table=True):
    __tablename__ = "daily_sequences"
    __table_args__ = (
        UniqueConstraint("sequence_date", "sequence_type", name="uq_daily_sequence"),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    sequence_date: date
    sequence_type: str = Field(max_length=30)
    current_value: int = Field(default=0)


# ---------------------------------------------------------------------------
# Reusable schemas
# ---------------------------------------------------------------------------


class SoftDeletePublic(SQLModel):
    id: uuid.UUID
    is_deleted: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TimestampPublic(SQLModel):
    id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NameLookupBase(SQLModel):
    name: str = Field(max_length=100)


class NameLookupUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)


class NameLookupPublic(NameLookupBase, SoftDeletePublic):
    pass


# ---------------------------------------------------------------------------
# Filter schemas
# ---------------------------------------------------------------------------


class PaginationFilter(SQLModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=500)


class SearchFilter(SQLModel):
    search: str | None = Field(default=None, max_length=255)


class SortFilter(SQLModel):
    sort_by: str | None = Field(default=None, max_length=100)
    sort_order: SortOrder = Field(default=SortOrder.asc)


class SoftDeleteFilter(SQLModel):
    include_deleted: bool = Field(default=False)


class CreatedAtFilter(SQLModel):
    created_from: datetime | None = None
    created_to: datetime | None = None


class LookupFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    pass


class TitleFilters(LookupFilters):
    pass


class UnitFilters(LookupFilters):
    pass


class PatientContextFilters(LookupFilters):
    pass


class PaymentMethodFilters(LookupFilters):
    pass


class RejectionReasonFilters(LookupFilters):
    pass


class SpecimenTypeFilters(LookupFilters):
    color: str | None = Field(default=None, max_length=50)


class CategoryFilters(LookupFilters):
    pass


class InsuranceProviderFilters(LookupFilters):
    pass


class PatientFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    gender: GenderType | None = None
    date_of_birth_from: date | None = None
    date_of_birth_to: date | None = None
    has_insurance: bool | None = None
    insurance_provider_id: uuid.UUID | None = None


class PatientInsuranceFilters(
    SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    patient_id: uuid.UUID | None = None
    insurance_provider_id: uuid.UUID | None = None
    is_primary: bool | None = None


class DoctorFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    title_id: uuid.UUID | None = None


class CatalogFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    type: CatalogType | None = None
    category_id: uuid.UUID | None = None
    is_orderable: bool | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None


class CatalogSpecimenRequirementFilters(SortFilter, PaginationFilter):
    catalog_id: uuid.UUID | None = None
    specimen_type_id: uuid.UUID | None = None


class CatalogPanelItemFilters(SortFilter, PaginationFilter):
    panel_id: uuid.UUID | None = None
    test_id: uuid.UUID | None = None


class AnalyteFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    unit_id: uuid.UUID | None = None
    data_type: AnalyteDataType | None = None
    is_calculated: bool | None = None


class CatalogItemAnalyteFilters(SortFilter, PaginationFilter):
    catalog_item_id: uuid.UUID | None = None
    analyte_id: uuid.UUID | None = None


class ValidationRuleFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    analyte_id: uuid.UUID | None = None
    data_type: AnalyteDataType | None = None
    is_active: bool | None = None
    target_gender: TargetGenderType | None = None
    required_context_id: uuid.UUID | None = None
    age_years: int | None = Field(default=None, ge=0)


class ConsistencyRuleFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    severity: RuleSeverity | None = None
    analyte_id: uuid.UUID | None = None


class ConsistencyRuleAnalyteFilters(SortFilter, PaginationFilter):
    rule_id: uuid.UUID | None = None
    analyte_id: uuid.UUID | None = None


class ReflexRuleFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    trigger_analyte_id: uuid.UUID | None = None
    trigger_operator: TriggerOperator | None = None
    action_catalog_id: uuid.UUID | None = None


class InstrumentFilters(SearchFilter, CreatedAtFilter, SortFilter, PaginationFilter):
    is_active: bool | None = None


class OrderFilters(SearchFilter, CreatedAtFilter, SortFilter, PaginationFilter):
    patient_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    patient_insurance_id: uuid.UUID | None = None
    patient_context_id: uuid.UUID | None = None
    status: OrderStatus | None = None
    created_by: uuid.UUID | None = None


class OrderSpecimenFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    order_id: uuid.UUID | None = None
    specimen_type_id: uuid.UUID | None = None
    collected_by: uuid.UUID | None = None
    status: SpecimenStatus | None = None
    rejection_reason_id: uuid.UUID | None = None
    collection_from: datetime | None = None
    collection_to: datetime | None = None


class OrderItemFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    order_id: uuid.UUID | None = None
    catalog_id: uuid.UUID | None = None
    order_specimen_id: uuid.UUID | None = None
    is_covered_by_insurance: bool | None = None
    is_reflex_added: bool | None = None


class OrderCatalogItemAnalyteFilters(SortFilter, PaginationFilter):
    order_item_id: uuid.UUID | None = None
    catalog_item_analyte_id: uuid.UUID | None = None


class AnalyteResultFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    order_item_id: uuid.UUID | None = None
    analyte_id: uuid.UUID | None = None
    specimen_id: uuid.UUID | None = None
    instrument_id: uuid.UUID | None = None
    validation_rule_id: uuid.UUID | None = None
    status: ResultStatus | None = None
    resulted_by_id: uuid.UUID | None = None
    verified_by_id: uuid.UUID | None = None
    is_abnormal: bool | None = None
    is_critical: bool | None = None
    delta_flag: bool | None = None
    is_rejected: bool | None = None
    resulted_from: datetime | None = None
    resulted_to: datetime | None = None
    verified_from: datetime | None = None
    verified_to: datetime | None = None


class AnalyteResultCommentFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    analyte_result_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None


class CriticalNotificationFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    analyte_result_id: uuid.UUID | None = None
    notified_by_id: uuid.UUID | None = None
    notified_to_id: uuid.UUID | None = None
    method: CriticalMethod | None = None
    acknowledged: bool | None = None
    notified_from: datetime | None = None
    notified_to: datetime | None = None


class ReportTemplateFilters(
    SearchFilter, SoftDeleteFilter, CreatedAtFilter, SortFilter, PaginationFilter
):
    is_default: bool | None = None


class ReportFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    order_id: uuid.UUID | None = None
    report_template_id: uuid.UUID | None = None
    released_by_id: uuid.UUID | None = None
    channel: ReportChannel | None = None
    delivery_status: DeliveryStatus | None = None
    is_voided: bool | None = None
    released_from: datetime | None = None
    released_to: datetime | None = None


class NotificationFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    order_id: uuid.UUID | None = None
    patient_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    type: NotificationType | None = None
    channel: NotificationChannel | None = None
    status: NotificationStatus | None = None
    sent_from: datetime | None = None
    sent_to: datetime | None = None


class InsurancePricingFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    insurance_provider_id: uuid.UUID | None = None
    catalog_id: uuid.UUID | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None


class InvoiceFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    order_id: uuid.UUID | None = None
    payment_status: PaymentStatus | None = None
    payment_method_id: uuid.UUID | None = None
    created_by_id: uuid.UUID | None = None
    is_voided: bool | None = None
    min_total_amount: Decimal | None = None
    max_total_amount: Decimal | None = None
    min_net_amount: Decimal | None = None
    max_net_amount: Decimal | None = None


class DoctorCommissionConfigFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    doctor_id: uuid.UUID | None = None
    effective_on: date | None = None
    effective_from: date | None = None
    effective_until: date | None = None


class DoctorCommissionEntryFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    order_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    payout_status: PayoutStatus | None = None
    paid_from: datetime | None = None
    paid_to: datetime | None = None


class DoctorCommissionPaymentFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    doctor_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    min_total_commission_amount: Decimal | None = None
    max_total_commission_amount: Decimal | None = None


class DoctorCommissionPaymentEntryFilters(SortFilter, PaginationFilter):
    commission_payment_id: uuid.UUID | None = None
    commission_entry_id: uuid.UUID | None = None


class AuditLogFilters(CreatedAtFilter, SortFilter, PaginationFilter):
    table_name: str | None = Field(default=None, max_length=100)
    record_id: uuid.UUID | None = None
    action: AuditAction | None = None
    category: AuditCategory | None = None
    performed_by_id: uuid.UUID | None = None
    performed_from: datetime | None = None
    performed_to: datetime | None = None


# ---------------------------------------------------------------------------
# Lookup / reference tables
# ---------------------------------------------------------------------------


class TitleBase(NameLookupBase):
    pass


class TitleCreate(TitleBase):
    pass


class TitleUpdate(NameLookupUpdate):
    pass


class Title(TitleBase, table=True):
    __tablename__ = "titles"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class TitlePublic(TitleBase, SoftDeletePublic):
    pass


class TitlesPublic(SQLModel):
    data: list[TitlePublic]
    count: int


class UnitBase(NameLookupBase):
    pass


class UnitCreate(UnitBase):
    pass


class UnitUpdate(NameLookupUpdate):
    pass


class Unit(UnitBase, table=True):
    __tablename__ = "units"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class UnitPublic(UnitBase, SoftDeletePublic):
    pass


class UnitsPublic(SQLModel):
    data: list[UnitPublic]
    count: int


class PatientContextBase(NameLookupBase):
    pass


class PatientContextCreate(PatientContextBase):
    pass


class PatientContextUpdate(NameLookupUpdate):
    pass


class PatientContext(PatientContextBase, table=True):
    __tablename__ = "patient_contexts"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class PatientContextPublic(PatientContextBase, SoftDeletePublic):
    pass


class PatientContextsPublic(SQLModel):
    data: list[PatientContextPublic]
    count: int


class PaymentMethodBase(NameLookupBase):
    pass


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(NameLookupUpdate):
    pass


class PaymentMethod(PaymentMethodBase, table=True):
    __tablename__ = "payment_methods"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class PaymentMethodPublic(PaymentMethodBase, SoftDeletePublic):
    pass


class PaymentMethodsPublic(SQLModel):
    data: list[PaymentMethodPublic]
    count: int


class RejectionReasonBase(SQLModel):
    name: str = Field(max_length=255)


class RejectionReasonCreate(RejectionReasonBase):
    pass


class RejectionReasonUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)


class RejectionReason(RejectionReasonBase, table=True):
    __tablename__ = "rejection_reasons"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class RejectionReasonPublic(RejectionReasonBase, SoftDeletePublic):
    pass


class RejectionReasonsPublic(SQLModel):
    data: list[RejectionReasonPublic]
    count: int


class SpecimenTypeBase(SQLModel):
    name: str = Field(max_length=100)
    description: str | None = None
    color: str | None = Field(default=None, max_length=50)


class SpecimenTypeCreate(SpecimenTypeBase):
    pass


class SpecimenTypeUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    color: str | None = Field(default=None, max_length=50)


class SpecimenType(SpecimenTypeBase, table=True):
    __tablename__ = "specimen_types"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class SpecimenTypePublic(SpecimenTypeBase, SoftDeletePublic):
    pass


class SpecimenTypesPublic(SQLModel):
    data: list[SpecimenTypePublic]
    count: int


class CategoryBase(SQLModel):
    name: str = Field(max_length=100)
    sort_order: int = Field(default=1)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    sort_order: int | None = None


class Category(CategoryBase, table=True):
    __tablename__ = "categories"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class CategoryPublic(CategoryBase, SoftDeletePublic):
    pass


class CategoriesPublic(SQLModel):
    data: list[CategoryPublic]
    count: int


class CategoryReorderItem(SQLModel):
    id: uuid.UUID
    sort_order: int


class CategoryReorderRequest(SQLModel):
    items: list[CategoryReorderItem] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Clinical setup
# ---------------------------------------------------------------------------


class InsuranceProviderBase(SQLModel):
    name: str = Field(max_length=255)


class InsuranceProviderCreate(InsuranceProviderBase):
    pass


class InsuranceProviderUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)


class InsuranceProvider(InsuranceProviderBase, table=True):
    __tablename__ = "insurance_providers"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class InsuranceProviderPublic(InsuranceProviderBase, SoftDeletePublic):
    pass


class InsuranceProvidersPublic(SQLModel):
    data: list[InsuranceProviderPublic]
    count: int


class PatientBase(SQLModel):
    identifier: str = Field(max_length=100)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: date
    gender: GenderType = Field(
        sa_column=Column(pg_enum(GenderType, "gender_type"), nullable=False)
    )
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, sa_column=Column(Text))


class PatientCreate(PatientBase):
    pass


class PatientUpdate(SQLModel):
    identifier: str | None = Field(default=None, max_length=100)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    gender: GenderType | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None


class Patient(PatientBase, table=True):
    __tablename__ = "patients"
    __table_args__ = (UniqueConstraint("identifier", name="uq_patients_identifier"),)

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class PatientPublic(PatientBase, SoftDeletePublic):
    pass


class PatientsPublic(SQLModel):
    data: list[PatientPublic]
    count: int


class PatientInsuranceBase(SQLModel):
    patient_id: uuid.UUID = Field(foreign_key="patients.id")
    insurance_provider_id: uuid.UUID = Field(foreign_key="insurance_providers.id")
    policy_number: str = Field(max_length=100)
    is_primary: bool = Field(default=False)


class PatientInsuranceCreate(SQLModel):
    insurance_provider_id: uuid.UUID
    policy_number: str = Field(max_length=100)
    is_primary: bool = Field(default=False)


class PatientInsuranceUpdate(SQLModel):
    policy_number: str | None = Field(default=None, max_length=100)
    is_primary: bool | None = None


class PatientInsurance(PatientInsuranceBase, table=True):
    __tablename__ = "patient_insurance"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class PatientInsurancePublic(PatientInsuranceBase, SoftDeletePublic):
    pass


class PatientInsuranceWithProviderPublic(PatientInsurancePublic):
    insurance_provider_name: str


class PatientInsurancesPublic(SQLModel):
    data: list[PatientInsuranceWithProviderPublic]
    count: int


class DoctorBase(SQLModel):
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    provenance: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    title_id: uuid.UUID | None = Field(default=None, foreign_key="titles.id")


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(SQLModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    provenance: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    title_id: uuid.UUID | None = None


class Doctor(DoctorBase, table=True):
    __tablename__ = "doctors"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class DoctorPublic(DoctorBase, SoftDeletePublic):
    pass


class DoctorWithTitlePublic(DoctorPublic):
    title_name: str | None = None


class DoctorsPublic(SQLModel):
    data: list[DoctorWithTitlePublic]
    count: int


class CatalogBase(SQLModel):
    type: CatalogType = Field(
        sa_column=Column(pg_enum(CatalogType, "catalog_type"), nullable=False)
    )
    name: str = Field(max_length=255)
    code: str = Field(max_length=50)
    price: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    is_orderable: bool = Field(default=True)
    category_id: uuid.UUID | None = Field(default=None, foreign_key="categories.id")


class CatalogCreate(CatalogBase):
    pass


class CatalogUpdate(SQLModel):
    type: CatalogType | None = None
    name: str | None = Field(default=None, max_length=255)
    code: str | None = Field(default=None, max_length=50)
    price: Decimal | None = None
    is_orderable: bool | None = None
    category_id: uuid.UUID | None = None


class Catalog(CatalogBase, table=True):
    __tablename__ = "catalog"
    __table_args__ = (UniqueConstraint("code", name="uq_catalog_code"),)

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class CatalogPublic(CatalogBase, SoftDeletePublic):
    pass


class CatalogsPublic(SQLModel):
    data: list[CatalogPublic]
    count: int


class CatalogRelationshipReorderItem(SQLModel):
    id: uuid.UUID
    sort_order: int


class CatalogRelationshipReorderRequest(SQLModel):
    items: list[CatalogRelationshipReorderItem] = Field(min_length=1)


class CatalogSummaryPublic(CatalogPublic):
    category_name: str | None = None
    analytes_count: int = 0
    specimen_requirements_count: int = 0
    panel_items_count: int = 0


class CatalogSummariesPublic(SQLModel):
    data: list[CatalogSummaryPublic]
    count: int


class CatalogSpecimenRequirementBase(SQLModel):
    catalog_id: uuid.UUID = Field(
        foreign_key="catalog.id", primary_key=True, ondelete="CASCADE"
    )
    specimen_type_id: uuid.UUID = Field(
        foreign_key="specimen_types.id", primary_key=True
    )
    volume_ml: Decimal | None = Field(default=None, sa_column=Column(Numeric(6, 2)))
    instructions: str | None = Field(default=None, sa_column=Column(Text))


class CatalogSpecimenRequirementCreate(SQLModel):
    specimen_type_id: uuid.UUID
    volume_ml: Decimal | None = None
    instructions: str | None = None


class CatalogSpecimenRequirementUpsert(SQLModel):
    volume_ml: Decimal | None = None
    instructions: str | None = None


class CatalogSpecimenRequirement(CatalogSpecimenRequirementBase, table=True):
    __tablename__ = "catalog_specimen_requirements"


class CatalogSpecimenRequirementPublic(CatalogSpecimenRequirementBase):
    pass


class CatalogSpecimenRequirementDetailPublic(CatalogSpecimenRequirementPublic):
    specimen_type_name: str
    specimen_type_color: str | None = None


class CatalogPanelItemBase(SQLModel):
    panel_id: uuid.UUID = Field(foreign_key="catalog.id", ondelete="CASCADE")
    test_id: uuid.UUID = Field(foreign_key="catalog.id", ondelete="CASCADE")
    sort_order: int = Field(default=0)


class CatalogPanelItemCreate(SQLModel):
    test_id: uuid.UUID
    sort_order: int = Field(default=0)


class CatalogPanelItem(CatalogPanelItemBase, table=True):
    __tablename__ = "catalog_panel_items"
    __table_args__ = (UniqueConstraint("panel_id", "test_id", name="uq_panel_test"),)

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class CatalogPanelItemPublic(CatalogPanelItemBase, TimestampPublic):
    pass


class CatalogPanelItemDetailPublic(CatalogPanelItemPublic):
    test_code: str
    test_name: str
    test_price: Decimal


class AnalyteBase(SQLModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    unit_id: uuid.UUID | None = Field(default=None, foreign_key="units.id")
    data_type: AnalyteDataType = Field(
        sa_column=Column(pg_enum(AnalyteDataType, "data_type"), nullable=False)
    )
    options_data: Any | None = Field(default=None, sa_column=Column(JSONB))
    reference_text: str | None = Field(default=None, sa_column=Column(Text))
    is_calculated: bool = Field(default=False)
    calculation_formula: str | None = Field(default=None, sa_column=Column(Text))


class AnalyteCreate(AnalyteBase):
    pass


class AnalyteUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)
    unit_id: uuid.UUID | None = None
    data_type: AnalyteDataType | None = None
    options_data: Any | None = None
    reference_text: str | None = None
    is_calculated: bool | None = None
    calculation_formula: str | None = None


class Analyte(AnalyteBase, table=True):
    __tablename__ = "analytes"
    __table_args__ = (UniqueConstraint("code", name="uq_analytes_code"),)

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class AnalytePublic(AnalyteBase, SoftDeletePublic):
    pass


class AnalytesPublic(SQLModel):
    data: list[AnalytePublic]
    count: int


class CatalogItemAnalyteBase(SQLModel):
    catalog_item_id: uuid.UUID = Field(foreign_key="catalog.id", ondelete="CASCADE")
    analyte_id: uuid.UUID = Field(foreign_key="analytes.id")
    sort_order: int = Field(default=0)


class CatalogItemAnalyteCreate(SQLModel):
    analyte_id: uuid.UUID
    sort_order: int = Field(default=0)


class CatalogItemAnalyte(CatalogItemAnalyteBase, table=True):
    __tablename__ = "catalog_item_analytes"
    __table_args__ = (
        UniqueConstraint(
            "catalog_item_id", "analyte_id", name="uq_catalog_item_analyte"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class CatalogItemAnalytePublic(CatalogItemAnalyteBase, TimestampPublic):
    pass


class CatalogItemAnalyteDetailPublic(CatalogItemAnalytePublic):
    analyte_code: str
    analyte_name: str
    analyte_data_type: AnalyteDataType
    unit_name: str | None = None


class CatalogDetailPublic(CatalogSummaryPublic):
    analytes: list[CatalogItemAnalyteDetailPublic] = Field(default_factory=list)
    specimen_requirements: list[CatalogSpecimenRequirementDetailPublic] = Field(
        default_factory=list
    )
    panel_items: list[CatalogPanelItemDetailPublic] = Field(default_factory=list)


class ValidationRuleBase(SQLModel):
    analyte_id: uuid.UUID = Field(foreign_key="analytes.id")
    is_active: bool = Field(default=True)
    target_gender: TargetGenderType = Field(
        default=TargetGenderType.all,
        sa_column=Column(
            pg_enum(TargetGenderType, "target_gender_type"), nullable=False
        ),
    )
    min_age_years: int | None = None
    max_age_years: int | None = None
    required_context_id: uuid.UUID | None = Field(
        default=None, foreign_key="patient_contexts.id"
    )
    priority: int = Field(default=0)
    absurd_min: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 4)))
    absurd_max: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 4)))
    panic_min: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 4)))
    panic_max: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 4)))
    normal_min: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 4)))
    normal_max: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 4)))
    expected_value: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(12, 4))
    )
    max_delta_percent: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(6, 2))
    )
    is_required: bool = Field(default=False)
    regex_pattern: str | None = Field(default=None, sa_column=Column(Text))
    validation_message: str | None = Field(default=None, sa_column=Column(Text))
    allowed_values: Any | None = Field(default=None, sa_column=Column(JSONB))
    abnormal_values: Any | None = Field(default=None, sa_column=Column(JSONB))
    critical_values: Any | None = Field(default=None, sa_column=Column(JSONB))


class ValidationRuleCreate(ValidationRuleBase):
    pass


class ValidationRuleUpdate(SQLModel):
    analyte_id: uuid.UUID | None = None
    is_active: bool | None = None
    target_gender: TargetGenderType | None = None
    min_age_years: int | None = None
    max_age_years: int | None = None
    required_context_id: uuid.UUID | None = None
    priority: int | None = None
    absurd_min: Decimal | None = None
    absurd_max: Decimal | None = None
    panic_min: Decimal | None = None
    panic_max: Decimal | None = None
    normal_min: Decimal | None = None
    normal_max: Decimal | None = None
    expected_value: Decimal | None = None
    max_delta_percent: Decimal | None = None
    is_required: bool | None = None
    regex_pattern: str | None = None
    validation_message: str | None = None
    allowed_values: Any | None = None
    abnormal_values: Any | None = None
    critical_values: Any | None = None


class ValidationRule(ValidationRuleBase, table=True):
    __tablename__ = "validation_rules"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class ValidationRulePublic(ValidationRuleBase, TimestampPublic):
    pass


class ValidationRuleDetailPublic(ValidationRulePublic):
    analyte_code: str
    analyte_name: str
    analyte_data_type: AnalyteDataType
    unit_name: str | None = None
    required_context_name: str | None = None


class ValidationRulesPublic(SQLModel):
    data: list[ValidationRuleDetailPublic]
    count: int


class ValidationRuleSimulationRequest(SQLModel):
    analyte_id: uuid.UUID
    age_years: int | None = Field(default=None, ge=0)
    gender: GenderType | None = None
    patient_context_id: uuid.UUID | None = None
    result_value: str | None = None
    previous_value: str | None = None


class ValidationRuleSimulationResponse(SQLModel):
    matched_rule: ValidationRuleDetailPublic | None = None
    is_valid: bool
    is_abnormal: bool = False
    is_critical: bool = False
    is_absurd: bool = False
    delta_flag: bool = False
    classification: str
    message: str


class ConsistencyRuleBase(SQLModel):
    name: str = Field(max_length=255)
    formula: str = Field(sa_column=Column(Text, nullable=False))
    formula_description: str | None = Field(default=None, sa_column=Column(Text))
    error_message: str = Field(sa_column=Column(Text, nullable=False))
    severity: RuleSeverity = Field(
        sa_column=Column(pg_enum(RuleSeverity, "rule_severity"), nullable=False)
    )


class ConsistencyRuleCreate(ConsistencyRuleBase):
    analyte_ids: list[uuid.UUID] = Field(default_factory=list)


class ConsistencyRuleUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    formula: str | None = None
    formula_description: str | None = None
    error_message: str | None = None
    severity: RuleSeverity | None = None
    analyte_ids: list[uuid.UUID] | None = None


class ConsistencyRule(ConsistencyRuleBase, table=True):
    __tablename__ = "consistency_rules"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class ConsistencyRulePublic(ConsistencyRuleBase, SoftDeletePublic):
    pass


class FormulaReferencePublic(SQLModel):
    id: uuid.UUID
    code: str
    name: str
    data_type: AnalyteDataType
    unit_name: str | None = None


class ConsistencyRuleDetailPublic(ConsistencyRulePublic):
    analytes: list[FormulaReferencePublic] = Field(default_factory=list)


class ConsistencyRulesPublic(SQLModel):
    data: list[ConsistencyRuleDetailPublic]
    count: int


class ConsistencyRuleAnalyte(SQLModel, table=True):
    __tablename__ = "consistency_rule_analytes"
    __table_args__ = (
        UniqueConstraint("rule_id", "analyte_id", name="uq_consistency_rule_analyte"),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    rule_id: uuid.UUID = Field(foreign_key="consistency_rules.id", ondelete="CASCADE")
    analyte_id: uuid.UUID = Field(foreign_key="analytes.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class ConsistencyRuleAnalytePublic(TimestampPublic):
    rule_id: uuid.UUID
    analyte_id: uuid.UUID


class ReflexRuleBase(SQLModel):
    trigger_analyte_id: uuid.UUID = Field(foreign_key="analytes.id")
    trigger_operator: TriggerOperator = Field(
        sa_column=Column(pg_enum(TriggerOperator, "trigger_operator"), nullable=False)
    )
    trigger_value: str = Field(max_length=255)
    action_catalog_id: uuid.UUID = Field(foreign_key="catalog.id")


class ReflexRuleCreate(ReflexRuleBase):
    pass


class ReflexRuleUpdate(SQLModel):
    trigger_analyte_id: uuid.UUID | None = None
    trigger_operator: TriggerOperator | None = None
    trigger_value: str | None = Field(default=None, max_length=255)
    action_catalog_id: uuid.UUID | None = None


class ReflexRule(ReflexRuleBase, table=True):
    __tablename__ = "reflex_rules"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class ReflexRulePublic(ReflexRuleBase, SoftDeletePublic):
    pass


class ReflexRuleDetailPublic(ReflexRulePublic):
    trigger_analyte_code: str
    trigger_analyte_name: str
    trigger_analyte_data_type: AnalyteDataType
    trigger_unit_name: str | None = None
    action_catalog_code: str
    action_catalog_name: str
    action_catalog_type: CatalogType


class ReflexRulesPublic(SQLModel):
    data: list[ReflexRuleDetailPublic]
    count: int


class FormulaPreviewRequest(SQLModel):
    formula: str
    expected_result_type: FormulaResultType
    values: dict[str, str | int | float | Decimal | None] = Field(default_factory=dict)
    allowed_analyte_ids: list[uuid.UUID] | None = None


class FormulaPreviewResponse(SQLModel):
    references: list[FormulaReferencePublic] = Field(default_factory=list)
    result: str | None = None
    result_type: FormulaResultType | None = None
    is_valid: bool
    message: str


class ConsistencyRulePreviewRequest(SQLModel):
    formula: str
    analyte_ids: list[uuid.UUID] = Field(default_factory=list)
    values: dict[str, str | int | float | Decimal | None] = Field(default_factory=dict)


class ReflexRulePreviewRequest(SQLModel):
    trigger_operator: TriggerOperator
    trigger_value: str
    sample_value: str


class ReflexRulePreviewResponse(SQLModel):
    is_triggered: bool
    message: str


class InstrumentBase(SQLModel):
    name: str = Field(max_length=255)
    model: str | None = Field(default=None, max_length=255)
    serial_number: str | None = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    serial_number: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class Instrument(InstrumentBase, table=True):
    __tablename__ = "instruments"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class InstrumentPublic(InstrumentBase, TimestampPublic):
    pass


class InstrumentsPublic(SQLModel):
    data: list[InstrumentPublic]
    count: int


# ---------------------------------------------------------------------------
# Orders, specimens, and results
# ---------------------------------------------------------------------------


class OrderBase(SQLModel):
    accession_number: str = Field(max_length=30)
    patient_id: uuid.UUID = Field(foreign_key="patients.id")
    doctor_id: uuid.UUID | None = Field(default=None, foreign_key="doctors.id")
    patient_insurance_id: uuid.UUID | None = Field(
        default=None, foreign_key="patient_insurance.id"
    )
    patient_context_id: uuid.UUID | None = Field(
        default=None, foreign_key="patient_contexts.id"
    )
    notes: str | None = Field(default=None, sa_column=Column(Text))


class OrderLineOverride(SQLModel):
    catalog_id: uuid.UUID
    price_charged: Decimal = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)


class OrderItemAnalyteSelection(SQLModel):
    catalog_id: uuid.UUID
    analyte_ids: list[uuid.UUID]


class OrderPaymentInput(SQLModel):
    amount: Decimal = Field(gt=0)
    payment_method_id: uuid.UUID


class OrderPreviewRequest(SQLModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None = None
    patient_insurance_id: uuid.UUID | None = None
    patient_context_id: uuid.UUID | None = None
    notes: str | None = None
    catalog_ids: list[uuid.UUID] = Field(min_length=1)
    item_analytes: list[OrderItemAnalyteSelection] = Field(default_factory=list)
    line_overrides: list[OrderLineOverride] = Field(default_factory=list)
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)
    discount_reason: str | None = Field(default=None, max_length=500)
    initial_payment: OrderPaymentInput | None = None


class OrderCreate(OrderPreviewRequest):
    pass


class OrderUpdate(OrderPreviewRequest):
    correction_reason: str = Field(min_length=1, max_length=1000)
    expected_revision: int = Field(ge=1)


class OrderCancelRequest(SQLModel):
    reason: str = Field(min_length=1, max_length=1000)
    expected_revision: int = Field(ge=1)


class Order(OrderBase, table=True):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("accession_number", name="uq_orders_accession_number"),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    status: OrderStatus = Field(
        default=OrderStatus.registered,
        sa_column=Column(pg_enum(OrderStatus, "order_status"), nullable=False),
    )
    revision_number: int = Field(default=1, ge=1)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class OrderPublic(OrderBase, TimestampPublic):
    status: OrderStatus
    created_by: uuid.UUID
    revision_number: int = 1


class OrderRevision(SQLModel, table=True):
    __tablename__ = "order_revisions"
    __table_args__ = (
        UniqueConstraint("order_id", "revision_number", name="uq_order_revision"),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id", ondelete="CASCADE")
    revision_number: int = Field(ge=1)
    correction_reason: str = Field(sa_column=Column(Text, nullable=False))
    old_values: Any = Field(sa_column=Column(JSONB, nullable=False))
    new_values: Any = Field(sa_column=Column(JSONB, nullable=False))
    effects: Any = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    performed_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class OrderRevisionPublic(SQLModel):
    id: uuid.UUID
    order_id: uuid.UUID
    revision_number: int
    correction_reason: str
    old_values: Any
    new_values: Any
    effects: Any
    performed_by_id: uuid.UUID
    performed_by_name: str | None = None
    created_at: datetime | None = None


class OrderRevisionsPublic(SQLModel):
    data: list[OrderRevisionPublic]
    count: int


class OrdersPublic(SQLModel):
    data: list[OrderPublic]
    count: int


class OrderSpecimenBase(SQLModel):
    order_id: uuid.UUID = Field(foreign_key="orders.id", ondelete="CASCADE")
    specimen_type_id: uuid.UUID = Field(foreign_key="specimen_types.id")
    collection_time: datetime | None = Field(default=None, sa_type=TIMESTAMPTZ)
    collected_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    status: SpecimenStatus = Field(
        default=SpecimenStatus.pending,
        sa_column=Column(pg_enum(SpecimenStatus, "specimen_status"), nullable=False),
    )
    required_volume_ml: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(6, 2))
    )
    collection_instructions: str | None = Field(default=None, sa_column=Column(Text))
    rejection_reason_id: uuid.UUID | None = Field(
        default=None, foreign_key="rejection_reasons.id"
    )
    notes: str | None = Field(default=None, sa_column=Column(Text))
    replaces_specimen_id: uuid.UUID | None = Field(
        default=None, foreign_key="order_specimens.id"
    )
    attempt_number: int = Field(default=1, ge=1)
    rejected_at: datetime | None = Field(default=None, sa_type=TIMESTAMPTZ)
    rejected_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    is_superseded: bool = Field(default=False)
    superseded_revision_id: uuid.UUID | None = Field(
        default=None, foreign_key="order_revisions.id"
    )


class OrderSpecimenUpdate(SQLModel):
    collection_time: datetime | None = None
    collected_by: uuid.UUID | None = None
    status: SpecimenStatus | None = None
    rejection_reason_id: uuid.UUID | None = None
    notes: str | None = None


class OrderSpecimen(OrderSpecimenBase, table=True):
    __tablename__ = "order_specimens"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class OrderSpecimenPublic(OrderSpecimenBase, TimestampPublic):
    pass


class OrderSpecimensPublic(SQLModel):
    data: list[OrderSpecimenPublic]
    count: int


class OrderItemBase(SQLModel):
    order_id: uuid.UUID = Field(foreign_key="orders.id", ondelete="CASCADE")
    catalog_id: uuid.UUID = Field(foreign_key="catalog.id")
    catalog_price: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    price_charged: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    price_override_reason: str | None = Field(default=None, sa_column=Column(Text))
    is_covered_by_insurance: bool = Field(default=False)
    insurance_provider_name: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0)
    is_reflex_added: bool = Field(default=False)
    is_active: bool = Field(default=True)
    revision_id: uuid.UUID | None = Field(
        default=None, foreign_key="order_revisions.id"
    )
    source_catalog_ids: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )


class OrderItemCreate(SQLModel):
    catalog_id: uuid.UUID
    price_override_reason: str | None = None


class OrderItemUpdate(SQLModel):
    price_charged: Decimal | None = None
    price_override_reason: str | None = None
    is_covered_by_insurance: bool | None = None
    sort_order: int | None = None


class OrderItem(OrderItemBase, table=True):
    __tablename__ = "order_items"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class OrderItemPublic(OrderItemBase, TimestampPublic):
    pass


class OrderItemsPublic(SQLModel):
    data: list[OrderItemPublic]
    count: int


class OrderItemSpecimen(SQLModel, table=True):
    __tablename__ = "order_item_specimens"
    __table_args__ = (
        UniqueConstraint(
            "order_item_id", "order_specimen_id", name="uq_order_item_specimen"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    order_item_id: uuid.UUID = Field(foreign_key="order_items.id", ondelete="CASCADE")
    order_specimen_id: uuid.UUID = Field(
        foreign_key="order_specimens.id", ondelete="CASCADE"
    )
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class OrderItemSpecimenPublic(SQLModel):
    id: uuid.UUID
    order_item_id: uuid.UUID
    order_specimen_id: uuid.UUID
    created_at: datetime | None = None


class OrderCatalogItemAnalyte(SQLModel, table=True):
    __tablename__ = "order_catalog_item_analytes"
    __table_args__ = (
        UniqueConstraint(
            "order_item_id",
            "analyte_id",
            name="uq_order_catalog_item_analyte",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    order_item_id: uuid.UUID = Field(foreign_key="order_items.id", ondelete="CASCADE")
    analyte_id: uuid.UUID = Field(foreign_key="analytes.id")
    catalog_item_analyte_id: uuid.UUID | None = Field(
        default=None, foreign_key="catalog_item_analytes.id"
    )
    is_active: bool = Field(default=True)
    removed_revision_id: uuid.UUID | None = Field(
        default=None, foreign_key="order_revisions.id"
    )
    removal_reason: str | None = Field(default=None, sa_column=Column(Text))
    sort_order: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class OrderCatalogItemAnalytePublic(TimestampPublic):
    order_item_id: uuid.UUID
    analyte_id: uuid.UUID
    catalog_item_analyte_id: uuid.UUID | None = None
    is_active: bool
    sort_order: int


class OrderAnalyteDetailPublic(SQLModel):
    analyte_id: uuid.UUID
    analyte_code: str
    analyte_name: str
    analyte_data_type: AnalyteDataType
    unit_name: str | None = None
    sort_order: int
    has_result: bool = False
    has_verified_result: bool = False


class OrderItemAnalyteCustomizeRequest(SQLModel):
    analyte_ids: list[uuid.UUID]
    reason: str | None = Field(default=None, max_length=1000)
    expected_revision: int = Field(ge=1)


class AnalyteResultBase(SQLModel):
    order_item_id: uuid.UUID = Field(foreign_key="order_items.id", ondelete="CASCADE")
    analyte_id: uuid.UUID = Field(foreign_key="analytes.id")
    specimen_id: uuid.UUID = Field(foreign_key="order_specimens.id")
    instrument_id: uuid.UUID | None = Field(default=None, foreign_key="instruments.id")
    result_value: str | None = Field(default=None, sa_column=Column(Text))
    validation_rule_id: uuid.UUID | None = Field(
        default=None, foreign_key="validation_rules.id"
    )
    is_abnormal: bool = Field(default=False)
    is_critical: bool = Field(default=False)
    delta_flag: bool = Field(default=False)
    is_rejected: bool = Field(default=False)
    rejection_reason: str | None = Field(default=None, sa_column=Column(Text))
    status: ResultStatus = Field(
        default=ResultStatus.pending,
        sa_column=Column(pg_enum(ResultStatus, "result_status"), nullable=False),
    )
    is_superseded: bool = Field(default=False)
    superseded_revision_id: uuid.UUID | None = Field(
        default=None, foreign_key="order_revisions.id"
    )


class AnalyteResultCreate(SQLModel):
    analyte_id: uuid.UUID
    specimen_id: uuid.UUID
    result_value: str
    instrument_id: uuid.UUID | None = None


class AnalyteResultUpdate(SQLModel):
    result_value: str | None = None
    instrument_id: uuid.UUID | None = None


class AnalyteResult(AnalyteResultBase, table=True):
    __tablename__ = "analyte_results"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    resulted_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    resulted_at: datetime | None = Field(default=None, sa_type=TIMESTAMPTZ)
    verified_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    verified_at: datetime | None = Field(default=None, sa_type=TIMESTAMPTZ)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class AnalyteResultPublic(AnalyteResultBase, TimestampPublic):
    resulted_by_id: uuid.UUID | None = None
    resulted_at: datetime | None = None
    verified_by_id: uuid.UUID | None = None
    verified_at: datetime | None = None


class AnalyteResultsPublic(SQLModel):
    data: list[AnalyteResultPublic]
    count: int


class AnalyteResultCommentBase(SQLModel):
    analyte_result_id: uuid.UUID = Field(
        foreign_key="analyte_results.id", ondelete="CASCADE"
    )
    user_id: uuid.UUID = Field(foreign_key="user.id")
    comment: str = Field(sa_column=Column(Text, nullable=False))


class AnalyteResultCommentCreate(SQLModel):
    comment: str


class AnalyteResultComment(AnalyteResultCommentBase, table=True):
    __tablename__ = "analyte_result_comments"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class AnalyteResultCommentPublic(AnalyteResultCommentBase, TimestampPublic):
    pass


class AnalyteResultCommentsPublic(SQLModel):
    data: list[AnalyteResultCommentPublic]
    count: int


class CriticalNotificationBase(SQLModel):
    analyte_result_id: uuid.UUID = Field(foreign_key="analyte_results.id")
    notified_by_id: uuid.UUID = Field(foreign_key="user.id")
    notified_to_id: uuid.UUID = Field(foreign_key="user.id")
    method: CriticalMethod = Field(
        sa_column=Column(pg_enum(CriticalMethod, "critical_method"), nullable=False)
    )
    notes: str | None = Field(default=None, sa_column=Column(Text))


class CriticalNotificationCreate(SQLModel):
    notified_to_id: uuid.UUID
    method: CriticalMethod
    notes: str | None = None


class CriticalNotificationAcknowledge(SQLModel):
    notes: str | None = None


class CriticalNotification(CriticalNotificationBase, table=True):
    __tablename__ = "critical_notifications"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    notified_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    acknowledged: bool = Field(default=False)
    acknowledged_at: datetime | None = Field(default=None, sa_type=TIMESTAMPTZ)
    acknowledged_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class CriticalNotificationPublic(CriticalNotificationBase, TimestampPublic):
    notified_at: datetime | None = None
    acknowledged: bool
    acknowledged_at: datetime | None = None
    acknowledged_by_id: uuid.UUID | None = None


class CriticalNotificationsPublic(SQLModel):
    data: list[CriticalNotificationPublic]
    count: int


class ResultEntryValue(SQLModel):
    analyte_id: uuid.UUID
    specimen_id: uuid.UUID
    result_value: str
    instrument_id: uuid.UUID | None = None


class ResultBulkEntryRequest(SQLModel):
    order_item_id: uuid.UUID
    values: list[ResultEntryValue] = Field(min_length=1)


class ResultCommentRequest(SQLModel):
    comment: str = Field(min_length=1, max_length=4000)


class ResultCorrectionRequest(SQLModel):
    result_value: str
    reason: str = Field(min_length=1, max_length=1000)
    instrument_id: uuid.UUID | None = None


class ResultCorrectionHistoryPublic(SQLModel):
    id: uuid.UUID
    old_value: str | None = None
    new_value: str | None = None
    reason: str
    performed_by_name: str | None = None
    performed_at: datetime | None = None


class ResultValidationOutcomePublic(SQLModel):
    classification: str
    message: str
    is_abnormal: bool = False
    is_critical: bool = False
    delta_flag: bool = False


class ResultConsistencyOutcomePublic(SQLModel):
    rule_id: uuid.UUID
    name: str
    severity: RuleSeverity
    message: str


class ResultReflexOutcomePublic(SQLModel):
    rule_id: uuid.UUID
    catalog_id: uuid.UUID
    catalog_code: str
    catalog_name: str
    added: bool


class ResultCommentDetailPublic(AnalyteResultCommentPublic):
    user_name: str


class CriticalNotificationDetailPublic(CriticalNotificationPublic):
    accession_number: str
    patient_name: str
    analyte_code: str
    analyte_name: str
    result_value: str | None = None
    notified_by_name: str
    notified_to_name: str
    acknowledged_by_name: str | None = None


class CriticalNotificationListPublic(SQLModel):
    data: list[CriticalNotificationDetailPublic]
    count: int


class CriticalNotificationCountPublic(SQLModel):
    count: int


class CriticalRecipientPublic(SQLModel):
    id: uuid.UUID
    name: str
    email: str


class CriticalRecipientsPublic(SQLModel):
    data: list[CriticalRecipientPublic]
    count: int


class ResultAnalyteWorkspacePublic(SQLModel):
    result_id: uuid.UUID | None = None
    analyte_id: uuid.UUID
    analyte_code: str
    analyte_name: str
    data_type: AnalyteDataType
    unit_name: str | None = None
    options_data: Any | None = None
    reference_text: str | None = None
    is_calculated: bool = False
    specimen_id: uuid.UUID
    specimen_type_name: str
    result_value: str | None = None
    image_url: str | None = None
    status: ResultStatus = ResultStatus.pending
    validation_rule_id: uuid.UUID | None = None
    validation: ResultValidationOutcomePublic | None = None
    is_abnormal: bool = False
    is_critical: bool = False
    delta_flag: bool = False
    resulted_by_name: str | None = None
    resulted_at: datetime | None = None
    verified_by_name: str | None = None
    verified_at: datetime | None = None
    verification_eligible: bool = False
    verification_blocker: str | None = None
    escalation_required: bool = False
    critical_notifications: list[CriticalNotificationDetailPublic] = Field(
        default_factory=list
    )
    comments: list[ResultCommentDetailPublic] = Field(default_factory=list)
    corrections: list[ResultCorrectionHistoryPublic] = Field(default_factory=list)


class ResultTestWorkspacePublic(SQLModel):
    order_item_id: uuid.UUID
    catalog_id: uuid.UUID
    catalog_code: str
    catalog_name: str
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    is_reflex_added: bool = False
    analytes: list[ResultAnalyteWorkspacePublic] = Field(default_factory=list)
    resulted_count: int = 0
    verified_count: int = 0


class ResultWorkspacePublic(SQLModel):
    order_id: uuid.UUID
    revision_number: int = 1
    accession_number: str
    patient_id: uuid.UUID
    patient_identifier: str
    patient_name: str
    patient_date_of_birth: date
    patient_gender: GenderType
    patient_context_id: uuid.UUID | None = None
    patient_context_name: str | None = None
    doctor_name: str | None = None
    order_status: OrderStatus
    tests: list[ResultTestWorkspacePublic] = Field(default_factory=list)
    total_count: int = 0
    resulted_count: int = 0
    verified_count: int = 0
    consistency_outcomes: list[ResultConsistencyOutcomePublic] = Field(
        default_factory=list
    )
    reflex_outcomes: list[ResultReflexOutcomePublic] = Field(default_factory=list)


class ResultSubmissionPublic(SQLModel):
    workspace: ResultWorkspacePublic
    saved_result_ids: list[uuid.UUID] = Field(default_factory=list)
    critical_result_ids: list[uuid.UUID] = Field(default_factory=list)
    consistency_outcomes: list[ResultConsistencyOutcomePublic] = Field(
        default_factory=list
    )
    reflex_outcomes: list[ResultReflexOutcomePublic] = Field(default_factory=list)


class ResultVerificationSkipPublic(SQLModel):
    result_id: uuid.UUID | None = None
    order_item_id: uuid.UUID
    analyte_id: uuid.UUID
    specimen_id: uuid.UUID
    analyte_name: str
    message: str


class ResultBulkVerificationPublic(SQLModel):
    workspace: ResultWorkspacePublic
    verified_count: int = 0
    skipped_count: int = 0
    verified_result_ids: list[uuid.UUID] = Field(default_factory=list)
    skipped: list[ResultVerificationSkipPublic] = Field(default_factory=list)


class ResultQueueItemPublic(SQLModel):
    order_id: uuid.UUID
    accession_number: str
    patient_id: uuid.UUID
    patient_identifier: str
    patient_name: str
    order_status: OrderStatus
    category_summary: str
    total_count: int
    resulted_count: int
    verified_count: int
    abnormal_count: int
    critical_count: int
    created_at: datetime | None = None


class ResultQueuePublic(SQLModel):
    data: list[ResultQueueItemPublic]
    count: int


# ---------------------------------------------------------------------------
# Reports, notifications, finance, commissions, and audit
# ---------------------------------------------------------------------------


class ReportTemplateBase(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text))
    template_storage_url: str | None = Field(default=None, sa_column=Column(Text))
    is_default: bool = Field(default=False)


class ReportTemplateCreate(ReportTemplateBase):
    pass


class ReportTemplateUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    template_storage_url: str | None = None
    is_default: bool | None = None


class ReportTemplate(ReportTemplateBase, table=True):
    __tablename__ = "report_templates"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class ReportTemplatePublic(ReportTemplateBase, SoftDeletePublic):
    pass


class ReportTemplatesPublic(SQLModel):
    data: list[ReportTemplatePublic]
    count: int


class ReportBase(SQLModel):
    order_id: uuid.UUID = Field(foreign_key="orders.id")
    version: int = Field(default=1)
    report_template_id: uuid.UUID | None = Field(
        default=None, foreign_key="report_templates.id"
    )
    channel: ReportChannel = Field(
        sa_column=Column(pg_enum(ReportChannel, "report_channel"), nullable=False)
    )
    recipient_note: str | None = Field(default=None, sa_column=Column(Text))
    report_storage_url: str | None = Field(default=None, sa_column=Column(Text))


class ReportCreate(SQLModel):
    report_template_id: uuid.UUID | None = None
    channel: ReportChannel
    recipient_note: str | None = None


class Report(ReportBase, table=True):
    __tablename__ = "reports"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    released_by_id: uuid.UUID = Field(foreign_key="user.id")
    released_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    delivery_status: DeliveryStatus = Field(
        default=DeliveryStatus.pending,
        sa_column=Column(pg_enum(DeliveryStatus, "delivery_status"), nullable=False),
    )
    is_voided: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class ReportPublic(ReportBase, TimestampPublic):
    released_by_id: uuid.UUID
    released_at: datetime | None = None
    delivery_status: DeliveryStatus
    is_voided: bool


class ReportsPublic(SQLModel):
    data: list[ReportPublic]
    count: int


class NotificationBase(SQLModel):
    order_id: uuid.UUID | None = Field(default=None, foreign_key="orders.id")
    patient_id: uuid.UUID | None = Field(default=None, foreign_key="patients.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    type: NotificationType = Field(
        sa_column=Column(pg_enum(NotificationType, "notification_type"), nullable=False)
    )
    channel: NotificationChannel = Field(
        sa_column=Column(
            pg_enum(NotificationChannel, "notification_channel"), nullable=False
        )
    )
    message: str = Field(sa_column=Column(Text, nullable=False))


class Notification(NotificationBase, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    status: NotificationStatus = Field(
        default=NotificationStatus.pending,
        sa_column=Column(
            pg_enum(NotificationStatus, "notification_status"), nullable=False
        ),
    )
    sent_at: datetime | None = Field(default=None, sa_type=TIMESTAMPTZ)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class NotificationPublic(NotificationBase, TimestampPublic):
    status: NotificationStatus
    sent_at: datetime | None = None


class NotificationsPublic(SQLModel):
    data: list[NotificationPublic]
    count: int


class InsurancePricingBase(SQLModel):
    insurance_provider_id: uuid.UUID = Field(foreign_key="insurance_providers.id")
    catalog_id: uuid.UUID = Field(foreign_key="catalog.id")
    insurance_price: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))


class InsurancePricingCreate(InsurancePricingBase):
    pass


class InsurancePricingUpdate(SQLModel):
    insurance_price: Decimal | None = None


class InsurancePricing(InsurancePricingBase, table=True):
    __tablename__ = "insurance_pricing"
    __table_args__ = (
        UniqueConstraint(
            "insurance_provider_id", "catalog_id", name="uq_insurance_pricing"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class InsurancePricingPublic(InsurancePricingBase, TimestampPublic):
    pass


class InsurancePricingDetailPublic(InsurancePricingPublic):
    insurance_provider_name: str
    catalog_code: str
    catalog_name: str
    catalog_price: Decimal


class InsurancePricingsPublic(SQLModel):
    data: list[InsurancePricingDetailPublic]
    count: int


class FinanceSettingsBase(SQLModel):
    discount_allocation_policy: DiscountAllocationPolicy = Field(
        default=DiscountAllocationPolicy.non_insured_first,
        sa_column=Column(
            pg_enum(DiscountAllocationPolicy, "discount_allocation_policy"),
            nullable=False,
        ),
    )
    default_commission_rate: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(5, 4), nullable=True)
    )
    default_insurance_commission_rate: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(5, 4), nullable=True)
    )


class FinanceSettingsUpdate(SQLModel):
    discount_allocation_policy: DiscountAllocationPolicy | None = None
    default_commission_rate: Decimal | None = None
    default_insurance_commission_rate: Decimal | None = None


class FinanceSettings(FinanceSettingsBase, table=True):
    __tablename__ = "finance_settings"

    id: int = Field(default=1, primary_key=True)
    updated_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class FinanceSettingsPublic(FinanceSettingsBase, TimestampPublic):
    id: int
    updated_by_id: uuid.UUID | None = None


class LabSettingsBase(SQLModel):
    display_name: str = Field(default="KENEYA LAB", min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    slogan: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, sa_column=Column(Text))
    city: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=120)
    primary_phone: str | None = Field(default=None, max_length=50)
    secondary_phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    registration_number: str | None = Field(default=None, max_length=100)
    laboratory_license: str | None = Field(default=None, max_length=100)
    tax_id: str | None = Field(default=None, max_length=100)
    bank_name: str | None = Field(default=None, max_length=255)
    bank_account_holder: str | None = Field(default=None, max_length=255)
    bank_account_number: str | None = Field(default=None, max_length=120)
    payment_instructions: str | None = Field(default=None, sa_column=Column(Text))
    director_name: str | None = Field(default=None, max_length=255)
    director_title: str | None = Field(default=None, max_length=255)
    document_footer: str | None = Field(default=None, sa_column=Column(Text))

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(TypeAdapter(EmailStr).validate_python(value))

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(TypeAdapter(AnyHttpUrl).validate_python(value))


class LabSettingsUpdate(SQLModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    slogan: str | None = Field(default=None, max_length=255)
    address: str | None = None
    city: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=120)
    primary_phone: str | None = Field(default=None, max_length=50)
    secondary_phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    registration_number: str | None = Field(default=None, max_length=100)
    laboratory_license: str | None = Field(default=None, max_length=100)
    tax_id: str | None = Field(default=None, max_length=100)
    bank_name: str | None = Field(default=None, max_length=255)
    bank_account_holder: str | None = Field(default=None, max_length=255)
    bank_account_number: str | None = Field(default=None, max_length=120)
    payment_instructions: str | None = None
    director_name: str | None = Field(default=None, max_length=255)
    director_title: str | None = Field(default=None, max_length=255)
    document_footer: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(TypeAdapter(EmailStr).validate_python(value))

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(TypeAdapter(AnyHttpUrl).validate_python(value))


class LabSettings(LabSettingsBase, table=True):
    __tablename__ = "lab_settings"

    id: int = Field(default=1, primary_key=True)
    logo_object_key: str | None = Field(default=None, max_length=500)
    updated_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class LabSettingsPublic(LabSettingsBase, TimestampPublic):
    id: int
    logo_url: str | None = None
    updated_by_id: uuid.UUID | None = None


class InvoiceBase(SQLModel):
    order_id: uuid.UUID = Field(foreign_key="orders.id")
    invoice_number: str = Field(max_length=30)
    version: int = Field(default=1)
    is_voided: bool = Field(default=False)
    total_amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    discount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    discount_reason: str | None = Field(default=None, sa_column=Column(Text))
    net_amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    amount_paid: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.unpaid,
        sa_column=Column(pg_enum(PaymentStatus, "payment_status"), nullable=False),
    )
    payment_method_id: uuid.UUID | None = Field(
        default=None, foreign_key="payment_methods.id"
    )


class InvoiceCreate(SQLModel):
    discount: Decimal = Decimal("0.00")


class InvoiceUpdate(SQLModel):
    discount: Decimal | None = None
    payment_method_id: uuid.UUID | None = None


class PaymentCollect(SQLModel):
    amount: Decimal = Field(gt=0)
    payment_method_id: uuid.UUID


class Invoice(InvoiceBase, table=True):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "version", name="uq_invoice_number_version"),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class InvoicePublic(InvoiceBase, TimestampPublic):
    created_by_id: uuid.UUID


class InvoicesPublic(SQLModel):
    data: list[InvoicePublic]
    count: int


class InvoiceLine(SQLModel, table=True):
    __tablename__ = "invoice_lines"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    invoice_id: uuid.UUID = Field(foreign_key="invoices.id", ondelete="CASCADE")
    order_item_id: uuid.UUID = Field(foreign_key="order_items.id")
    catalog_code: str = Field(max_length=100)
    catalog_name: str = Field(max_length=255)
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    is_covered_by_insurance: bool = Field(default=False)
    insurance_provider_name: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class InvoiceLinePublic(SQLModel):
    id: uuid.UUID
    order_item_id: uuid.UUID
    catalog_code: str
    catalog_name: str
    amount: Decimal
    is_covered_by_insurance: bool
    insurance_provider_name: str | None = None
    sort_order: int


class PaymentTransaction(SQLModel, table=True):
    __tablename__ = "payment_transactions"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    invoice_id: uuid.UUID = Field(foreign_key="invoices.id", ondelete="CASCADE")
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    payment_method_id: uuid.UUID = Field(foreign_key="payment_methods.id")
    status: PaymentTransactionStatus = Field(
        default=PaymentTransactionStatus.completed,
        sa_column=Column(
            pg_enum(PaymentTransactionStatus, "payment_transaction_status"),
            nullable=False,
        ),
    )
    collected_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class PaymentTransactionPublic(SQLModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Decimal
    payment_method_id: uuid.UUID
    payment_method_name: str
    status: PaymentTransactionStatus
    collected_by_id: uuid.UUID
    collected_by_name: str | None = None
    refunded_amount: Decimal = Decimal("0.00")
    refundable_amount: Decimal = Decimal("0.00")
    created_at: datetime | None = None


class PaymentRefund(SQLModel, table=True):
    __tablename__ = "payment_refunds"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    payment_id: uuid.UUID = Field(
        foreign_key="payment_transactions.id", ondelete="CASCADE"
    )
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    payment_method_id: uuid.UUID = Field(foreign_key="payment_methods.id")
    reason: str = Field(sa_column=Column(Text, nullable=False))
    refunded_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class PaymentRefundCreate(SQLModel):
    amount: Decimal = Field(gt=0)
    payment_method_id: uuid.UUID
    reason: str = Field(min_length=1, max_length=1000)


class PaymentRefundPublic(SQLModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    amount: Decimal
    payment_method_id: uuid.UUID
    payment_method_name: str
    reason: str
    refunded_by_id: uuid.UUID
    refunded_by_name: str | None = None
    created_at: datetime | None = None


class InvoiceBalanceTransfer(SQLModel, table=True):
    __tablename__ = "invoice_balance_transfers"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    source_invoice_id: uuid.UUID = Field(foreign_key="invoices.id")
    target_invoice_id: uuid.UUID = Field(foreign_key="invoices.id")
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    created_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class InvoiceBalanceTransferPublic(SQLModel):
    id: uuid.UUID
    source_invoice_id: uuid.UUID
    target_invoice_id: uuid.UUID
    amount: Decimal
    created_by_id: uuid.UUID
    created_by_name: str | None = None
    created_at: datetime | None = None


class CustomerCredit(SQLModel, table=True):
    __tablename__ = "customer_credits"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id")
    source_invoice_id: uuid.UUID = Field(foreign_key="invoices.id")
    order_revision_id: uuid.UUID = Field(foreign_key="order_revisions.id")
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    reason: str = Field(sa_column=Column(Text, nullable=False))
    is_resolved: bool = Field(default=False)
    created_by_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class CustomerCreditPublic(SQLModel):
    id: uuid.UUID
    order_id: uuid.UUID
    source_invoice_id: uuid.UUID
    order_revision_id: uuid.UUID
    amount: Decimal
    reason: str
    is_resolved: bool
    created_by_id: uuid.UUID
    created_at: datetime | None = None


class InvoiceReissueRequest(SQLModel):
    discount: Decimal = Field(ge=0)
    reason: str = Field(min_length=1, max_length=1000)


class InvoiceListItemPublic(SQLModel):
    id: uuid.UUID
    invoice_number: str
    version: int
    is_voided: bool
    order_id: uuid.UUID
    accession_number: str
    patient_id: uuid.UUID
    patient_identifier: str
    patient_name: str
    insurance_provider_name: str | None = None
    total_amount: Decimal
    discount: Decimal
    net_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    payment_status: PaymentStatus
    created_at: datetime | None = None


class InvoiceListPublic(SQLModel):
    data: list[InvoiceListItemPublic]
    count: int


class InvoiceSummaryPublic(SQLModel):
    count: int
    net_billed: Decimal
    collected: Decimal
    outstanding: Decimal


class InvoiceDetailPublic(InvoicePublic):
    accession_number: str
    patient_id: uuid.UUID
    patient_identifier: str
    patient_name: str
    doctor_name: str | None = None
    insurance_provider_name: str | None = None
    insurance_policy_number: str | None = None
    created_by_name: str | None = None
    balance_due: Decimal
    lines: list[InvoiceLinePublic] = Field(default_factory=list)
    payments: list[PaymentTransactionPublic] = Field(default_factory=list)
    refunds: list[PaymentRefundPublic] = Field(default_factory=list)
    transfers: list[InvoiceBalanceTransferPublic] = Field(default_factory=list)
    versions: list[InvoicePublic] = Field(default_factory=list)


class OrderPreviewItemPublic(SQLModel):
    catalog_id: uuid.UUID
    catalog_code: str
    catalog_name: str
    catalog_price: Decimal
    price_charged: Decimal
    is_covered_by_insurance: bool
    insurance_provider_name: str | None = None
    price_override_reason: str | None = None
    source_catalog_ids: list[uuid.UUID] = Field(default_factory=list)
    analytes: list[OrderAnalyteDetailPublic] = Field(default_factory=list)


class OrderPreviewSpecimenPublic(SQLModel):
    specimen_type_id: uuid.UUID
    specimen_type_name: str
    specimen_type_color: str | None = None
    required_volume_ml: Decimal | None = None
    collection_instructions: str | None = None
    catalog_ids: list[uuid.UUID] = Field(default_factory=list)


class OrderPreviewPublic(SQLModel):
    items: list[OrderPreviewItemPublic]
    specimens: list[OrderPreviewSpecimenPublic]
    total_amount: Decimal
    discount: Decimal
    net_amount: Decimal
    initial_payment_amount: Decimal
    balance_due: Decimal


class OrderListItemPublic(SQLModel):
    id: uuid.UUID
    accession_number: str
    patient_id: uuid.UUID
    patient_identifier: str
    patient_name: str
    doctor_id: uuid.UUID | None = None
    doctor_name: str | None = None
    status: OrderStatus
    net_amount: Decimal
    payment_status: PaymentStatus
    created_at: datetime | None = None


class OrderListPublic(SQLModel):
    data: list[OrderListItemPublic]
    count: int


class OrderItemDetailPublic(OrderItemPublic):
    catalog_code: str
    catalog_name: str
    specimen_ids: list[uuid.UUID] = Field(default_factory=list)
    analytes: list[OrderAnalyteDetailPublic] = Field(default_factory=list)


class OrderSpecimenDetailPublic(OrderSpecimenPublic):
    specimen_type_name: str
    specimen_type_color: str | None = None
    collected_by_name: str | None = None
    rejected_by_name: str | None = None
    rejection_reason_name: str | None = None
    is_active_attempt: bool = True


class SpecimenCollectRequest(SQLModel):
    specimen_ids: list[uuid.UUID] = Field(min_length=1)
    collection_time: datetime | None = None


class SpecimenRejectRequest(SQLModel):
    rejection_reason_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=1000)


class SpecimenQueueItemPublic(SQLModel):
    order_id: uuid.UUID
    accession_number: str
    patient_id: uuid.UUID
    patient_identifier: str
    patient_name: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime | None = None
    pending_count: int
    collected_count: int
    rejected_count: int
    specimen_count: int
    specimen_summary: str


class SpecimenQueuePublic(SQLModel):
    data: list[SpecimenQueueItemPublic]
    count: int


class SpecimenWorkspacePublic(SQLModel):
    order_id: uuid.UUID
    accession_number: str
    patient_identifier: str
    patient_name: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    balance_due: Decimal
    specimens: list[OrderSpecimenDetailPublic] = Field(default_factory=list)


class DashboardMetricPublic(SQLModel):
    key: str
    label: str
    value: int | Decimal
    unit: str | None = None


class DashboardStatusPointPublic(SQLModel):
    key: str
    label: str
    count: int


class DashboardTrendPointPublic(SQLModel):
    label: str
    orders: int = 0
    specimens: int = 0
    results: int = 0
    revenue: Decimal = Decimal("0.00")


class DashboardActionPublic(SQLModel):
    key: str
    label: str
    description: str
    href: str
    priority: int = 0


class DashboardOrdersPublic(SQLModel):
    metrics: list[DashboardMetricPublic] = Field(default_factory=list)
    status_breakdown: list[DashboardStatusPointPublic] = Field(default_factory=list)
    recent: list[OrderListItemPublic] = Field(default_factory=list)


class DashboardSpecimensPublic(SQLModel):
    metrics: list[DashboardMetricPublic] = Field(default_factory=list)
    oldest_waiting: SpecimenQueueItemPublic | None = None


class DashboardResultsPublic(SQLModel):
    metrics: list[DashboardMetricPublic] = Field(default_factory=list)


class DashboardCriticalPublic(SQLModel):
    metrics: list[DashboardMetricPublic] = Field(default_factory=list)
    latest: list[CriticalNotificationDetailPublic] = Field(default_factory=list)


class DashboardFinancePublic(SQLModel):
    metrics: list[DashboardMetricPublic] = Field(default_factory=list)


class DashboardPublic(SQLModel):
    generated_at: datetime
    created_from: datetime
    created_to: datetime
    orders: DashboardOrdersPublic | None = None
    specimens: DashboardSpecimensPublic | None = None
    results: DashboardResultsPublic | None = None
    critical: DashboardCriticalPublic | None = None
    finance: DashboardFinancePublic | None = None
    trends: list[DashboardTrendPointPublic] = Field(default_factory=list)
    quick_actions: list[DashboardActionPublic] = Field(default_factory=list)


class OrderDetailPublic(OrderPublic):
    patient_identifier: str
    patient_name: str
    patient_date_of_birth: date
    patient_gender: GenderType
    doctor_name: str | None = None
    patient_context_name: str | None = None
    insurance_provider_name: str | None = None
    insurance_policy_number: str | None = None
    created_by_name: str | None = None
    items: list[OrderItemDetailPublic] = Field(default_factory=list)
    specimens: list[OrderSpecimenDetailPublic] = Field(default_factory=list)
    invoice: InvoicePublic
    payments: list[PaymentTransactionPublic] = Field(default_factory=list)


class SuggestedIdentifierPublic(SQLModel):
    identifier: str


class DoctorCommissionConfigBase(SQLModel):
    doctor_id: uuid.UUID = Field(foreign_key="doctors.id")
    commission_rate: Decimal = Field(sa_column=Column(Numeric(5, 4), nullable=False))
    insurance_commission_rate: Decimal = Field(
        sa_column=Column(Numeric(5, 4), nullable=False)
    )
    effective_from: date
    effective_until: date | None = None


class DoctorCommissionConfigCreate(SQLModel):
    commission_rate: Decimal
    insurance_commission_rate: Decimal
    effective_from: date
    effective_until: date | None = None


class DoctorCommissionConfigUpdate(SQLModel):
    commission_rate: Decimal | None = None
    insurance_commission_rate: Decimal | None = None
    effective_until: date | None = None


class DoctorCommissionConfig(DoctorCommissionConfigBase, table=True):
    __tablename__ = "doctor_commission_configs"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class DoctorCommissionConfigPublic(DoctorCommissionConfigBase, TimestampPublic):
    pass


class DoctorCommissionConfigsPublic(SQLModel):
    data: list[DoctorCommissionConfigPublic]
    count: int


class DoctorCommissionEntryBase(SQLModel):
    order_id: uuid.UUID = Field(foreign_key="orders.id")
    doctor_id: uuid.UUID = Field(foreign_key="doctors.id")
    order_net_amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    insured_net_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    insured_rate_applied: Decimal = Field(
        default=Decimal("0.0000"), sa_column=Column(Numeric(5, 4), nullable=False)
    )
    insured_commission_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    non_insured_net_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    non_insured_rate_applied: Decimal = Field(
        default=Decimal("0.0000"), sa_column=Column(Numeric(5, 4), nullable=False)
    )
    non_insured_commission_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    discount_allocation_policy: DiscountAllocationPolicy = Field(
        sa_column=Column(
            pg_enum(DiscountAllocationPolicy, "discount_allocation_policy"),
            nullable=False,
        )
    )
    commission_amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    payout_status: PayoutStatus = Field(
        default=PayoutStatus.pending,
        sa_column=Column(pg_enum(PayoutStatus, "payout_status"), nullable=False),
    )
    paid_at: datetime | None = Field(default=None, sa_type=TIMESTAMPTZ)


class DoctorCommissionEntry(DoctorCommissionEntryBase, table=True):
    __tablename__ = "doctor_commission_entries"
    __table_args__ = (
        UniqueConstraint("order_id", "doctor_id", name="uq_commission_entry_per_order"),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class DoctorCommissionEntryPublic(DoctorCommissionEntryBase, TimestampPublic):
    pass


class DoctorCommissionEntriesPublic(SQLModel):
    data: list[DoctorCommissionEntryPublic]
    count: int


class DoctorCommissionEntryListItemPublic(DoctorCommissionEntryPublic):
    doctor_name: str
    patient_id: uuid.UUID
    patient_name: str
    accession_number: str
    invoice_number: str
    total_adjustments: Decimal
    unsettled_adjustments: Decimal
    outstanding_amount: Decimal
    adjustment_count: int


class DoctorCommissionEntryListPublic(SQLModel):
    data: list[DoctorCommissionEntryListItemPublic]
    count: int


class DoctorCommissionAdjustmentCreate(SQLModel):
    amount: Decimal
    reason: str = Field(min_length=1, max_length=2000)


class DoctorCommissionAdjustment(SQLModel, table=True):
    __tablename__ = "doctor_commission_adjustments"
    __table_args__ = (
        CheckConstraint(
            "(order_revision_id IS NOT NULL) <> (created_by_id IS NOT NULL)",
            name="ck_commission_adjustment_source",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    commission_entry_id: uuid.UUID = Field(foreign_key="doctor_commission_entries.id")
    order_revision_id: uuid.UUID | None = Field(
        default=None, foreign_key="order_revisions.id"
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    reason: str = Field(sa_column=Column(Text, nullable=False))
    is_settled: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class DoctorCommissionAdjustmentPublic(SQLModel):
    id: uuid.UUID
    commission_entry_id: uuid.UUID
    order_revision_id: uuid.UUID | None = None
    created_by_id: uuid.UUID | None = None
    created_by_name: str | None = None
    source: str
    amount: Decimal
    reason: str
    is_settled: bool
    created_at: datetime


class DoctorCommissionEntryDetailPublic(DoctorCommissionEntryListItemPublic):
    adjustments: list[DoctorCommissionAdjustmentPublic] = Field(default_factory=list)


class DoctorCommissionPaymentBase(SQLModel):
    doctor_id: uuid.UUID = Field(foreign_key="doctors.id")
    total_commission_amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False)
    )


class DoctorCommissionPaymentCreate(SQLModel):
    line_ids: list[str] = Field(min_length=1)
    payment_method_id: uuid.UUID
    reference: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=2000)


class DoctorCommissionPayment(DoctorCommissionPaymentBase, table=True):
    __tablename__ = "doctor_commission_payments"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    payment_method_id: uuid.UUID = Field(foreign_key="payment_methods.id")
    reference: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class DoctorCommissionPaymentPublic(DoctorCommissionPaymentBase, TimestampPublic):
    created_by: uuid.UUID
    payment_method_id: uuid.UUID
    reference: str | None = None
    note: str | None = None


class DoctorCommissionPaymentsPublic(SQLModel):
    data: list[DoctorCommissionPaymentPublic]
    count: int


class DoctorCommissionPaymentEntry(SQLModel, table=True):
    __tablename__ = "doctor_commission_payment_entries"
    __table_args__ = (
        UniqueConstraint(
            "commission_payment_id", "commission_entry_id", name="uq_payment_entry"
        ),
        UniqueConstraint(
            "commission_payment_id",
            "commission_adjustment_id",
            name="uq_payment_adjustment",
        ),
        CheckConstraint(
            "(commission_entry_id IS NOT NULL) <> "
            "(commission_adjustment_id IS NOT NULL)",
            name="ck_commission_payment_line_source",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    commission_payment_id: uuid.UUID = Field(
        foreign_key="doctor_commission_payments.id", ondelete="CASCADE"
    )
    commission_entry_id: uuid.UUID | None = Field(
        default=None, foreign_key="doctor_commission_entries.id"
    )
    commission_adjustment_id: uuid.UUID | None = Field(
        default=None, foreign_key="doctor_commission_adjustments.id"
    )
    order_id: uuid.UUID = Field(foreign_key="orders.id")
    accession_number: str = Field(max_length=30)
    invoice_number: str = Field(max_length=30)
    order_date: datetime = Field(sa_type=TIMESTAMPTZ)
    patient_first_name: str = Field(max_length=100)
    patient_last_name: str = Field(max_length=100)
    line_type: str = Field(max_length=20)
    description: str = Field(sa_column=Column(Text, nullable=False))
    insured_net_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    non_insured_net_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    insured_commission_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    non_insured_commission_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False)
    )
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    source_created_at: datetime = Field(sa_type=TIMESTAMPTZ)
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    updated_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class DoctorCommissionPaymentEntryPublic(TimestampPublic):
    commission_payment_id: uuid.UUID
    commission_entry_id: uuid.UUID | None = None
    commission_adjustment_id: uuid.UUID | None = None
    order_id: uuid.UUID
    accession_number: str
    invoice_number: str
    order_date: datetime
    patient_first_name: str
    patient_last_name: str
    line_type: str
    description: str
    insured_net_amount: Decimal
    non_insured_net_amount: Decimal
    insured_commission_amount: Decimal
    non_insured_commission_amount: Decimal
    amount: Decimal
    source_created_at: datetime


class DoctorCommissionPayableLinePublic(SQLModel):
    id: str
    line_type: str
    source_id: uuid.UUID
    doctor_id: uuid.UUID
    doctor_name: str
    order_id: uuid.UUID
    accession_number: str
    invoice_number: str
    order_date: datetime
    patient_first_name: str
    patient_last_name: str
    description: str
    insured_net_amount: Decimal
    non_insured_net_amount: Decimal
    insured_commission_amount: Decimal
    non_insured_commission_amount: Decimal
    amount: Decimal
    created_at: datetime


class DoctorCommissionPayableLinesPublic(SQLModel):
    data: list[DoctorCommissionPayableLinePublic]
    count: int


class DoctorCommissionPaymentLinePublic(DoctorCommissionPayableLinePublic):
    pass


class DoctorCommissionPaymentListItemPublic(DoctorCommissionPaymentPublic):
    doctor_name: str
    created_by_name: str | None = None
    payment_method_name: str
    line_count: int


class DoctorCommissionPaymentListPublic(SQLModel):
    data: list[DoctorCommissionPaymentListItemPublic]
    count: int


class DoctorCommissionPaymentDetailPublic(DoctorCommissionPaymentListItemPublic):
    lines: list[DoctorCommissionPaymentLinePublic] = Field(default_factory=list)


class DoctorCommissionPaymentPreviewPublic(SQLModel):
    doctor_id: uuid.UUID
    doctor_name: str
    payment_method_id: uuid.UUID
    payment_method_name: str
    reference: str | None = None
    note: str | None = None
    lines: list[DoctorCommissionPayableLinePublic]
    total_commission_amount: Decimal


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid_pk, primary_key=True)
    table_name: str = Field(max_length=100)
    record_id: uuid.UUID | None = None
    action: AuditAction = Field(
        sa_column=Column(pg_enum(AuditAction, "audit_action"), nullable=False)
    )
    category: AuditCategory = Field(
        default=AuditCategory.system,
        sa_column=Column(pg_enum(AuditCategory, "audit_category"), nullable=False),
    )
    record_label: str | None = Field(default=None, max_length=255)
    old_values: Any | None = Field(default=None, sa_column=Column(JSONB))
    new_values: Any | None = Field(default=None, sa_column=Column(JSONB))
    metadata_json: Any | None = Field(
        default=None,
        sa_column=Column("metadata", JSONB),
    )
    performed_by_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        ondelete="SET NULL",
    )
    actor_name: str | None = Field(default=None, max_length=255)
    actor_email: str | None = Field(default=None, max_length=255)
    request_id: str | None = Field(default=None, max_length=100)
    correlation_id: str | None = Field(default=None, max_length=100)
    source: str = Field(default="system", max_length=30)
    ip_address: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=500)
    http_method: str | None = Field(default=None, max_length=10)
    http_path: str | None = Field(default=None, max_length=500)
    performed_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )
    created_at: datetime = Field(
        default_factory=utc_timestamp_field, sa_type=TIMESTAMPTZ
    )


class AuditLogPublic(SQLModel):
    id: uuid.UUID
    table_name: str
    record_id: uuid.UUID | None = None
    action: AuditAction
    category: AuditCategory
    record_label: str | None = None
    old_values: Any | None = None
    new_values: Any | None = None
    audit_metadata: Any | None = Field(
        default=None,
        validation_alias="metadata",
        serialization_alias="metadata",
    )
    performed_by_id: uuid.UUID | None = None
    actor_name: str | None = None
    actor_email: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    source: str
    ip_address: str | None = None
    user_agent: str | None = None
    http_method: str | None = None
    http_path: str | None = None
    performed_at: datetime | None = None
    created_at: datetime | None = None


class AuditLogsPublic(SQLModel):
    data: list[AuditLogPublic]
    count: int


class AuditSummaryPublic(SQLModel):
    total: int
    inserts: int
    updates: int
    deletes: int
    security_events: int


class AuditActorPublic(SQLModel):
    id: uuid.UUID
    name: str | None = None
    email: str | None = None


class AuditActorsPublic(SQLModel):
    data: list[AuditActorPublic]


__all__ = [
    name
    for name, value in globals().items()
    if isinstance(value, type) and getattr(value, "__module__", None) == __name__
]
