"""Split doctor commissions by insurance coverage and add finance settings.

Revision ID: d4f7a2c9e610
Revises: b52e8f9d3a01
"""

from alembic import op

revision = "d4f7a2c9e610"
down_revision = "b52e8f9d3a01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE discount_allocation_policy AS ENUM (
            'proportional', 'non_insured_first', 'insured_first'
        )
        """
    )
    op.execute(
        """
        CREATE TABLE finance_settings (
            id INTEGER PRIMARY KEY,
            discount_allocation_policy discount_allocation_policy NOT NULL
                DEFAULT 'non_insured_first',
            updated_by_id UUID REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_finance_settings_singleton CHECK (id = 1)
        )
        """
    )
    op.execute(
        """
        INSERT INTO finance_settings (id, discount_allocation_policy)
        VALUES (1, 'non_insured_first')
        """
    )
    op.execute(
        """
        ALTER TABLE doctor_commission_entries
            ADD COLUMN insured_net_amount NUMERIC(12, 2),
            ADD COLUMN insured_rate_applied NUMERIC(5, 4),
            ADD COLUMN insured_commission_amount NUMERIC(12, 2),
            ADD COLUMN non_insured_net_amount NUMERIC(12, 2),
            ADD COLUMN non_insured_rate_applied NUMERIC(5, 4),
            ADD COLUMN non_insured_commission_amount NUMERIC(12, 2),
            ADD COLUMN discount_allocation_policy discount_allocation_policy
        """
    )
    op.execute(
        """
        WITH entry_values AS (
            SELECT
                dce.id,
                i.net_amount,
                i.discount,
                COALESCE(
                    SUM(il.amount) FILTER (
                        WHERE il.is_covered_by_insurance
                    ),
                    0
                )::numeric(12, 2) AS insured_gross,
                COALESCE(
                    SUM(il.amount) FILTER (
                        WHERE NOT il.is_covered_by_insurance
                    ),
                    0
                )::numeric(12, 2) AS non_insured_gross,
                COALESCE(
                    config.insurance_commission_rate,
                    dce.rate_applied
                ) AS insured_rate,
                COALESCE(
                    config.commission_rate,
                    dce.rate_applied
                ) AS non_insured_rate
            FROM doctor_commission_entries dce
            JOIN orders o ON o.id = dce.order_id
            JOIN invoices i
                ON i.order_id = o.id
                AND NOT i.is_voided
            LEFT JOIN invoice_lines il ON il.invoice_id = i.id
            LEFT JOIN LATERAL (
                SELECT
                    dcc.commission_rate,
                    dcc.insurance_commission_rate
                FROM doctor_commission_configs dcc
                WHERE dcc.doctor_id = dce.doctor_id
                  AND dcc.effective_from <= o.created_at::date
                  AND (
                      dcc.effective_until IS NULL
                      OR dcc.effective_until >= o.created_at::date
                  )
                ORDER BY dcc.effective_from DESC
                LIMIT 1
            ) config ON TRUE
            GROUP BY
                dce.id,
                i.net_amount,
                i.discount,
                config.insurance_commission_rate,
                config.commission_rate
        ),
        split_values AS (
            SELECT
                id,
                net_amount,
                GREATEST(
                    insured_gross - GREATEST(discount - non_insured_gross, 0),
                    0
                )::numeric(12, 2) AS insured_net,
                insured_rate,
                non_insured_rate
            FROM entry_values
        ),
        calculated AS (
            SELECT
                id,
                net_amount,
                insured_net,
                (net_amount - insured_net)::numeric(12, 2) AS non_insured_net,
                insured_rate,
                non_insured_rate
            FROM split_values
        )
        UPDATE doctor_commission_entries target
        SET
            order_net_amount = calculated.net_amount,
            insured_net_amount = calculated.insured_net,
            insured_rate_applied = calculated.insured_rate,
            insured_commission_amount = ROUND(
                calculated.insured_net * calculated.insured_rate,
                2
            ),
            non_insured_net_amount = calculated.non_insured_net,
            non_insured_rate_applied = calculated.non_insured_rate,
            non_insured_commission_amount = ROUND(
                calculated.non_insured_net * calculated.non_insured_rate,
                2
            ),
            discount_allocation_policy = 'non_insured_first',
            commission_amount = ROUND(
                calculated.insured_net * calculated.insured_rate,
                2
            ) + ROUND(
                calculated.non_insured_net * calculated.non_insured_rate,
                2
            )
        FROM calculated
        WHERE target.id = calculated.id
        """
    )
    op.execute(
        """
        ALTER TABLE doctor_commission_entries
            ALTER COLUMN insured_net_amount SET NOT NULL,
            ALTER COLUMN insured_rate_applied SET NOT NULL,
            ALTER COLUMN insured_commission_amount SET NOT NULL,
            ALTER COLUMN non_insured_net_amount SET NOT NULL,
            ALTER COLUMN non_insured_rate_applied SET NOT NULL,
            ALTER COLUMN non_insured_commission_amount SET NOT NULL,
            ALTER COLUMN discount_allocation_policy SET NOT NULL,
            DROP COLUMN rate_applied
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE doctor_commission_entries "
        "ADD COLUMN rate_applied NUMERIC(5, 4)"
    )
    op.execute(
        """
        UPDATE doctor_commission_entries
        SET rate_applied = CASE
            WHEN order_net_amount > 0
                THEN ROUND(commission_amount / order_net_amount, 4)
            ELSE 0
        END
        """
    )
    op.execute(
        """
        ALTER TABLE doctor_commission_entries
            ALTER COLUMN rate_applied SET NOT NULL,
            DROP COLUMN insured_net_amount,
            DROP COLUMN insured_rate_applied,
            DROP COLUMN insured_commission_amount,
            DROP COLUMN non_insured_net_amount,
            DROP COLUMN non_insured_rate_applied,
            DROP COLUMN non_insured_commission_amount,
            DROP COLUMN discount_allocation_policy
        """
    )
    op.execute("DROP TABLE finance_settings")
    op.execute("DROP TYPE discount_allocation_policy")
