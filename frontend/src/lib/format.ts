export function formatDecimal(
  value: number | string | null | undefined,
  fallback = "-",
) {
  if (value === null || value === undefined || value === "") return fallback
  const amount = Number(value)
  if (!Number.isFinite(amount)) return fallback

  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatPrice(value: number | string | null | undefined) {
  const amount = Number(value ?? 0)

  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "XOF",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0)
}
