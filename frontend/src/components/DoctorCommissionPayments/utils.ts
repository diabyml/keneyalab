export const formatMoney = (value: string | number) =>
  new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "XOF",
    maximumFractionDigits: 0,
  }).format(Number(value))

export const formatDateTime = (value?: string | null) =>
  value
    ? new Intl.DateTimeFormat("fr-FR", {
        dateStyle: "long",
        timeStyle: "short",
      }).format(new Date(value))
    : "—"

export const formatDate = (value?: string | null) =>
  value
    ? new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(
        new Date(value),
      )
    : "—"
