"""Expand the immutable audit log system.

Revision ID: 3a7b0c1d2e43
Revises: 2f6a9b0c1d32
"""

from alembic import op

revision = "3a7b0c1d2e43"
down_revision = "2f6a9b0c1d32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'login_success'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'login_failed'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'password_recovery'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'password_reset'")
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE audit_category AS ENUM (
                'clinical', 'workflow', 'finance',
                'configuration', 'security', 'system'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        ALTER TABLE audit_logs
            ALTER COLUMN record_id DROP NOT NULL,
            ADD COLUMN category audit_category NOT NULL DEFAULT 'system',
            ADD COLUMN record_label VARCHAR(255),
            ADD COLUMN metadata JSONB,
            ADD COLUMN actor_name VARCHAR(255),
            ADD COLUMN actor_email VARCHAR(255),
            ADD COLUMN request_id VARCHAR(100),
            ADD COLUMN correlation_id VARCHAR(100),
            ADD COLUMN source VARCHAR(30) NOT NULL DEFAULT 'system',
            ADD COLUMN ip_address VARCHAR(64),
            ADD COLUMN user_agent VARCHAR(500),
            ADD COLUMN http_method VARCHAR(10),
            ADD COLUMN http_path VARCHAR(500)
        """
    )
    op.execute(
        """
        ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_performed_by_id_fkey;
        ALTER TABLE audit_logs
            ADD CONSTRAINT audit_logs_performed_by_id_fkey
            FOREIGN KEY (performed_by_id) REFERENCES "user" (id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        UPDATE audit_logs
        SET category = CASE
                WHEN table_name IN (
                    'user', 'users', 'permissions', 'roles',
                    'role_permissions', 'user_roles', 'authentication'
                ) THEN 'security'::audit_category
                WHEN table_name IN (
                    'finance_settings', 'insurance_pricing', 'invoices',
                    'invoice_lines', 'payment_transactions', 'payment_refunds',
                    'invoice_balance_transfers', 'customer_credits',
                    'doctor_commission_configs', 'doctor_commission_entries',
                    'doctor_commission_adjustments',
                    'doctor_commission_payments',
                    'doctor_commission_payment_entries'
                ) THEN 'finance'::audit_category
                WHEN table_name IN (
                    'titles', 'units', 'patient_contexts', 'payment_methods',
                    'rejection_reasons', 'specimen_types', 'categories',
                    'insurance_providers', 'catalog',
                    'catalog_specimen_requirements', 'catalog_panel_items',
                    'analytes', 'catalog_item_analytes', 'validation_rules',
                    'consistency_rules', 'consistency_rule_analytes',
                    'reflex_rules', 'instruments', 'report_templates',
                    'lab_settings'
                ) THEN 'configuration'::audit_category
                WHEN table_name IN (
                    'orders', 'order_revisions', 'order_specimens',
                    'order_items', 'order_item_specimens',
                    'order_catalog_item_analytes', 'analyte_results',
                    'analyte_result_comments', 'critical_notifications',
                    'reports', 'notifications'
                ) THEN 'workflow'::audit_category
                WHEN table_name IN ('patients', 'patient_insurance', 'doctors')
                    THEN 'clinical'::audit_category
                ELSE 'system'::audit_category
            END
        """
    )
    op.execute(
        """
        UPDATE audit_logs AS audit
        SET
            actor_name = COALESCE(audit.actor_name, usr.full_name),
            actor_email = COALESCE(audit.actor_email, usr.email)
        FROM "user" AS usr
        WHERE audit.performed_by_id = usr.id
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_category_action
            ON audit_logs (category, action);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_time
            ON audit_logs (table_name, performed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_time
            ON audit_logs (performed_by_id, performed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_record_time
            ON audit_logs (record_id, performed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id
            ON audit_logs (request_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_correlation_id
            ON audit_logs (correlation_id);
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Les entrées du journal d''audit sont immuables';
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs;
        CREATE TRIGGER audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation()")
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_correlation_id")
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_request_id")
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_record_time")
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_actor_time")
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_entity_time")
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_category_action")
    op.execute(
        """
        ALTER TABLE audit_logs
            DROP COLUMN IF EXISTS http_path,
            DROP COLUMN IF EXISTS http_method,
            DROP COLUMN IF EXISTS user_agent,
            DROP COLUMN IF EXISTS ip_address,
            DROP COLUMN IF EXISTS source,
            DROP COLUMN IF EXISTS correlation_id,
            DROP COLUMN IF EXISTS request_id,
            DROP COLUMN IF EXISTS actor_email,
            DROP COLUMN IF EXISTS actor_name,
            DROP COLUMN IF EXISTS metadata,
            DROP COLUMN IF EXISTS record_label,
            DROP COLUMN IF EXISTS category
        """
    )
    op.execute("DROP TYPE IF EXISTS audit_category")
