"""add_lis_foundation_models

Revision ID: 7f8a9b0c1d2e
Revises: 43d71e16ae17
Create Date: 2026-06-01 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "7f8a9b0c1d2e"
down_revision = "43d71e16ae17"
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gist"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    op.execute("""
CREATE TYPE gender_type AS ENUM ('male', 'female');
CREATE TYPE data_type AS ENUM ('numeric', 'text', 'options', 'image');
CREATE TYPE catalog_type AS ENUM ('item', 'panel');
CREATE TYPE target_gender_type AS ENUM ('male', 'female', 'all');
CREATE TYPE trigger_operator AS ENUM ('gt', 'lt', 'eq', 'gte', 'lte', 'in');
CREATE TYPE rule_severity AS ENUM ('warning', 'error');
CREATE TYPE order_status AS ENUM ('registered', 'collected', 'in_progress', 'partial_results', 'completed', 'cancelled');
CREATE TYPE specimen_status AS ENUM ('collected', 'rejected', 'processed');
CREATE TYPE result_status AS ENUM ('pending', 'resulted', 'verified', 'rejected');
CREATE TYPE payout_status AS ENUM ('pending', 'paid');
CREATE TYPE payment_status AS ENUM ('unpaid', 'paid', 'partial', 'refunded');
CREATE TYPE report_channel AS ENUM ('print', 'email', 'whatsapp', 'portal');
CREATE TYPE delivery_status AS ENUM ('pending', 'sent', 'failed');
CREATE TYPE notification_type AS ENUM ('result_ready', 'order_update', 'report_released', 'general');
CREATE TYPE notification_channel AS ENUM ('sms', 'email', 'whatsapp', 'in_app');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed');
CREATE TYPE critical_method AS ENUM ('call', 'sms', 'in_app', 'email');
CREATE TYPE audit_action AS ENUM ('insert', 'update', 'delete');
""")

    op.execute("""
CREATE TABLE titles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE patient_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE rejection_reasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE insurance_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender gender_type NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_patients_identifier UNIQUE (identifier)
);
CREATE INDEX idx_patients_identifier ON patients (identifier);
CREATE INDEX idx_patients_first_name ON patients USING GIN (first_name gin_trgm_ops);
CREATE INDEX idx_patients_last_name ON patients USING GIN (last_name gin_trgm_ops);

CREATE TABLE patient_insurance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients (id),
    insurance_provider_id UUID NOT NULL REFERENCES insurance_providers (id),
    policy_number VARCHAR(100) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uq_primary_insurance_per_patient
    ON patient_insurance (patient_id)
    WHERE is_primary = TRUE AND is_deleted = FALSE;
CREATE INDEX idx_patient_insurance_patient_id ON patient_insurance (patient_id);

CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    provenance VARCHAR(255),
    phone VARCHAR(50),
    title_id UUID REFERENCES titles (id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_doctors_title_id ON doctors (title_id);

CREATE TABLE specimen_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(50),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type catalog_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    is_orderable BOOLEAN NOT NULL DEFAULT TRUE,
    category_id UUID REFERENCES categories (id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_catalog_code UNIQUE (code)
);
CREATE INDEX idx_catalog_category_id ON catalog (category_id);
CREATE INDEX idx_catalog_type ON catalog (type);
CREATE INDEX idx_catalog_code ON catalog (code);

CREATE TABLE catalog_specimen_requirements (
    catalog_id UUID NOT NULL REFERENCES catalog (id) ON DELETE CASCADE,
    specimen_type_id UUID NOT NULL REFERENCES specimen_types (id),
    volume_ml NUMERIC(6, 2),
    instructions TEXT,
    PRIMARY KEY (catalog_id, specimen_type_id)
);

CREATE TABLE catalog_panel_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    panel_id UUID NOT NULL REFERENCES catalog (id) ON DELETE CASCADE,
    test_id UUID NOT NULL REFERENCES catalog (id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_panel_test UNIQUE (panel_id, test_id),
    CONSTRAINT chk_panel_not_self CHECK (panel_id <> test_id)
);

CREATE OR REPLACE FUNCTION check_catalog_panel_items()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT type FROM catalog WHERE id = NEW.panel_id) <> 'panel' THEN
        RAISE EXCEPTION 'panel_id must reference a catalog entry of type ''panel''';
    END IF;
    IF (SELECT type FROM catalog WHERE id = NEW.test_id) <> 'item' THEN
        RAISE EXCEPTION 'test_id must reference a catalog entry of type ''item''';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_catalog_panel_items
    BEFORE INSERT OR UPDATE ON catalog_panel_items
    FOR EACH ROW EXECUTE FUNCTION check_catalog_panel_items();

