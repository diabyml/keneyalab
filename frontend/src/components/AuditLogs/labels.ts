import type { AuditAction, AuditCategory } from "@/client"

export const AUDIT_ACTION_LABELS: Record<AuditAction, string> = {
  insert: "Création",
  update: "Modification",
  delete: "Suppression",
  login_success: "Connexion réussie",
  login_failed: "Échec de connexion",
  password_recovery: "Récupération demandée",
  password_reset: "Mot de passe réinitialisé",
}

export const AUDIT_CATEGORY_LABELS: Record<AuditCategory, string> = {
  clinical: "Clinique",
  workflow: "Flux laboratoire",
  finance: "Finance",
  configuration: "Configuration",
  security: "Sécurité",
  system: "Système",
}

export const AUDIT_ENTITY_LABELS: Record<string, string> = {
  authentication: "Authentification",
  user: "Utilisateurs",
  permissions: "Permissions",
  roles: "Rôles",
  role_permissions: "Permissions des rôles",
  user_roles: "Rôles des utilisateurs",
  patients: "Patients",
  patient_insurance: "Assurances patient",
  doctors: "Médecins",
  orders: "Demandes",
  order_revisions: "Révisions de demande",
  order_specimens: "Prélèvements",
  order_items: "Examens demandés",
  order_catalog_item_analytes: "Analytes personnalisés",
  analyte_results: "Résultats",
  analyte_result_comments: "Commentaires de résultat",
  critical_notifications: "Notifications critiques",
  reports: "Comptes rendus",
  invoices: "Factures",
  invoice_lines: "Lignes de facture",
  payment_transactions: "Paiements",
  payment_refunds: "Remboursements",
  customer_credits: "Avoirs",
  doctor_commission_configs: "Configurations de commission",
  doctor_commission_entries: "Écritures de commission",
  doctor_commission_adjustments: "Ajustements de commission",
  doctor_commission_payments: "Paiements de commission",
  catalog: "Catalogue",
  analytes: "Analytes",
  validation_rules: "Règles de validation",
  consistency_rules: "Règles de cohérence",
  reflex_rules: "Règles réflexes",
  categories: "Catégories",
  specimen_types: "Types de prélèvement",
  units: "Unités",
  titles: "Titres",
  patient_contexts: "Contextes patient",
  payment_methods: "Méthodes de paiement",
  rejection_reasons: "Motifs de rejet",
  insurance_providers: "Assureurs",
  insurance_pricing: "Tarifs assurance",
  finance_settings: "Configuration financière",
  lab_settings: "Configuration du laboratoire",
}

export const AUDIT_ENTITY_OPTIONS = Object.entries(AUDIT_ENTITY_LABELS).sort(
  ([, left], [, right]) => left.localeCompare(right, "fr"),
)

export function auditEntityLabel(tableName: string) {
  return AUDIT_ENTITY_LABELS[tableName] ?? tableName.replace(/_/g, " ")
}
