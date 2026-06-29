"""Add reagent inventory module.

Revision ID: 9b2c3d4e5f61
Revises: 8f1a4b5c6d87
"""

from alembic import op

revision = "9b2c3d4e5f61"
down_revision = "8f1a4b5c6d87"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE reagent_lot_status AS ENUM ('active', 'depleted', 'disposed');
        CREATE TYPE reagent_movement_type AS ENUM ('received', 'used', 'adjusted', 'disposed');

        CREATE TABLE reagent_settings (
            id INTEGER PRIMARY KEY,
            default_expiry_warning_days INTEGER NOT NULL DEFAULT 30,
            expiry_alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            low_stock_alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            updated_by_id UUID REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_reagent_settings_singleton CHECK (id = 1),
            CONSTRAINT ck_reagent_settings_expiry_days
                CHECK (default_expiry_warning_days BETWEEN 1 AND 3650)
        );

        INSERT INTO reagent_settings (id) VALUES (1);

        CREATE TABLE reagents (
            id UUID PRIMARY KEY,
            code VARCHAR(50) NOT NULL,
            name VARCHAR(255) NOT NULL,
            unit_label VARCHAR(50) NOT NULL,
            storage_condition VARCHAR(255),
            storage_location VARCHAR(255),
            supplier VARCHAR(255),
            notes TEXT,
            minimum_stock_level NUMERIC(12, 3),
            expiry_warning_days_override INTEGER,
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_reagents_code UNIQUE (code),
            CONSTRAINT ck_reagents_minimum_stock_nonnegative
                CHECK (minimum_stock_level IS NULL OR minimum_stock_level >= 0),
            CONSTRAINT ck_reagents_expiry_override
                CHECK (
                    expiry_warning_days_override IS NULL
                    OR expiry_warning_days_override BETWEEN 1 AND 3650
                )
        );

        CREATE TABLE reagent_lots (
            id UUID PRIMARY KEY,
            reagent_id UUID NOT NULL REFERENCES reagents(id),
            lot_number VARCHAR(100) NOT NULL,
            expiry_date DATE NOT NULL,
            received_date DATE NOT NULL,
            initial_quantity NUMERIC(12, 3) NOT NULL,
            current_quantity NUMERIC(12, 3) NOT NULL,
            unit_cost NUMERIC(12, 2),
            supplier_name VARCHAR(255),
            location VARCHAR(255),
            notes TEXT,
            status reagent_lot_status NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_reagent_lots_reagent_lot UNIQUE (reagent_id, lot_number),
            CONSTRAINT ck_reagent_lots_initial_positive CHECK (initial_quantity > 0),
            CONSTRAINT ck_reagent_lots_current_nonnegative CHECK (current_quantity >= 0)
        );

        CREATE TABLE reagent_stock_movements (
            id UUID PRIMARY KEY,
            reagent_id UUID NOT NULL REFERENCES reagents(id),
            lot_id UUID NOT NULL REFERENCES reagent_lots(id),
            movement_type reagent_movement_type NOT NULL,
            quantity NUMERIC(12, 3) NOT NULL,
            balance_after NUMERIC(12, 3) NOT NULL,
            reason VARCHAR(255) NOT NULL,
            notes TEXT,
            performed_by_id UUID NOT NULL REFERENCES "user"(id),
            performed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_reagent_movements_quantity_positive CHECK (quantity > 0),
            CONSTRAINT ck_reagent_movements_balance_nonnegative CHECK (balance_after >= 0)
        );

        CREATE INDEX idx_reagents_deleted ON reagents (is_deleted);
        CREATE INDEX idx_reagent_lots_reagent_id ON reagent_lots (reagent_id);
        CREATE INDEX idx_reagent_lots_expiry_date ON reagent_lots (expiry_date);
        CREATE INDEX idx_reagent_lots_status ON reagent_lots (status);
        CREATE INDEX idx_reagent_movements_reagent_id ON reagent_stock_movements (reagent_id);
        CREATE INDEX idx_reagent_movements_lot_id ON reagent_stock_movements (lot_id);
        CREATE INDEX idx_reagent_movements_performed_at ON reagent_stock_movements (performed_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE reagent_stock_movements;
        DROP TABLE reagent_lots;
        DROP TABLE reagents;
        DROP TABLE reagent_settings;
        DROP TYPE reagent_movement_type;
        DROP TYPE reagent_lot_status;
        """
    )