CREATE TABLE analytes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    unit_id UUID REFERENCES units (id),
    data_type data_type NOT NULL,
    options_data JSONB,
    reference_text TEXT,
    is_calculated BOOLEAN NOT NULL DEFAULT FALSE,
    calculation_formula TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_analytes_code UNIQUE (code)
);
CREATE INDEX idx_analytes_code ON analytes (code);
CREATE INDEX idx_analytes_unit_id ON analytes (unit_id);

CREATE TABLE catalog_item_analytes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_item_id UUID NOT NULL REFERENCES catalog (id) ON DELETE CASCADE,
    analyte_id UUID NOT NULL REFERENCES analytes (id),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_catalog_item_analyte UNIQUE (catalog_item_id, analyte_id)
);
CREATE INDEX idx_catalog_item_analytes_catalog ON catalog_item_analytes (catalog_item_id);
CREATE INDEX idx_catalog_item_analytes_analyte ON catalog_item_analytes (analyte_id);

CREATE TABLE validation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analyte_id UUID NOT NULL REFERENCES analytes (id),
    target_gender target_gender_type NOT NULL DEFAULT 'all',
    min_age_years INTEGER,
    max_age_years INTEGER,
    required_context_id UUID REFERENCES patient_contexts (id),
    priority INTEGER NOT NULL DEFAULT 0,
    absurd_min NUMERIC(12, 4),
    absurd_max NUMERIC(12, 4),
    panic_min NUMERIC(12, 4),
    panic_max NUMERIC(12, 4),
    normal_min NUMERIC(12, 4),
    normal_max NUMERIC(12, 4),
    expected_value NUMERIC(12, 4),
    max_delta_percent NUMERIC(6, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_validation_rules_analyte_id ON validation_rules (analyte_id);
CREATE INDEX idx_validation_rules_priority ON validation_rules (analyte_id, priority DESC);

CREATE TABLE consistency_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    formula TEXT NOT NULL,
    formula_description TEXT,
    error_message TEXT NOT NULL,
    severity rule_severity NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE consistency_rule_analytes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES consistency_rules (id) ON DELETE CASCADE,
    analyte_id UUID NOT NULL REFERENCES analytes (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_consistency_rule_analyte UNIQUE (rule_id, analyte_id)
);
CREATE INDEX idx_consistency_rule_analytes_rule ON consistency_rule_analytes (rule_id);
CREATE INDEX idx_consistency_rule_analytes_analyte ON consistency_rule_analytes (analyte_id);

CREATE TABLE reflex_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_analyte_id UUID NOT NULL REFERENCES analytes (id),
    trigger_operator trigger_operator NOT NULL,
    trigger_value VARCHAR(255) NOT NULL,
    action_catalog_id UUID NOT NULL REFERENCES catalog (id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_reflex_rules_trigger_analyte ON reflex_rules (trigger_analyte_id);

CREATE TABLE instruments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    model VARCHAR(255),
    serial_number VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""")

    op.execute("""
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients (id),
    doctor_id UUID NOT NULL REFERENCES doctors (id),
    patient_insurance_id UUID REFERENCES patient_insurance (id),
    status order_status NOT NULL DEFAULT 'registered',
    patient_context_id UUID REFERENCES patient_contexts (id),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES "user" (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_orders_patient_id ON orders (patient_id);
CREATE INDEX idx_orders_doctor_id ON orders (doctor_id);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_created_at ON orders (created_at DESC);

CREATE TABLE order_specimens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    specimen_type_id UUID NOT NULL REFERENCES specimen_types (id),
    collection_time TIMESTAMPTZ,
    collected_by UUID REFERENCES "user" (id),
    status specimen_status NOT NULL DEFAULT 'collected',
    rejection_reason_id UUID REFERENCES rejection_reasons (id),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_order_specimens_order_id ON order_specimens (order_id);
CREATE INDEX idx_order_specimens_status ON order_specimens (status);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    catalog_id UUID NOT NULL REFERENCES catalog (id),
    order_specimen_id UUID REFERENCES order_specimens (id),
    catalog_price NUMERIC(12, 2) NOT NULL,
    price_charged NUMERIC(12, 2) NOT NULL,
    price_override_reason TEXT,
    is_covered_by_insurance BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_reflex_added BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_order_items_order_id ON order_items (order_id);
CREATE INDEX idx_order_items_catalog_id ON order_items (catalog_id);
CREATE INDEX idx_order_items_order_specimen_id ON order_items (order_specimen_id);

CREATE TABLE order_catalog_item_analytes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_item_id UUID NOT NULL REFERENCES order_items (id) ON DELETE CASCADE,
    catalog_item_analyte_id UUID NOT NULL REFERENCES catalog_item_analytes (id),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_order_catalog_item_analyte UNIQUE (order_item_id, catalog_item_analyte_id)
);
CREATE INDEX idx_order_catalog_item_analytes_order_item ON order_catalog_item_analytes (order_item_id);

CREATE TABLE analyte_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_item_id UUID NOT NULL REFERENCES order_items (id) ON DELETE CASCADE,
    analyte_id UUID NOT NULL REFERENCES analytes (id),
    specimen_id UUID NOT NULL REFERENCES order_specimens (id),
    instrument_id UUID REFERENCES instruments (id),
    result_value TEXT,
    validation_rule_id UUID REFERENCES validation_rules (id),
    is_abnormal BOOLEAN NOT NULL DEFAULT FALSE,
    is_critical BOOLEAN NOT NULL DEFAULT FALSE,
    delta_flag BOOLEAN NOT NULL DEFAULT FALSE,
    is_rejected BOOLEAN NOT NULL DEFAULT FALSE,
    rejection_reason TEXT,
    status result_status NOT NULL DEFAULT 'pending',
    resulted_by_id UUID REFERENCES "user" (id),
    resulted_at TIMESTAMPTZ,
    verified_by_id UUID REFERENCES "user" (id),
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_analyte_results_order_item_id ON analyte_results (order_item_id);
CREATE INDEX idx_analyte_results_analyte_id ON analyte_results (analyte_id);
CREATE INDEX idx_analyte_results_specimen_id ON analyte_results (specimen_id);
CREATE INDEX idx_analyte_results_status ON analyte_results (status);
CREATE INDEX idx_analyte_results_is_critical ON analyte_results (is_critical) WHERE is_critical = TRUE;

CREATE TABLE analyte_result_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analyte_result_id UUID NOT NULL REFERENCES analyte_results (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES "user" (id),
    comment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_analyte_result_comments_result_id ON analyte_result_comments (analyte_result_id);

CREATE TABLE critical_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analyte_result_id UUID NOT NULL REFERENCES analyte_results (id),
    notified_by_id UUID NOT NULL REFERENCES "user" (id),
    notified_to_id UUID NOT NULL REFERENCES "user" (id),
    notified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    method critical_method NOT NULL,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_critical_notifications_result_id ON critical_notifications (analyte_result_id);
CREATE INDEX idx_critical_notifications_acknowledged ON critical_notifications (acknowledged) WHERE acknowledged = FALSE;

CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_storage_url TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uq_default_report_template
    ON report_templates (is_default)
    WHERE is_default = TRUE AND is_deleted = FALSE;

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders (id),
    version INTEGER NOT NULL DEFAULT 1,
    report_template_id UUID REFERENCES report_templates (id),
    released_by_id UUID NOT NULL REFERENCES "user" (id),
    released_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel report_channel NOT NULL,
    delivery_status delivery_status NOT NULL DEFAULT 'pending',
    recipient_note TEXT,
    report_storage_url TEXT,
    is_voided BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_reports_order_id ON reports (order_id);
CREATE INDEX idx_reports_is_voided ON reports (is_voided) WHERE is_voided = FALSE;

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders (id),
    patient_id UUID REFERENCES patients (id),
    user_id UUID NOT NULL REFERENCES "user" (id),
    type notification_type NOT NULL,
    channel notification_channel NOT NULL,
    message TEXT NOT NULL,
    status notification_status NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_notifications_user_id ON notifications (user_id);
CREATE INDEX idx_notifications_order_id ON notifications (order_id);
CREATE INDEX idx_notifications_status ON notifications (status);

CREATE TABLE insurance_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurance_provider_id UUID NOT NULL REFERENCES insurance_providers (id),
    catalog_id UUID NOT NULL REFERENCES catalog (id),
    insurance_price NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_insurance_pricing UNIQUE (insurance_provider_id, catalog_id)
);
CREATE INDEX idx_insurance_pricing_provider ON insurance_pricing (insurance_provider_id);
CREATE INDEX idx_insurance_pricing_catalog ON insurance_pricing (catalog_id);

CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders (id),
    version INTEGER NOT NULL DEFAULT 1,
    is_voided BOOLEAN NOT NULL DEFAULT FALSE,
    total_amount NUMERIC(12, 2) NOT NULL,
    discount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    net_amount NUMERIC(12, 2) NOT NULL,
    amount_paid NUMERIC(12, 2) NOT NULL DEFAULT 0,
    payment_status payment_status NOT NULL DEFAULT 'unpaid',
    payment_method_id UUID REFERENCES payment_methods (id),
    created_by_id UUID NOT NULL REFERENCES "user" (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_invoices_order_id ON invoices (order_id);
CREATE INDEX idx_invoices_payment_status ON invoices (payment_status);
CREATE INDEX idx_invoices_is_voided ON invoices (is_voided) WHERE is_voided = FALSE;

CREATE TABLE doctor_commission_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id UUID NOT NULL REFERENCES doctors (id),
    commission_rate NUMERIC(5, 4) NOT NULL,
    insurance_commission_rate NUMERIC(5, 4) NOT NULL,
    effective_from DATE NOT NULL,
    effective_until DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE doctor_commission_configs
    ADD CONSTRAINT no_overlapping_commission_configs
    EXCLUDE USING GIST (
        doctor_id WITH =,
        daterange(effective_from, effective_until, '[)') WITH &&
    );
CREATE INDEX idx_commission_configs_doctor_id ON doctor_commission_configs (doctor_id);

CREATE TABLE doctor_commission_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders (id),
    doctor_id UUID NOT NULL REFERENCES doctors (id),
    order_net_amount NUMERIC(12, 2) NOT NULL,
    rate_applied NUMERIC(5, 4) NOT NULL,
    commission_amount NUMERIC(12, 2) NOT NULL,
    payout_status payout_status NOT NULL DEFAULT 'pending',
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_commission_entry_per_order UNIQUE (order_id, doctor_id)
);
CREATE INDEX idx_commission_entries_doctor_id ON doctor_commission_entries (doctor_id);
CREATE INDEX idx_commission_entries_payout_status ON doctor_commission_entries (payout_status);

CREATE TABLE doctor_commission_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id UUID NOT NULL REFERENCES doctors (id),
    total_commission_amount NUMERIC(12, 2) NOT NULL,
    created_by UUID NOT NULL REFERENCES "user" (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_commission_payments_doctor_id ON doctor_commission_payments (doctor_id);

CREATE TABLE doctor_commission_payment_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commission_payment_id UUID NOT NULL REFERENCES doctor_commission_payments (id) ON DELETE CASCADE,
    commission_entry_id UUID NOT NULL REFERENCES doctor_commission_entries (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_payment_entry UNIQUE (commission_payment_id, commission_entry_id)
);
CREATE INDEX idx_commission_payment_entries_payment_id ON doctor_commission_payment_entries (commission_payment_id);
CREATE INDEX idx_commission_payment_entries_entry_id ON doctor_commission_payment_entries (commission_entry_id);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action audit_action NOT NULL,
    old_values JSONB,
    new_values JSONB,
    performed_by_id UUID REFERENCES "user" (id),
    performed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_logs_table_name ON audit_logs (table_name);
CREATE INDEX idx_audit_logs_record_id ON audit_logs (record_id);
CREATE INDEX idx_audit_logs_performed_by ON audit_logs (performed_by_id);
CREATE INDEX idx_audit_logs_performed_at ON audit_logs (performed_at DESC);
""")


def downgrade():
    op.execute("""
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS doctor_commission_payment_entries;
DROP TABLE IF EXISTS doctor_commission_payments;
DROP TABLE IF EXISTS doctor_commission_entries;
DROP TABLE IF EXISTS doctor_commission_configs;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS insurance_pricing;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS report_templates;
DROP TABLE IF EXISTS critical_notifications;
DROP TABLE IF EXISTS analyte_result_comments;
DROP TABLE IF EXISTS analyte_results;
DROP TABLE IF EXISTS order_catalog_item_analytes;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS order_specimens;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS instruments;
DROP TABLE IF EXISTS reflex_rules;
DROP TABLE IF EXISTS consistency_rule_analytes;
DROP TABLE IF EXISTS consistency_rules;
DROP TABLE IF EXISTS validation_rules;
DROP TABLE IF EXISTS catalog_item_analytes;
DROP TRIGGER IF EXISTS trg_check_catalog_panel_items ON catalog_panel_items;
DROP FUNCTION IF EXISTS check_catalog_panel_items();
DROP TABLE IF EXISTS catalog_panel_items;
DROP TABLE IF EXISTS catalog_specimen_requirements;
DROP TABLE IF EXISTS analytes;
DROP TABLE IF EXISTS catalog;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS specimen_types;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS patient_insurance;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS insurance_providers;
DROP TABLE IF EXISTS rejection_reasons;
DROP TABLE IF EXISTS payment_methods;
DROP TABLE IF EXISTS patient_contexts;
DROP TABLE IF EXISTS units;
DROP TABLE IF EXISTS titles;

DROP TYPE IF EXISTS audit_action;
DROP TYPE IF EXISTS critical_method;
DROP TYPE IF EXISTS notification_status;
DROP TYPE IF EXISTS notification_channel;
DROP TYPE IF EXISTS notification_type;
DROP TYPE IF EXISTS delivery_status;
DROP TYPE IF EXISTS report_channel;
DROP TYPE IF EXISTS payment_status;
DROP TYPE IF EXISTS payout_status;
DROP TYPE IF EXISTS result_status;
DROP TYPE IF EXISTS specimen_status;
DROP TYPE IF EXISTS order_status;
DROP TYPE IF EXISTS rule_severity;
DROP TYPE IF EXISTS trigger_operator;
DROP TYPE IF EXISTS target_gender_type;
DROP TYPE IF EXISTS catalog_type;
DROP TYPE IF EXISTS data_type;
DROP TYPE IF EXISTS gender_type;
""")
