"""Add modern patient and prescriber report details template.

Revision ID: 6d9e2f3a4b65
Revises: 4b8c1d2e3f54
"""

from alembic import op

revision = "6d9e2f3a4b65"
down_revision = "4b8c1d2e3f54"
branch_labels = None
depends_on = None


DETAILS_COMPONENT_ID = "22222222-2222-4222-8222-222222222222"
DETAILS_VERSION_ID = "62222222-2222-4222-8222-222222222222"

DETAILS_HTML = """
<section class="identity-details">
  <div class="identity-panel patient-panel">
    <div class="identity-panel-head">
      <span class="identity-mark">P</span>
      <div>
        <span class="identity-eyebrow">Identification</span>
        <strong>Patient</strong>
      </div>
    </div>
    <div class="identity-name">{{patient.name}}</div>
    <div class="identity-grid">
      <div class="detail-row">
        <span class="detail-label">Identifiant</span>
        <span class="detail-value">{{patient.identifier}}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Date de naissance</span>
        <span class="detail-value">{{patient.date_of_birth}}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Âge</span>
        <span class="detail-value">{{patient.age}} ans</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Sexe</span>
        <span class="detail-value">{{patient.gender_label}}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Contexte</span>
        <span class="detail-value">{{patient.context}}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Téléphone</span>
        <span class="detail-value">{{patient.phone}}</span>
      </div>
      <div class="detail-row detail-row-wide">
        <span class="detail-label">Adresse</span>
        <span class="detail-value">{{patient.address}}</span>
      </div>
    </div>
  </div>

  <div class="identity-panel doctor-panel">
    <div class="identity-panel-head">
      <span class="identity-mark">Rx</span>
      <div>
        <span class="identity-eyebrow">Prescription</span>
        <strong>Médecin prescripteur</strong>
      </div>
    </div>
    <div class="identity-name">
      <span class="optional-value">{{doctor.title}}</span>
      {{doctor.name}}
    </div>
    <div class="identity-grid doctor-grid">
      <div class="detail-row detail-row-wide">
        <span class="detail-label">Établissement / provenance</span>
        <span class="detail-value">{{doctor.provenance}}</span>
      </div>
      <div class="detail-row detail-row-wide">
        <span class="detail-label">Téléphone</span>
        <span class="detail-value">{{doctor.phone}}</span>
      </div>
    </div>
    <div class="doctor-signature">
      <span>Prescripteur enregistré</span>
      <strong>{{doctor.name}}</strong>
    </div>
  </div>
</section>
""".strip()

DETAILS_CSS = """
.identity-details{
  display:grid;
  grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr);
  gap:12px;
  margin:16px 0 20px;
  color:#17324d;
  font-family:Arial,Helvetica,sans-serif
}
.identity-panel{
  position:relative;
  min-height:176px;
  overflow:hidden;
  background:#fff;
  border:1px solid #dce6eb;
  border-radius:3px;
  padding:15px 16px 14px
}
.identity-panel:before{
  position:absolute;
  top:0;
  right:0;
  left:0;
  height:4px;
  content:""
}
.patient-panel:before{background:#087f76}
.doctor-panel:before{background:#f28c28}
.identity-panel-head{
  display:flex;
  align-items:center;
  gap:10px;
  padding-bottom:10px;
  border-bottom:1px solid #e6edf1
}
.identity-mark{
  display:flex;
  width:32px;
  height:32px;
  flex:0 0 32px;
  align-items:center;
  justify-content:center;
  color:#fff;
  background:#087f76;
  border-radius:50%;
  font-size:11px;
  font-weight:800;
  letter-spacing:.02em
}
.doctor-panel .identity-mark{background:#f28c28}
.identity-panel-head div{display:flex;flex-direction:column}
.identity-eyebrow{
  color:#7a8a9a;
  font-size:7px;
  font-weight:700;
  letter-spacing:.14em;
  line-height:1.2;
  text-transform:uppercase
}
.identity-panel-head strong{
  margin-top:2px;
  color:#17324d;
  font-size:10px;
  line-height:1.2
}
.identity-name{
  min-height:18px;
  margin:11px 0 10px;
  color:#087f76;
  font-size:15px;
  font-weight:800;
  line-height:1.2
}
.doctor-panel .identity-name{color:#c96c13}
.optional-value:empty{display:none}
.optional-value:not(:empty):after{content:" "}
.identity-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:7px 15px
}
.doctor-grid{grid-template-columns:1fr}
.detail-row{
  display:flex;
  min-width:0;
  flex-direction:column;
  gap:2px
}
.detail-row-wide{grid-column:1/-1}
.detail-row:has(.detail-value:empty){display:none}
.detail-label{
  color:#81909f;
  font-size:7px;
  font-weight:700;
  letter-spacing:.08em;
  text-transform:uppercase
}
.detail-value{
  overflow-wrap:anywhere;
  color:#263b50;
  font-size:9px;
  font-weight:600;
  line-height:1.3
}
.doctor-signature{
  position:absolute;
  right:16px;
  bottom:14px;
  left:16px;
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:12px;
  padding-top:9px;
  color:#81909f;
  border-top:1px dashed #d8e1e7;
  font-size:7px
}
.doctor-signature strong{
  color:#526579;
  font-size:8px;
  font-weight:700
}
@media print{
  .identity-details{break-inside:avoid}
  .identity-panel{box-shadow:none}
}
""".strip()


def upgrade() -> None:
    escaped_html = DETAILS_HTML.replace("'", "''")
    escaped_css = DETAILS_CSS.replace("'", "''").replace("%", "%%")
    op.get_bind().exec_driver_sql(
        f"""
        UPDATE report_component_versions
        SET status = 'archived', updated_at = NOW()
        WHERE component_id = '{DETAILS_COMPONENT_ID}'
          AND status = 'published'
          AND NOT EXISTS (
              SELECT 1 FROM report_component_versions
              WHERE id = '{DETAILS_VERSION_ID}'
          );

        INSERT INTO report_component_versions
            (id, component_id, version, status, html_source, css_source, published_at)
        SELECT
            '{DETAILS_VERSION_ID}',
            '{DETAILS_COMPONENT_ID}',
            COALESCE(MAX(version), 0) + 1,
            'published',
            '{escaped_html}',
            '{escaped_css}',
            NOW()
        FROM report_component_versions
        WHERE component_id = '{DETAILS_COMPONENT_ID}'
        HAVING EXISTS (
            SELECT 1 FROM report_components
            WHERE id = '{DETAILS_COMPONENT_ID}'
        )
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.get_bind().exec_driver_sql(
        f"""
        DELETE FROM report_component_versions
        WHERE id = '{DETAILS_VERSION_ID}';

        UPDATE report_component_versions
        SET status = 'published', updated_at = NOW()
        WHERE id = '52222222-2222-4222-8222-222222222222'
          AND NOT EXISTS (
              SELECT 1 FROM report_component_versions
              WHERE component_id = '{DETAILS_COMPONENT_ID}'
                AND status = 'published'
          );
        """
    )
