import type { AuditLogPublic } from "@/client"

export function formatAuditDate(value?: string | null) {
  if (!value) return "Date inconnue"
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value))
}

export function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

export function eventSummary(event: AuditLogPublic) {
  const metadata = asRecord(event.metadata)
  const reason =
    metadata.reason ??
    metadata.correction_reason ??
    asRecord(event.new_values).correction_reason ??
    asRecord(event.new_values).reason
  if (typeof reason === "string" && reason.trim()) return reason

  if (event.action === "login_failed") return "Identifiants refusés"
  if (event.action === "login_success") return "Session authentifiée"
  if (event.action === "password_recovery")
    return "Demande de récupération de compte"
  if (event.action === "password_reset") return "Changement du mot de passe"

  const changedKeys = new Set([
    ...Object.keys(asRecord(event.old_values)),
    ...Object.keys(asRecord(event.new_values)),
  ])
  if (changedKeys.size > 0) {
    return `${changedKeys.size} champ${changedKeys.size > 1 ? "s" : ""} concerné${changedKeys.size > 1 ? "s" : ""}`
  }
  return "Événement enregistré"
}

export function entityLink(event: AuditLogPublic) {
  if (!event.record_id) return null
  if (event.table_name === "patients") {
    return {
      to: "/patients/$patientId" as const,
      params: { patientId: event.record_id },
    }
  }
  if (event.table_name === "orders") {
    return {
      to: "/orders/$orderId" as const,
      params: { orderId: event.record_id },
    }
  }
  if (event.table_name === "invoices") {
    return {
      to: "/invoices/$invoiceId" as const,
      params: { invoiceId: event.record_id },
    }
  }
  return null
}
