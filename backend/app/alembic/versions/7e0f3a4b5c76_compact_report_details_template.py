"""Publish compact patient and prescriber report details.

Revision ID: 7e0f3a4b5c76
Revises: 6d9e2f3a4b65
"""

from alembic import op

revision = "7e0f3a4b5c76"
down_revision = "6d9e2f3a4b65"
branch_labels = None
depends_on = None


COMPONENT_ID = "22222222-2222-4222-8222-222222222222"
VERSION_ID = "72222222-2222-4222-8222-222222222222"

HTML = """
<section class="compact-details">
  <div class="compact-card doctor-card">
    <div class="card-title">
      <span class="card-icon">+</span>
      <strong>Médecin</strong>
    </div>
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

  <div class="compact-card patient-card">
    <div class="card-title">
      <span class="card-icon">P</span>
      <strong>Patient</strong>
    </div>
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
</section>
""".strip()

CSS = """
.compact-details{
  display:grid;
  grid-template-columns:.9fr 1.1fr;
  gap:10px;
  margin:12px 0 16px;
  color:#17324d;
  font-family:Arial,Helvetica,sans-serif
}
.compact-card{
  position:relative;
  padding:10px 12px 11px;
  background:#fff;
  border:1px solid #9aabba;
  border-radius:8px;
  box-shadow:0 3px 8px rgba(23,50,77,.08)
}
.compact-card:before{
  position:absolute;
  top:-1px;
  right:14px;
  left:14px;
  height:2px;
  content:"";
  background:#087f76
}
.doctor-card:before{background:#f28c28}
.card-title{
  display:flex;
  align-items:center;
  gap:7px;
  margin-bottom:8px;
  color:#102a43;
  font-size:10px
}
.card-icon{
  display:flex;
  width:18px;
  height:18px;
  align-items:center;
  justify-content:center;
  color:#087f76;
  border:1px solid #087f76;
  border-radius:50%;
  font-size:8px;
  font-weight:800
}
.doctor-card .card-icon{
  color:#c96c13;
  border-color:#f28c28
}
.compact-fields{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:7px 14px
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
  color:#7b8996;
  font-size:7px;
  font-weight:700;
  letter-spacing:.08em;
  line-height:1.2;
  text-transform:uppercase
}
.field-value{
  overflow-wrap:anywhere;
  color:#172033;
  font-size:9px;
  font-weight:600;
  line-height:1.3
}
strong.field-value{font-weight:800}
.optional-value:empty{display:none}
.optional-value:not(:empty):after{content:" "}
@media print{
  .compact-details{break-inside:avoid}
  .compact-card{box-shadow:none}
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
        WHERE id = '62222222-2222-4222-8222-222222222222'
          AND NOT EXISTS (
              SELECT 1 FROM report_component_versions
              WHERE component_id = '{COMPONENT_ID}' AND status = 'published'
          );
        """
    )
