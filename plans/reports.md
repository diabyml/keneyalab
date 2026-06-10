# Dual-Path Report Rendering Architecture

## Summary

Both browser printing and backend PDF generation will use:

- The same immutable `ReportRenderDocument` JSON snapshot.
- The same React report components, CSS, fonts, pagination rules, layouts, and
  category renderers.
- A dedicated Node/Chromium rendering service for backend PDF generation.

The FastAPI backend remains responsible for clinical data, permissions,
renderer selection, snapshot creation, release workflow, and delivery.

## Rendering Contract

Create a versioned `ReportRenderDocument` structure containing:

- `schema_version`
- Report and laboratory metadata
- Patient and doctor snapshots
- Selected layout version and structured header, details, and footer definitions
- Page configuration
- Ordered category sections
- Resolved renderer type and configuration for each section
- Verified result snapshots, units, ranges, flags, comments, signatures, and
  timestamps

The backend constructs and validates this document. Neither the browser nor the
rendering service queries clinical tables while rendering.

## Shared React Renderer

Create a shared TypeScript report-renderer package containing:

- `ReportDocument`
- Structured layout block renderer
- `StandardTableRenderer`
- `AtbTableRenderer`
- `NarrativeRenderer`
- `ImageGridRenderer`
- Print CSS, page breaks, fonts, headers, footers, and page numbering

The main frontend uses this package to render previews and invoke
`window.print()`. The rendering service uses the same package in headless
Chromium and calls `page.pdf()`. This provides exact visual parity between
browser and backend output.

## Backend Rendering Service

Add an internal Node/Chromium service with:

- `POST /render/pdf`
- Input: complete `ReportRenderDocument`
- Output: PDF bytes plus content hash
- No database access
- No arbitrary HTML or JavaScript input
- Internal authentication, request-size limits, timeout, and supported
  schema-version validation

The FastAPI service calls it for email, WhatsApp, portal, download, or archived
PDF generation.

## Database Design

### Design Components

`report_design_components`

- `id`
- `name`
- `component_type`: `header`, `patient_doctor_details`, `footer`
- `description`
- `is_deleted`
- timestamps

`report_design_component_versions`

- `id`
- `component_id`
- `version`
- `schema_version`
- `definition JSONB`
- `status`: `draft`, `published`, `archived`
- `created_by_id`
- `published_at`
- timestamps
- Unique constraint on `(component_id, version)`

The structured `definition` supports validated blocks such as text, image,
bound field, row, column, divider, and spacer. Bindings are restricted to
documented fields such as `patient.full_name`, `doctor.name`,
`order.accession_number`, and `lab.logo`.

Published versions are immutable.

### Named Layouts

`report_layouts`

- `id`
- `name`
- `description`
- `is_default`
- `is_deleted`
- timestamps
- Partial unique index allowing only one non-deleted default layout

`report_layout_versions`

- `id`
- `layout_id`
- `version`
- `header_version_id`
- `details_version_id`
- `footer_version_id`
- `page_config JSONB`
- `status`
- `created_by_id`
- `published_at`
- timestamps
- Unique constraint on `(layout_id, version)`

`page_config` contains paper size, margins, orientation, repeated header/footer
behavior, and page numbering.

### Managed Content Renderers

`result_renderers`

- `id`
- `name`
- `renderer_type`: `standard_table`, `atb_table`, `narrative`, `image_grid`
- `description`
- `is_system_default`
- `is_deleted`
- timestamps
- Only one active system default

`result_renderer_versions`

- `id`
- `renderer_id`
- `version`
- `schema_version`
- `config JSONB`
- `status`
- `created_by_id`
- `published_at`
- timestamps
- Unique constraint on `(renderer_id, version)`

The backend maintains a registry of built-in renderer implementations. The
`config` is validated through a renderer-specific Pydantic schema and is never
treated as arbitrary executable code.

Example configurations:

- Standard table: displayed columns, abnormal markers, reference ranges,
  grouping, and sorting
- ATB table: organism grouping, antibiotic rows, S/I/R columns, MIC display,
  and legend
- Narrative: heading, result text, comments, and interpretation placement
- Image grid: captions, dimensions, and page-breaking behavior

### Category Defaults

Add `default_result_renderer_id` to `categories`, referencing
`result_renderers.id`.

Resolution order during preview:

1. Explicit renderer selected for the category in the current preview.
2. Category's default renderer.
3. System default renderer.

Catalog entries without a category use a generated `Sans categorie` section and
the system default renderer.

