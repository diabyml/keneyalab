"""Add antibiogramme report renderer.

Revision ID: d1e2f3a4b5c6
Revises: c4d5e6f7a8b9
"""

import sqlalchemy as sa
from alembic import op

revision = "d1e2f3a4b5c6"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


RENDERER_ID = "55555555-5555-4555-8555-555555555555"
VERSION_ID = "65555555-5555-4555-8555-555555555555"

ANTIBIOGRAMME_RENDERER_JSX = """
function Renderer({ category }) {
  const resultClass = (value) => {
    const normalized = String(value || "").trim().toLowerCase();
    if (normalized === "s" || normalized.includes("sensible")) return "antibio-result antibio-sensitive";
    if (normalized === "i" || normalized.includes("intermediaire") || normalized.includes("intermédiaire")) return "antibio-result antibio-intermediate";
    if (normalized === "r" || normalized.includes("resistant") || normalized.includes("résistant")) return "antibio-result antibio-resistant";
    return "antibio-result";
  };

  return (
    <section className="antibio-category">
      <h2>{category.name}</h2>
      {category.tests.map((test) => (
        <div className="antibio-test" key={test.order_item_id}>
          {test.catalog_name ? <h3>{test.catalog_name}</h3> : null}
          <table className="antibio-table">
            <thead>
              <tr>
                <th>Antibiotique</th>
                <th>Résultat</th>
              </tr>
            </thead>
            <tbody>
              {test.analytes.map((analyte) => (
                <tr key={analyte.analyte_id}>
                  <td>{analyte.analyte_name}</td>
                  <td>
                    <span className={resultClass(analyte.result_value)}>
                      {analyte.result_value || "—"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}
""".strip()

ANTIBIOGRAMME_RENDERER_CSS = """
.antibio-category{
  margin:18px 0;
  font-size:11px
}
.antibio-category h2{
  margin:0 0 10px;
  padding-bottom:6px;
  border-bottom:1px solid #374151;
  font-size:14px;
  font-weight:700
}
.antibio-test{
  margin:12px 0 16px
}
.antibio-test h3{
  margin:0 0 6px;
  font-size:12px;
  font-weight:700
}
.antibio-table{
  width:100%;
  border-collapse:collapse;
  table-layout:fixed
}
.antibio-table th,
.antibio-table td{
  padding:7px 6px;
  border:1px solid #d1d5db;
  text-align:left;
  vertical-align:top
}
.antibio-table th{
  background:#f3f4f6;
  font-size:10px;
  font-weight:700;
  text-transform:uppercase
}
.antibio-table th:nth-child(1),
.antibio-table td:nth-child(1){
  width:68%
}
.antibio-table th:nth-child(2),
.antibio-table td:nth-child(2){
  width:32%;
  text-align:center
}
.antibio-result{
  display:inline-block;
  min-width:56px;
  padding:3px 8px;
  border:1px solid #9ca3af;
  font-weight:700;
  text-align:center
}
.antibio-sensitive{
  border-color:#15803d;
  color:#15803d
}
.antibio-intermediate{
  border-color:#b45309;
  color:#b45309
}
.antibio-resistant{
  border-color:#b91c1c;
  color:#b91c1c
}
""".strip()


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO report_renderers
                (id, name, description, is_builtin)
            VALUES
                (:renderer_id, 'Antibiogramme',
                 'Rendu par défaut pour les résultats d''antibiogramme', TRUE)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"renderer_id": RENDERER_ID},
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO report_renderer_versions
                (id, renderer_id, version, status, jsx_source, css_source, published_at)
            VALUES
                (:version_id, :renderer_id, 1, 'published', :jsx_source, :css_source, NOW())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "version_id": VERSION_ID,
            "renderer_id": RENDERER_ID,
            "jsx_source": ANTIBIOGRAMME_RENDERER_JSX,
            "css_source": ANTIBIOGRAMME_RENDERER_CSS,
        },
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE categories
            SET report_renderer_id = NULL
            WHERE report_renderer_id = :renderer_id
            """
        ),
        {"renderer_id": RENDERER_ID},
    )
    connection.execute(
        sa.text(
            """
            UPDATE report_settings
            SET default_renderer_id = NULL
            WHERE default_renderer_id = :renderer_id
            """
        ),
        {"renderer_id": RENDERER_ID},
    )
    connection.execute(
        sa.text("DELETE FROM report_renderer_versions WHERE id = :version_id"),
        {"version_id": VERSION_ID},
    )
    connection.execute(
        sa.text("DELETE FROM report_renderers WHERE id = :renderer_id"),
        {"renderer_id": RENDERER_ID},
    )
