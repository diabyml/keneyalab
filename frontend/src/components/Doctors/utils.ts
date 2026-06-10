import type {
  DoctorCommissionConfigPublic,
  DoctorWithTitlePublic,
} from "@/client"

export type DoctorSortBy =
  | "first_name"
  | "last_name"
  | "provenance"
  | "created_at"
export type StatusFilter = "active" | "deleted" | "all"

export function getDoctorName(
  doctor: Pick<
    DoctorWithTitlePublic,
    "first_name" | "last_name" | "title_name"
  >,
) {
  return [doctor.title_name, doctor.first_name, doctor.last_name]
    .filter(Boolean)
    .join(" ")
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "-"
  return new Intl.DateTimeFormat("fr-FR").format(new Date(value))
}

export function formatPercent(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "-"
  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value) * 100)
}

export function percentToDecimalString(value: string) {
  const normalized = value.replace(",", ".").trim()
  if (!normalized) return "0"
  return (Number(normalized) / 100).toFixed(4)
}

export function decimalToPercentString(
  value: string | number | null | undefined,
) {
  if (value === null || value === undefined || value === "") return ""
  return (Number(value) * 100).toFixed(2)
}

export function doctorExportColumns() {
  return [
    {
      header: "Titre",
      value: (row: DoctorWithTitlePublic) => row.title_name ?? "",
    },
    { header: "Prénom", value: (row: DoctorWithTitlePublic) => row.first_name },
    { header: "Nom", value: (row: DoctorWithTitlePublic) => row.last_name },
    {
      header: "Provenance",
      value: (row: DoctorWithTitlePublic) => row.provenance ?? "",
    },
    {
      header: "Téléphone",
      value: (row: DoctorWithTitlePublic) => row.phone ?? "",
    },
    {
      header: "Statut",
      value: (row: DoctorWithTitlePublic) =>
        row.is_deleted ? "Supprimé" : "Actif",
    },
  ]
}

export function commissionExportColumns() {
  return [
    {
      header: "Commission",
      value: (row: DoctorCommissionConfigPublic) =>
        `${formatPercent(row.commission_rate)} %`,
    },
    {
      header: "Commission assurance",
      value: (row: DoctorCommissionConfigPublic) =>
        `${formatPercent(row.insurance_commission_rate)} %`,
    },
    {
      header: "Début",
      value: (row: DoctorCommissionConfigPublic) =>
        formatDate(row.effective_from),
    },
    {
      header: "Fin",
      value: (row: DoctorCommissionConfigPublic) =>
        formatDate(row.effective_until),
    },
  ]
}
