"""Publish modern default report header.

Revision ID: b8e2c4d6f910
Revises: a7c9d2e4f631
"""

from alembic import op

revision = "b8e2c4d6f910"
down_revision = "a7c9d2e4f631"
branch_labels = None
depends_on = None


COMPONENT_ID = "11111111-1111-4111-8111-111111111111"
VERSION_ID = "81111111-1111-4111-8111-111111111111"
PREVIOUS_VERSION_ID = "51111111-1111-4111-8111-111111111111"

HTML = """
<header class="modern-report-header">
  <div class="lab-identity">
    <div class="lab-logo-box">
      <span class="lab-logo-fallback">KL</span>
      <img class="lab-logo-image" src="{{lab.logo_url}}" alt="Logo du laboratoire">
    </div>
    <div class="lab-copy">
      <span class="lab-eyebrow">Laboratoire d'analyses médicales</span>
      <strong class="lab-name">{{lab.display_name}}</strong>
      <span class="lab-slogan">{{lab.slogan}}</span>
    </div>
  </div>

  <div class="report-heading">
    <span class="report-kicker">Compte rendu</span>
    <strong>Analyses biologiques</strong>
    <span class="report-reference">Dossier {{order.accession_number}}</span>
  </div>

  <div class="lab-meta">
    <div class="meta-line meta-address">
      <span>{{lab.address}}</span>
      <span>{{lab.city}}</span>
      <span>{{lab.country}}</span>
    </div>
    <div class="meta-line">
      <span>Tél. {{lab.primary_phone}}</span>
      <span>{{lab.email}}</span>
      <span>{{lab.website}}</span>
    </div>
    <div class="meta-line meta-legal">
      <span>Agrément {{lab.laboratory_license}}</span>
      <span>RC {{lab.registration_number}}</span>
      <span>NIF {{lab.tax_id}}</span>
    </div>
  </div>
</header>
""".strip()

CSS = """
.modern-report-header{
  display:grid;
  grid-template-columns:1fr auto;
  gap:9px 18px;
  padding:0 0 10px;
  color:#000;
  border-bottom:2px solid #111827;
  font-family:Arial,Helvetica,sans-serif
}
.lab-identity{
  display:flex;
  min-width:0;
  align-items:center;
  gap:11px
}
.lab-logo-box{
  position:relative;
  display:flex;
  width:44px;
  height:44px;
  flex:0 0 44px;
  align-items:center;
  justify-content:center;
  overflow:hidden;
  background:#eef8f6;
  border:1px solid #087f76;
  border-radius:8px
}
.lab-logo-fallback{
  color:#087f76;
  font-size:13px;
  font-weight:900;
  letter-spacing:.06em
}
.lab-logo-image{
  position:absolute;
  inset:0;
  display:block;
  width:100%;
  height:100%;
  object-fit:contain;
  padding:4px;
  background:#fff
}
.lab-logo-image[src=""]{display:none}
.lab-copy{
  display:flex;
  min-width:0;
  flex-direction:column;
  gap:2px
}
.lab-eyebrow,
.report-kicker{
  font-size:7px;
  font-weight:800;
  letter-spacing:.12em;
  line-height:1.2;
  text-transform:uppercase
}
.lab-name{
  overflow-wrap:anywhere;
  font-size:20px;
  font-weight:900;
  letter-spacing:.02em;
  line-height:1.05
}
.lab-slogan{
  font-size:9px;
  font-weight:600;
  line-height:1.25
}
.lab-slogan:empty{display:none}
.report-heading{
  display:flex;
  min-width:150px;
  flex-direction:column;
  align-items:flex-end;
  justify-content:center;
  gap:3px;
  text-align:right
}
.report-heading strong{
  font-size:14px;
  font-weight:900;
  letter-spacing:.08em;
  line-height:1.1;
  text-transform:uppercase
}
.report-reference{
  padding:2px 7px;
  background:#f3f4f6;
  border:1px solid #d1d5db;
  border-radius:999px;
  font-size:8px;
  font-weight:800;
  line-height:1.3
}
.lab-meta{
  display:grid;
  grid-column:1/-1;
  grid-template-columns:1fr;
  gap:3px;
  padding-top:8px;
  border-top:1px solid #d1d5db;
  font-size:8px;
  font-weight:600;
  line-height:1.25
}
.meta-line{
  display:flex;
  flex-wrap:wrap;
  gap:4px 12px
}
.meta-line span:empty{display:none}
.meta-line span:not(:empty) + span:not(:empty):before{
  margin-right:12px;
  content:"|";
  color:#9ca3af
}
.meta-legal{
  font-size:7px;
  font-weight:700;
  letter-spacing:.04em;
  text-transform:uppercase
}
@media print{
  .modern-report-header{break-inside:avoid}
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
