"""Add global laboratory settings.

Revision ID: 2f6a9b0c1d32
Revises: 1e5f8a9b0c21
"""

from alembic import op

revision = "2f6a9b0c1d32"
down_revision = "1e5f8a9b0c21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE lab_settings (
            id INTEGER PRIMARY KEY,
            display_name VARCHAR(255) NOT NULL DEFAULT 'KENEYA LAB',
            legal_name VARCHAR(255),
            slogan VARCHAR(255),
            logo_object_key VARCHAR(500),
            address TEXT,
            city VARCHAR(120),
            postal_code VARCHAR(30),
            country VARCHAR(120),
            primary_phone VARCHAR(50),
            secondary_phone VARCHAR(50),
            email VARCHAR(255),
            website VARCHAR(255),
            registration_number VARCHAR(100),
            laboratory_license VARCHAR(100),
            tax_id VARCHAR(100),
            bank_name VARCHAR(255),
            bank_account_holder VARCHAR(255),
            bank_account_number VARCHAR(120),
            payment_instructions TEXT,
            director_name VARCHAR(255),
            director_title VARCHAR(255),
            document_footer TEXT,
            updated_by_id UUID REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_lab_settings_singleton CHECK (id = 1)
        )
        """
    )
    op.execute(
        "INSERT INTO lab_settings (id, display_name) VALUES (1, 'KENEYA LAB')"
    )


def downgrade() -> None:
    op.execute("DROP TABLE lab_settings")