### Released Reports

Update `reports` to store:

- Existing report fields
- `report_layout_version_id`
- `render_schema_version`
- `render_document JSONB`
- `pdf_storage_url`
- `content_hash`
- `generation_status`: `pending`, `rendering`, `ready`, `failed`
- `generation_error`
- Version, release, voiding, and audit metadata

`report_sections`

- `id`
- `report_id`
- `category_id`, nullable for uncategorized results
- `category_name_snapshot`
- `sort_order`
- `renderer_version_id`
- `renderer_config_snapshot JSONB`
- `content_snapshot JSONB`
- timestamps

`content_snapshot` contains the normalized result data passed to the renderer,
including analyte names, values, units, reference ranges, flags, comments,
verification data, and relevant catalog information.

The stored PDF remains the authoritative released artifact. Snapshots permit
auditing or deterministic regeneration without reading mutable current results
or configuration.

### Deliveries

Separate document generation from delivery with `report_deliveries`:

- `id`
- `report_id`
- `channel`: `email`, `whatsapp`, `portal`, `print`
- Recipient metadata
- `status`: `pending`, `sent`, `failed`
- Attempt count
- Last error
- Sent timestamp
- timestamps

This allows one generated report to be delivered through multiple channels
without generating separate report records.

## Workflows

### Preview

1. The frontend requests a preview with layout and category-renderer overrides.
2. The backend resolves configuration and returns a non-persisted
   `ReportRenderDocument`.
3. React renders it directly in the browser.
4. The preview is clearly marked unreleased.

### Release

1. The backend validates that required results are verified.
2. It resolves published layout and renderer versions.
3. It creates the immutable render document.
4. The rendering service generates the PDF.
5. The backend stores the PDF, report snapshot, and content hash.
6. The report becomes `ready` and immutable.
7. Later result changes require a new report version.

The release persistence and final status transition must be transactional.
Failed rendering must not produce a released report.

### Browser Printing

Released reports load `reports.render_document`, render through React, and call
`window.print()`.

They never rebuild from current patient, doctor, result, category, or
configuration records.

### Media Delivery

Email and other delivery jobs reuse the stored PDF. Retries create or update
delivery attempts without regenerating the report.

## APIs

- `POST /orders/{order_id}/reports/preview`
- `POST /orders/{order_id}/reports/release`
- `GET /reports/{report_id}/render-document`
- `GET /reports/{report_id}/pdf`
- `POST /reports/{report_id}/deliveries`
- CRUD and publish endpoints for layouts, components, and renderers

Preview and release requests accept:

- `layout_id`
- Optional category-to-renderer overrides

Only published, non-deleted configurations can be selected for release.
Configurations referenced by published versions cannot be hard-deleted; they
are archived or soft-deleted.

## Migration

- Seed a standard-table renderer and make it the system default.
- Seed header, patient/doctor details, and footer components.
- Seed one default named layout.
- Assign the standard renderer to existing categories.
- Preserve existing `reports.report_template_id` temporarily for compatibility.
- Migrate usable template metadata, then remove the legacy relationship after
  report generation uses layout versions.
- Keep existing released report URLs unchanged.

## Test Plan

- Category default, preview override, and system fallback resolution
- Mixed-category reports using different renderer types
- ATB and standard-table sections in the same document
- Layout composition from exact component versions
- Browser and backend screenshot/PDF visual regression parity
- Matching headers, details, footers, fonts, and page breaks
- Published configuration immutability
- Historical reports unchanged after result or configuration edits
- Uncategorized catalog result fallback
- Rejected, pending, and superseded results excluded
- Backend delivery reuses the stored PDF
- Transaction rollback when PDF generation or snapshot persistence fails
- Explicit failure for unsupported render schema versions
- Rejection of arbitrary scripts and invalid block definitions
- Multiple delivery channels with independent retries
- Authorization for configuration, preview, release, reprint, delivery, and
  void operations

## Assumptions

- One released document can contain several category sections.
- Renderer overrides are selected during report preview, not order creation.
- Renderers are vetted backend implementations with managed structured
  configuration.
- Layout definitions use structured JSON.
- Multiple named layouts can exist, with one default and optional per-report
  selection.
- Exact browser and backend visual parity is required.
- A dedicated Node/Chromium rendering service is acceptable.
- React is the only presentation implementation.
- FastAPI owns clinical data transformation and snapshot creation.
- Released browser printing uses the immutable report snapshot.
