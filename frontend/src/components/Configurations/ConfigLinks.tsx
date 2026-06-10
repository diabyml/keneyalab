import { useNavigate } from "@tanstack/react-router"
import {
  BadgeDollarSign,
  Building2,
  CreditCard,
  FolderTree,
  KeyRound,
  type LucideIcon,
  Microscope,
  Ruler,
  Search,
  Settings2,
  ShieldCheck,
  Tag,
  TestTube,
  UserRound,
  Users,
  WalletCards,
  XCircle,
} from "lucide-react"
import { useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import {
  Empty,
  EmptyDescription,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Input } from "@/components/ui/input"
import { usePermission } from "@/hooks/usePermission"
import { cn } from "@/lib/utils"

interface ConfigLink {
  id: string
  name: string
  description: string
  icon: LucideIcon
  requiredPermission?: { resource: string; action: string }
  category: string
  navigateTo?: string
}

const CONFIG_LINKS: ConfigLink[] = [
  {
    id: "roles-config",
    name: "Rôles",
    description: "Définir les rôles et leurs permissions",
    icon: ShieldCheck,
    requiredPermission: { resource: "roles", action: "manage" },
    category: "RBAC",
    navigateTo: "/configurations/roles",
  },
  {
    id: "permissions-config",
    name: "Permissions",
    description: "Gérer les permissions granulaires des ressources",
    icon: KeyRound,
    requiredPermission: { resource: "roles", action: "manage" },
    category: "RBAC",
    navigateTo: "/configurations/permissions",
  },
  {
    id: "users-config",
    name: "Utilisateurs",
    description: "Gérer les comptes utilisateurs et l'assignation des rôles",
    icon: Users,
    requiredPermission: { resource: "users", action: "manage" },
    category: "RBAC",
    navigateTo: "/configurations/users",
  },
  {
    id: "catalogue-config",
    name: "Catalogue",
    description: "Gérer les tests, panels, prélèvements et tarifs",
    icon: TestTube,
    requiredPermission: { resource: "catalog", action: "manage" },
    category: "Catalogue & règles",
    navigateTo: "/configurations/catalogue",
  },
  {
    id: "analytes-config",
    name: "Analytes",
    description: "Gérer les analytes, types de résultat et formules",
    icon: Microscope,
    requiredPermission: { resource: "catalog", action: "manage" },
    category: "Catalogue & règles",
    navigateTo: "/configurations/analytes",
  },
  {
    id: "categories-config",
    name: "Catégories",
    description: "Gérer le regroupement et l'ordre d'affichage du catalogue",
    icon: FolderTree,
    requiredPermission: { resource: "catalog", action: "manage" },
    category: "Catalogue & règles",
    navigateTo: "/configurations/categories",
  },
  {
    id: "regles-validation-config",
    name: "Règles de validation",
    description: "Configurer les plages, seuils critiques et delta checks",
    icon: ShieldCheck,
    requiredPermission: { resource: "rules", action: "manage" },
    category: "Catalogue & règles",
    navigateTo: "/configurations/regles-validation",
  },
  {
    id: "regles-automatisees-config",
    name: "Règles automatisées",
    description: "Gérer les règles de cohérence et les règles réflexes",
    icon: Settings2,
    requiredPermission: { resource: "rules", action: "manage" },
    category: "Catalogue & règles",
    navigateTo: "/configurations/regles-automatisees",
  },
  {
    id: "titres-config",
    name: "Titres",
    description: "Gérer les titres de civilité (Dr, Pr, etc.)",
    icon: Tag,
    requiredPermission: { resource: "reference_data", action: "manage" },
    category: "Données de référence",
    navigateTo: "/configurations/titres",
  },
  {
    id: "unites-config",
    name: "Unités",
    description: "Gérer les unités de mesure des analytes",
    icon: Ruler,
    requiredPermission: { resource: "reference_data", action: "manage" },
    category: "Données de référence",
    navigateTo: "/configurations/unites",
  },
  {
    id: "contexts-patient-config",
    name: "Contextes patient",
    description: "Gérer les contextes cliniques (à jeun, enceinte, etc.)",
    icon: UserRound,
    requiredPermission: { resource: "reference_data", action: "manage" },
    category: "Données de référence",
    navigateTo: "/configurations/contexts-patient",
  },
  {
    id: "methodes-paiement-config",
    name: "Méthodes de paiement",
    description: "Gérer les méthodes de paiement acceptées",
    icon: CreditCard,
    requiredPermission: { resource: "reference_data", action: "manage" },
    category: "Données de référence",
    navigateTo: "/configurations/methodes-paiement",
  },
  {
    id: "motifs-rejet-config",
    name: "Motifs de rejet",
    description: "Gérer les motifs de rejet des prélèvements",
    icon: XCircle,
    requiredPermission: { resource: "reference_data", action: "manage" },
    category: "Données de référence",
    navigateTo: "/configurations/motifs-rejet",
  },
  {
    id: "types-prelevement-config",
    name: "Types de prélèvement",
    description: "Gérer les types de prélèvement (sang, urine, etc.)",
    icon: TestTube,
    requiredPermission: { resource: "reference_data", action: "manage" },
    category: "Données de référence",
    navigateTo: "/configurations/types-prelevement",
  },
  {
    id: "assureurs-config",
    name: "Assureurs",
    description: "Gérer les compagnies d'assurance",
    icon: Building2,
    requiredPermission: { resource: "reference_data", action: "manage" },
    category: "Assurances",
    navigateTo: "/configurations/assureurs",
  },
  {
    id: "finance-config",
    name: "Finance",
    description: "Configurer la répartition des remises et commissions",
    icon: WalletCards,
    requiredPermission: { resource: "finance", action: "manage" },
    category: "Finance",
    navigateTo: "/configurations/finance",
  },
  {
    id: "tarifs-assurance-config",
    name: "Tarifs assurance",
    description: "Définir les prix des tests par assureur",
    icon: BadgeDollarSign,
    requiredPermission: { resource: "finance", action: "manage" },
    category: "Assurances",
    navigateTo: "/configurations/tarifs-assurance",
  },
]

function ConfigLinks() {
  const navigate = useNavigate()
  const canManageRoles = usePermission("roles", "manage")
  const canManageUsers = usePermission("users", "manage")
  const canManageCatalog = usePermission("catalog", "manage")
  const canManageRules = usePermission("rules", "manage")
  const canManageReferenceData = usePermission("reference_data", "manage")
  const canManageFinance = usePermission("finance", "manage")
  const [search, setSearch] = useState("")

  function accessAllowed(link: ConfigLink): boolean {
    if (!link.requiredPermission) return true
    if (link.requiredPermission.resource === "roles") return canManageRoles
    if (link.requiredPermission.resource === "users") return canManageUsers
    if (link.requiredPermission.resource === "catalog") return canManageCatalog
    if (link.requiredPermission.resource === "rules") return canManageRules
    if (link.requiredPermission.resource === "reference_data")
      return canManageReferenceData
    if (link.requiredPermission.resource === "finance") return canManageFinance
    return false
  }

  const filteredLinks = useMemo(() => {
    const q = search.toLowerCase().trim()
    return CONFIG_LINKS.filter((link) => {
      if (!q) return true
      return link.name.toLowerCase().includes(q)
    })
  }, [search])

  const groupedLinks = useMemo(() => {
    const groups: Record<string, ConfigLink[]> = {}
    filteredLinks.forEach((link) => {
      if (!groups[link.category]) groups[link.category] = []
      groups[link.category].push(link)
    })
    return groups
  }, [filteredLinks])

  const categories = Object.keys(groupedLinks)

  return (
    <div className="flex flex-col gap-6">
      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Rechercher dans les configurations…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Empty state */}
      {categories.length === 0 && (
        <Empty>
          <EmptyMedia variant="icon">
            <Search />
          </EmptyMedia>
          <EmptyTitle>Aucun résultat</EmptyTitle>
          <EmptyDescription>
            Essayez d'ajuster votre recherche.
          </EmptyDescription>
        </Empty>
      )}

      {/* Grouped config links */}
      {categories.map((category) => (
        <div key={category} className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground">
            {category}
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {groupedLinks[category].map((link) => {
              const allowed = accessAllowed(link)
              const Icon = link.icon

              return (
                <button
                  type="button"
                  key={link.id}
                  disabled={!allowed}
                  onClick={() => {
                    if (allowed && link.navigateTo) {
                      navigate({ to: link.navigateTo })
                    }
                  }}
                  className={cn(
                    "group relative flex items-start gap-3 rounded-xl border p-4 text-left transition-[border-color,box-shadow,background-color] duration-200 ease-out",
                    "active:scale-[0.98]",
                    allowed
                      ? "border-border bg-card hover:border-primary/30 hover:bg-accent/40 hover:shadow-sm cursor-pointer"
                      : "border-border/50 bg-muted/30 cursor-not-allowed opacity-60",
                  )}
                >
                  <div
                    className={cn(
                      "flex size-10 shrink-0 items-center justify-center rounded-lg transition-colors",
                      allowed
                        ? "bg-primary/10 text-primary group-hover:bg-primary/15"
                        : "bg-muted text-muted-foreground",
                    )}
                  >
                    <Icon className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "text-sm font-medium",
                          !allowed && "text-muted-foreground",
                        )}
                      >
                        {link.name}
                      </span>
                      {!allowed && (
                        <Badge
                          variant="outline"
                          className="bg-background h-5 px-1.5 py-0 text-xs"
                        >
                          Verrouillé
                        </Badge>
                      )}
                    </div>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                      {link.description}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

export default ConfigLinks
