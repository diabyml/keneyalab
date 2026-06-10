import type { GenderType, PatientPublic } from "@/client"

export const GENDER_LABELS: Record<GenderType, string> = {
  male: "Homme",
  female: "Femme",
}

export type PatientSortBy =
  | "identifier"
  | "first_name"
  | "last_name"
  | "date_of_birth"
  | "created_at"

export type StatusFilter = "active" | "deleted" | "all"
export type GenderFilter = GenderType | "all"

export function formatDate(value: string | null | undefined) {
  if (!value) return "-"
  return new Intl.DateTimeFormat("fr-FR").format(new Date(value))
}

export function getPatientName(
  patient: Pick<PatientPublic, "first_name" | "last_name">,
) {
  return `${patient.first_name} ${patient.last_name}`.trim()
}

export function getPatientAge(dateOfBirth: string) {
  const birth = new Date(dateOfBirth)
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const monthDelta = today.getMonth() - birth.getMonth()
  if (
    monthDelta < 0 ||
    (monthDelta === 0 && today.getDate() < birth.getDate())
  ) {
    age -= 1
  }
  return age
}

export function patientExportColumns() {
  return [
    { header: "Identifiant", value: (row: PatientPublic) => row.identifier },
    { header: "Prénom", value: (row: PatientPublic) => row.first_name },
    { header: "Nom", value: (row: PatientPublic) => row.last_name },
    {
      header: "Date de naissance",
      value: (row: PatientPublic) => formatDate(row.date_of_birth),
    },
    {
      header: "Sexe",
      value: (row: PatientPublic) => GENDER_LABELS[row.gender],
    },
    { header: "Téléphone", value: (row: PatientPublic) => row.phone ?? "" },
    { header: "Adresse", value: (row: PatientPublic) => row.address ?? "" },
    {
      header: "Statut",
      value: (row: PatientPublic) => (row.is_deleted ? "Supprimé" : "Actif"),
    },
  ]
}
