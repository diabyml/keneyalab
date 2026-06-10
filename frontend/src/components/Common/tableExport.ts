export interface ExportColumn<TData> {
  header: string
  value: (row: TData) => string | number | boolean | null | undefined
}

function escapeCsvValue(value: string | number | boolean | null | undefined) {
  const text = value === null || value === undefined ? "" : String(value)
  if (!/[",\n\r]/.test(text)) return text
  return `"${text.replace(/"/g, '""')}"`
}

function fallbackColumns<TData extends object>(
  rows: TData[],
): ExportColumn<TData>[] {
  const keys = Array.from(
    new Set(
      rows.flatMap((row) =>
        Object.entries(row)
          .filter(([, value]) =>
            ["string", "number", "boolean"].includes(typeof value),
          )
          .map(([key]) => key),
      ),
    ),
  )
  return keys.map((key) => ({
    header: key,
    value: (row) => {
      const value = row[key as keyof TData]
      if (
        typeof value === "string" ||
        typeof value === "number" ||
        typeof value === "boolean"
      ) {
        return value
      }
      return ""
    },
  }))
}

export function downloadCsv<TData extends object>({
  rows,
  columns,
  filename,
}: {
  rows: TData[]
  columns?: ExportColumn<TData>[]
  filename: string
}) {
  const exportColumns = columns?.length ? columns : fallbackColumns(rows)
  const csv = [
    exportColumns.map((column) => escapeCsvValue(column.header)).join(","),
    ...rows.map((row) =>
      exportColumns
        .map((column) => escapeCsvValue(column.value(row)))
        .join(","),
    ),
  ].join("\n")

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
