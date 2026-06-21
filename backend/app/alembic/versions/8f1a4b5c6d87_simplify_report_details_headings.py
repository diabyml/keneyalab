"""Simplify default report patient and doctor headings.

Revision ID: 8f1a4b5c6d87
Revises: 7e0f3a4b5c76
"""

from alembic import op

revision = "8f1a4b5c6d87"
down_revision = "7e0f3a4b5c76"
branch_labels = None
depends_on = None


COMPONENT_ID = "22222222-2222-4222-8222-222222222222"
VERSION_ID = "82222222-2222-4222-8222-222222222222"
PREVIOUS_VERSION_ID = "72222222-2222-4222-8222-222222222222"

HTML = """
<section class="compact-details">
  <div class="compact-card patient-card">
    <div class="card-title">Patient</div>
    <div class="compact-fields">
      <div class="compact-field">
        <span class="field-label">Nom et prénom</span>
        <strong class="field-value">{{patient.name}}</strong>
      </div>
      <div class="compact-field">
        <span class="field-label">Identifiant</span>
        <strong class="field-value">{{patient.identifier}}</strong>
      </div>
      <div class="compact-field">
        <span class="field-label">Né(e) le</span>
        <span class="field-value">{{patient.date_of_birth}} · {{patient.age}} ans</span>
      </div>
      <div class="compact-field">
        <span class="field-label">Sexe / contexte</span>
        <span class="field-value">{{patient.gender_label}} · {{patient.context}}</span>
      </div>
      <div class="compact-field">
        <span class="field-label">Téléphone</span>
        <span class="field-value">{{patient.phone}}</span>
      </div>
      <div class="compact-field">
        <span class="field-label">Adresse</span>
        <span class="field-value">{{patient.address}}</span>
      </div>
    </div>
  </div>

  <div class="compact-card doctor-card">
    <div class="card-title">Médecin prescripteur</div>
    <div class="compact-fields">
      <div class="compact-field compact-field-wide">
        <span class="field-label">Nom et prénom</span>
        <strong class="field-value">
          <span class="optional-value">{{doctor.title}}</span>{{doctor.name}}
        </strong>
      </div>
      <div class="compact-field">
        <span class="field-label">Téléphone</span>
        <span class="field-value">{{doctor.phone}}</span>
      </div>
      <div class="compact-field">
        <span class="field-label">Provenance</span>
        <span class="field-value">{{doctor.provenance}}</span>
      </div>
    </div>
  </div>
</section>
""".strip()

CSS = """
.compact-details{
  display:grid;
  grid-template-columns:1.1fr .9fr;
  gap:10px;
  margin:10px 0 14px;
  color:#000;
  font-family:Arial,Helvetica,sans-serif
}
.compact-card{
  position:relative;
  padding:8px 11px 10px;
  background:#fff;
  border:1px solid #374151;
  border-radius:5px
}
.compact-card:before{
  position:absolute;
  top:-1px;
  right:11px;
  left:11px;
  height:2px;
  content:"";
  background:#087f76
}
.doctor-card:before{background:#f28c28}
.card-title{
  margin-bottom:6px;
  padding:2px 0 5px;
  color:#000;
  border-bottom:1px solid #374151;
  font-size:9px;
  font-weight:800;
  letter-spacing:.08em;
  line-height:1.2;
  text-transform:uppercase
}
.compact-fields{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:6px 13px
}
.compact-field{
  display:flex;
  min-width:0;
  flex-direction:column;
  gap:1px
}
.compact-field-wide{grid-column:1/-1}
.compact-field:has(.field-value:empty){display:none}
.field-label{
  color:#000;
  font-size:7px;
  font-weight:700;
  letter-spacing:.06em;
  line-height:1.2;
  text-transform:uppercase
}
.field-value{
  overflow-wrap:anywhere;
  color:#000;
  font-size:9px;
  font-weight:600;
  line-height:1.25
}
strong.field-value{font-weight:800}
.optional-value:empty{display:none}
.optional-value:not(:empty):after{content:" "}
@media print{
  .compact-details{break-inside:avoid}
}
""".strip()


def upgrade() -> None:
    html = HTML.replace("'", "''")
    css = CSS.replace("'", "''").replace("%", "%%")
    op.get_bind().exec_driver_sql(
        f"""
        UPDATE report_component_versions
        SET status = 'archived', updated_at = NOW()
        WHERE component_id = '{COMPONENT_ID}'
          AND status = 'published'
          AND NOT EXISTS (
              SELECT 1 FROM report_component_versions WHERE id = '{VERSION_ID}'
          );

        INSERT INTO report_component_versions
            (id, component_id, version, status, html_source, css_source, published_at)
        SELECT
            '{VERSION_ID}', '{COMPONENT_ID}', COALESCE(MAX(version), 0) + 1,
            'published', '{html}', '{css}', NOW()
        FROM report_component_versions
        WHERE component_id = '{COMPONENT_ID}'
        HAVING EXISTS (
            SELECT 1 FROM report_components WHERE id = '{COMPONENT_ID}'
        )
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.get_bind().exec_driver_sql(
        f"""
        DELETE FROM report_component_versions WHERE id = '{VERSION_ID}';
        UPDATE report_component_versions
        SET status = 'published', updated_at = NOW()
        WHERE id = '{PREVIOUS_VERSION_ID}'
          AND NOT EXISTS (
              SELECT 1 FROM report_component_versions
              WHERE component_id = '{COMPONENT_ID}' AND status = 'published'
          );
        """
    )
