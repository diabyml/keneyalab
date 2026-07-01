"""Add versioned report designer and immutable report snapshots.

Revision ID: 4b8c1d2e3f54
Revises: 3a7b0c1d2e43
"""

from alembic import op

revision = "4b8c1d2e3f54"
down_revision = "3a7b0c1d2e43"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE report_component_type AS ENUM (
                'header', 'patient_doctor_details', 'footer'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        DO $$ BEGIN
            CREATE TYPE report_template_version_status AS ENUM (
                'draft', 'published', 'archived'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        CREATE TABLE report_components (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            component_type report_component_type NOT NULL,
            is_archived BOOLEAN NOT NULL DEFAULT FALSE,
            created_by_id UUID REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE report_component_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            component_id UUID NOT NULL REFERENCES report_components(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            status report_template_version_status NOT NULL DEFAULT 'draft',
            html_source TEXT NOT NULL DEFAULT '',
            css_source TEXT NOT NULL DEFAULT '',
            created_by_id UUID REFERENCES "user"(id),
            published_by_id UUID REFERENCES "user"(id),
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_report_component_version UNIQUE(component_id, version)
        );
        CREATE UNIQUE INDEX uq_report_component_draft
            ON report_component_versions(component_id)
            WHERE status = 'draft';

        CREATE TABLE report_renderers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
            is_archived BOOLEAN NOT NULL DEFAULT FALSE,
            created_by_id UUID REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE report_renderer_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            renderer_id UUID NOT NULL REFERENCES report_renderers(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            status report_template_version_status NOT NULL DEFAULT 'draft',
            jsx_source TEXT NOT NULL DEFAULT '',
            css_source TEXT NOT NULL DEFAULT '',
            created_by_id UUID REFERENCES "user"(id),
            published_by_id UUID REFERENCES "user"(id),
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_report_renderer_version UNIQUE(renderer_id, version)
        );
        CREATE UNIQUE INDEX uq_report_renderer_draft
            ON report_renderer_versions(renderer_id)
            WHERE status = 'draft';

        ALTER TABLE categories
            ADD COLUMN report_renderer_id UUID REFERENCES report_renderers(id);

        CREATE TABLE report_settings (
            id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            default_header_id UUID REFERENCES report_components(id),
            default_details_id UUID REFERENCES report_components(id),
            default_footer_id UUID REFERENCES report_components(id),
            default_renderer_id UUID REFERENCES report_renderers(id),
            updated_by_id UUID REFERENCES "user"(id),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        ALTER TABLE reports
            ADD COLUMN snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN template_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN delivery_metadata JSONB NOT NULL DEFAULT '{}'::jsonb;
        CREATE UNIQUE INDEX uq_report_order_version
            ON reports(order_id, version);

        INSERT INTO report_components
            (id, name, description, component_type)
        VALUES
            ('11111111-1111-4111-8111-111111111111', 'En-tête par défaut',
             'Identité et coordonnées du laboratoire', 'header'),
            ('22222222-2222-4222-8222-222222222222', 'Patient et prescripteur',
             'Identification de la demande, du patient et du médecin', 'patient_doctor_details'),
            ('33333333-3333-4333-8333-333333333333', 'Pied de page par défaut',
             'Mention de validation et pagination', 'footer')
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO report_component_versions
            (id, component_id, version, status, html_source, css_source, published_at)
        VALUES
            ('51111111-1111-4111-8111-111111111111',
             '11111111-1111-4111-8111-111111111111', 1, 'published',
             '<div class="report-header"><div><strong>{{lab.display_name}}</strong><p>{{lab.address}}</p></div><div class="report-title">COMPTE RENDU D''ANALYSES</div></div>',
             '.report-header{display:flex;justify-content:space-between;gap:24px;border-bottom:2px solid #0f766e;padding-bottom:14px}.report-header strong{font-size:22px;color:#0f766e}.report-header p{margin:4px 0 0;color:#64748b}.report-title{font-size:13px;font-weight:700;letter-spacing:.12em}', NOW()),
            ('52222222-2222-4222-8222-222222222222',
             '22222222-2222-4222-8222-222222222222', 1, 'published',
             '<div class="report-details"><div><span>Patient</span><strong>{{patient.name}}</strong><small>{{patient.identifier}} · Né(e) le {{patient.date_of_birth}}</small></div><div><span>Demande</span><strong>{{order.accession_number}}</strong><small>Prescripteur : {{doctor.name}}</small></div></div>',
             '.report-details{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0;padding:14px;background:#f8fafc;border:1px solid #e2e8f0}.report-details span,.report-details small{display:block;color:#64748b}.report-details strong{display:block;margin:3px 0}', NOW()),
            ('53333333-3333-4333-8333-333333333333',
             '33333333-3333-4333-8333-333333333333', 1, 'published',
             '<div class="report-footer"><span>Résultats validés électroniquement</span><span>{{lab.display_name}}</span></div>',
             '.report-footer{display:flex;justify-content:space-between;border-top:1px solid #cbd5e1;padding-top:10px;color:#64748b;font-size:10px}', NOW())
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO report_renderers
            (id, name, description, is_builtin)
        VALUES
            ('44444444-4444-4444-8444-444444444444', 'Tableau clinique',
             'Rendu clinique standard groupé par examens', TRUE)
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO report_renderer_versions
            (id, renderer_id, version, status, jsx_source, css_source, published_at)
        VALUES
            ('54444444-4444-4444-8444-444444444444',
             '44444444-4444-4444-8444-444444444444', 1, 'published',
             'function Renderer({ category, ReportKit }) { return <ReportKit.ClinicalTable category={category} /> }',
             '.report-category{margin:18px 0}.report-category h2{font-size:14px;color:#0f766e;border-bottom:1px solid #cbd5e1;padding-bottom:6px}.clinical-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:11px}.clinical-table th,.clinical-table td{padding:7px 6px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}.clinical-table th{color:#475569;font-weight:600}.clinical-table th:nth-child(1),.clinical-table td:nth-child(1){width:24%}.clinical-table th:nth-child(2),.clinical-table td:nth-child(2){width:14%}.clinical-table th:nth-child(3),.clinical-table td:nth-child(3){width:10%}.clinical-table th:nth-child(4),.clinical-table td:nth-child(4){width:52%}.clinical-table td{overflow-wrap:anywhere}.clinical-table .report-test-heading th{width:auto}.result-abnormal{font-weight:700;color:#b45309}.result-critical{font-weight:800;color:#b91c1c}',
             NOW())
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO report_settings
            (id, default_header_id, default_details_id, default_footer_id, default_renderer_id)
        VALUES
            (1,
             '11111111-1111-4111-8111-111111111111',
             '22222222-2222-4222-8222-222222222222',
             '33333333-3333-4333-8333-333333333333',
             '44444444-4444-4444-8444-444444444444')
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE reports
            DROP COLUMN IF EXISTS delivery_metadata,
            DROP COLUMN IF EXISTS template_snapshot,
            DROP COLUMN IF EXISTS snapshot;
        DROP INDEX IF EXISTS uq_report_order_version;
        DROP TABLE IF EXISTS report_settings;
        ALTER TABLE categories DROP COLUMN IF EXISTS report_renderer_id;
        DROP TABLE IF EXISTS report_renderer_versions;
        DROP TABLE IF EXISTS report_renderers;
        DROP TABLE IF EXISTS report_component_versions;
        DROP TABLE IF EXISTS report_components;
        DROP TYPE IF EXISTS report_template_version_status;
        DROP TYPE IF EXISTS report_component_type;
        """
    )
