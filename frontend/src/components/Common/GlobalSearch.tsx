import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import {
  BadgeDollarSign,
  Building2,
  ClipboardList,
  CreditCard,
  FileText,
  FolderTree,
  HandCoins,
  Home,
  KeyRound,
  type LucideIcon,
  Microscope,
  PackageSearch,
  ReceiptText,
  Ruler,
  ScrollText,
  Search,
  Settings2,
  ShieldCheck,
  Stethoscope,
  Tag,
  TestTube,
  UserRound,
  Users,
  WalletCards,
  XCircle,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { type GlobalSearchResultPublic, GlobalSearchService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command"
import { usePermission } from "@/hooks/usePermission"
import { cn } from "@/lib/utils"

type SearchItem = {
  id: string
  title: string
  subtitle?: string
  badge?: string
  href: string
  group: string
  icon: LucideIcon
  keywords?: string[]
  allowed: boolean
}

const RESULT_GROUP_LABELS: Record<string, string> = {
  orders: "Demandes",
  patients: "Patients",
  doctors: "Médecins",
  invoices: "Factures",
  catalog: "Catalogue",
  specimens: "Prélèvements",
  results: "Résultats",
  reagents: "Réactifs",
}

const RESULT_ICONS: Record<string, LucideIcon> = {
  orders: ClipboardList,
  patients: UserRound,
  doctors: Stethoscope,
  invoices: ReceiptText,
  catalog: TestTube,
  specimens: TestTube,
  results: Microscope,
  reagents: PackageSearch,
}

function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
}

function matches(item: SearchItem, query: string): boolean {
  const q = normalize(query.trim())
  if (!q) return true

  return normalize(
    [
      item.title,
      item.subtitle,
      item.badge,
      item.group,
      ...(item.keywords ?? []),
    ]
      .filter(Boolean)
      .join(" "),
  ).includes(q)
}

function useShortcutLabel() {
  return useMemo(() => {
    if (typeof navigator === "undefined") return "Ctrl K"
    return /Mac|iPhone|iPad|iPod/.test(navigator.platform) ? "⌘K" : "Ctrl K"
  }, [])
}

export function GlobalSearch() {
  const navigate = useNavigate()
  const shortcutLabel = useShortcutLabel()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")

  const canViewOrders = usePermission("orders", "view")
  const canCreateOrders = usePermission("orders", "create")
  const canViewSpecimens = usePermission("specimens", "view")
  const canViewResults = usePermission("results", "view")
  const canViewReagents = usePermission("reagents", "view")
  const canViewInvoices = usePermission("invoices", "view")
  const canViewCommissions = usePermission("commissions", "view")
  const canViewPatients = usePermission("patients", "view")
  const canViewDoctors = usePermission("doctors", "view")
  const canManageRoles = usePermission("roles", "manage")
  const canManageUsers = usePermission("users", "manage")
  const canManageCatalog = usePermission("catalog", "manage")
  const canManageRules = usePermission("rules", "manage")
  const canManageReferenceData = usePermission("reference_data", "manage")
  const canManageFinance = usePermission("finance", "manage")
  const canManageLabSettings = usePermission("lab_settings", "manage")
  const canViewAudit = usePermission("audit", "view")
  const canManageReports = usePermission("reports", "manage_templates")

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setOpen((current) => !current)
      }
    }

    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedQuery(query.trim())
    }, 250)

    return () => window.clearTimeout(timeout)
  }, [query])

  const navigationItems = useMemo<SearchItem[]>(
    () =>
      [
        {
          id: "nav-dashboard",
          title: "Tableau de bord",
          subtitle: "Vue d'ensemble du laboratoire",
          href: "/",
          group: "Navigation",
          icon: Home,
          keywords: ["accueil", "dashboard"],
          allowed: true,
        },
        {
          id: "nav-orders",
          title: "Demandes",
          subtitle: "Créer et suivre les dossiers patients",
          href: "/orders",
          group: "Navigation",
          icon: ClipboardList,
          keywords: ["ordres", "dossiers"],
          allowed: canViewOrders || canCreateOrders,
        },
        {
          id: "nav-specimens",
          title: "Prélèvements",
          subtitle: "Suivi des échantillons",
          href: "/specimens",
          group: "Navigation",
          icon: TestTube,
          keywords: ["echantillons", "specimens"],
          allowed: canViewSpecimens,
        },
        {
          id: "nav-results",
          title: "Résultats",
          subtitle: "Saisie, validation et lecture des résultats",
          href: "/results",
          group: "Navigation",
          icon: Microscope,
          keywords: ["analyses", "validation"],
          allowed: canViewResults,
        },
        {
          id: "nav-reagents",
          title: "Réactifs",
          subtitle: "Stocks et alertes de réactifs",
          href: "/reagents",
          group: "Navigation",
          icon: PackageSearch,
          keywords: ["stock", "inventaire"],
          allowed: canViewReagents,
        },
        {
          id: "nav-invoices",
          title: "Factures",
          subtitle: "Facturation et paiements",
          href: "/invoices",
          group: "Navigation",
          icon: ReceiptText,
          keywords: ["finance", "paiements"],
          allowed: canViewInvoices,
        },
        {
          id: "nav-commissions",
          title: "Commissions",
          subtitle: "Paiements des commissions médecins",
          href: "/commissions/payments",
          group: "Navigation",
          icon: HandCoins,
          keywords: ["medecins", "paiements"],
          allowed: canViewCommissions,
        },
        {
          id: "nav-patients",
          title: "Patients",
          subtitle: "Dossiers administratifs patients",
          href: "/patients",
          group: "Navigation",
          icon: UserRound,
          keywords: ["personnes"],
          allowed: canViewPatients,
        },
        {
          id: "nav-doctors",
          title: "Médecins",
          subtitle: "Prescripteurs et contacts",
          href: "/doctors",
          group: "Navigation",
          icon: Stethoscope,
          keywords: ["prescripteurs"],
          allowed: canViewDoctors,
        },
        {
          id: "nav-configurations",
          title: "Configurations",
          subtitle: "Paramètres du système",
          href: "/configurations",
          group: "Navigation",
          icon: Settings2,
          keywords: ["parametres"],
          allowed: true,
        },
        {
          id: "config-audit",
          title: "Journal d'audit",
          subtitle: "Changements et événements de sécurité",
          href: "/configurations/audit",
          group: "Configurations",
          icon: ScrollText,
          allowed: canViewAudit,
        },
        {
          id: "config-laboratoire",
          title: "Laboratoire",
          subtitle: "Identité, logo et coordonnées",
          href: "/configurations/laboratoire",
          group: "Configurations",
          icon: Building2,
          allowed: canManageLabSettings,
        },
        {
          id: "config-rapports",
          title: "Rapports",
          subtitle: "En-têtes, rendus cliniques et pieds de page",
          href: "/configurations/rapports",
          group: "Configurations",
          icon: FileText,
          allowed: canManageReports,
        },
        {
          id: "config-roles",
          title: "Rôles",
          subtitle: "Rôles et permissions",
          href: "/configurations/roles",
          group: "Configurations",
          icon: ShieldCheck,
          allowed: canManageRoles,
        },
        {
          id: "config-permissions",
          title: "Permissions",
          subtitle: "Permissions granulaires",
          href: "/configurations/permissions",
          group: "Configurations",
          icon: KeyRound,
          allowed: canManageRoles,
        },
        {
          id: "config-users",
          title: "Utilisateurs",
          subtitle: "Comptes et assignation des rôles",
          href: "/configurations/users",
          group: "Configurations",
          icon: Users,
          allowed: canManageUsers,
        },
        {
          id: "config-catalogue",
          title: "Catalogue",
          subtitle: "Tests, panels, prélèvements et tarifs",
          href: "/configurations/catalogue",
          group: "Configurations",
          icon: TestTube,
          allowed: canManageCatalog,
        },
        {
          id: "config-analytes",
          title: "Analytes",
          subtitle: "Analytes, types de résultat et formules",
          href: "/configurations/analytes",
          group: "Configurations",
          icon: Microscope,
          allowed: canManageCatalog,
        },
        {
          id: "config-categories",
          title: "Catégories",
          subtitle: "Regroupement et ordre du catalogue",
          href: "/configurations/categories",
          group: "Configurations",
          icon: FolderTree,
          allowed: canManageCatalog,
        },
        {
          id: "config-validation-rules",
          title: "Règles de validation",
          subtitle: "Plages, seuils critiques et delta checks",
          href: "/configurations/regles-validation",
          group: "Configurations",
          icon: ShieldCheck,
          allowed: canManageRules,
        },
        {
          id: "config-automation-rules",
          title: "Règles automatisées",
          subtitle: "Cohérence et règles réflexes",
          href: "/configurations/regles-automatisees",
          group: "Configurations",
          icon: Settings2,
          allowed: canManageRules,
        },
        {
          id: "config-titles",
          title: "Titres",
          subtitle: "Civilités des patients et médecins",
          href: "/configurations/titres",
          group: "Configurations",
          icon: Tag,
          allowed: canManageReferenceData,
        },
        {
          id: "config-units",
          title: "Unités",
          subtitle: "Unités de mesure des analytes",
          href: "/configurations/unites",
          group: "Configurations",
          icon: Ruler,
          allowed: canManageReferenceData,
        },
        {
          id: "config-contexts",
          title: "Contextes patient",
          subtitle: "Contextes cliniques",
          href: "/configurations/contexts-patient",
          group: "Configurations",
          icon: UserRound,
          allowed: canManageReferenceData,
        },
        {
          id: "config-payment-methods",
          title: "Méthodes de paiement",
          subtitle: "Modes de paiement acceptés",
          href: "/configurations/methodes-paiement",
          group: "Configurations",
          icon: CreditCard,
          allowed: canManageReferenceData,
        },
        {
          id: "config-rejection-reasons",
          title: "Motifs de rejet",
          subtitle: "Motifs de rejet des prélèvements",
          href: "/configurations/motifs-rejet",
          group: "Configurations",
          icon: XCircle,
          allowed: canManageReferenceData,
        },
        {
          id: "config-specimen-types",
          title: "Types de prélèvement",
          subtitle: "Types d'échantillons acceptés",
          href: "/configurations/types-prelevement",
          group: "Configurations",
          icon: TestTube,
          allowed: canManageReferenceData,
        },
        {
          id: "config-insurers",
          title: "Assureurs",
          subtitle: "Compagnies d'assurance",
          href: "/configurations/assureurs",
          group: "Configurations",
          icon: Building2,
          allowed: canManageReferenceData,
        },
        {
          id: "config-finance",
          title: "Finance",
          subtitle: "Remises et commissions",
          href: "/configurations/finance",
          group: "Configurations",
          icon: WalletCards,
          allowed: canManageFinance,
        },
        {
          id: "config-insurance-prices",
          title: "Tarifs assurance",
          subtitle: "Prix des tests par assureur",
          href: "/configurations/tarifs-assurance",
          group: "Configurations",
          icon: BadgeDollarSign,
          allowed: canManageFinance,
        },
      ].filter((item) => item.allowed),
    [
      canCreateOrders,
      canManageCatalog,
      canManageFinance,
      canManageLabSettings,
      canManageReferenceData,
      canManageReports,
      canManageRoles,
      canManageRules,
      canManageUsers,
      canViewAudit,
      canViewCommissions,
      canViewDoctors,
      canViewInvoices,
      canViewOrders,
      canViewPatients,
      canViewReagents,
      canViewResults,
      canViewSpecimens,
    ],
  )

  const filteredNavigationItems = useMemo(
    () => navigationItems.filter((item) => matches(item, query)),
    [navigationItems, query],
  )

  const businessSearchQuery = useQuery({
    queryKey: ["global-search", debouncedQuery],
    queryFn: () =>
      GlobalSearchService.readGlobalSearch({
        query: debouncedQuery,
        limit: 5,
      }),
    enabled: debouncedQuery.length >= 2,
    staleTime: 20_000,
  })

  const groupedBusinessResults = useMemo(() => {
    const groups = new Map<string, GlobalSearchResultPublic[]>()

    for (const result of businessSearchQuery.data?.data ?? []) {
      const label = RESULT_GROUP_LABELS[result.kind] ?? result.kind
      groups.set(label, [...(groups.get(label) ?? []), result])
    }

    return Array.from(groups.entries())
  }, [businessSearchQuery.data?.data])

  const hasResults =
    filteredNavigationItems.length > 0 || groupedBusinessResults.length > 0
  const showTypeMore = query.trim().length > 0 && query.trim().length < 2
  const visibleNavigationItems = filteredNavigationItems.filter(
    (item) => item.group === "Navigation",
  )
  const visibleConfigurationItems = filteredNavigationItems.filter(
    (item) => item.group === "Configurations",
  )

  function openResult(href: string) {
    setOpen(false)
    navigate({ to: href })
  }

  function renderItem(item: SearchItem) {
    const Icon = item.icon

    return (
      <CommandItem
        key={item.id}
        value={item.id}
        onSelect={() => openResult(item.href)}
        className="min-h-11 cursor-pointer gap-3 px-3 py-2"
      >
        <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
          <Icon className="size-3.5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium">{item.title}</span>
          {item.subtitle && (
            <span className="block truncate text-[0.68rem] text-muted-foreground">
              {item.subtitle}
            </span>
          )}
        </span>
        {item.badge && (
          <CommandShortcut className="normal-case tracking-normal">
            {item.badge}
          </CommandShortcut>
        )}
      </CommandItem>
    )
  }

  function renderBusinessResult(result: GlobalSearchResultPublic) {
    const Icon = RESULT_ICONS[result.kind] ?? Search

    return (
      <CommandItem
        key={`${result.kind}-${result.record_id ?? result.href}`}
        value={`${result.kind}-${result.record_id ?? result.href}`}
        onSelect={() => openResult(result.href)}
        className="min-h-11 cursor-pointer gap-3 px-3 py-2"
      >
        <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
          <Icon className="size-3.5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium">{result.title}</span>
          {result.subtitle && (
            <span className="block truncate text-[0.68rem] text-muted-foreground">
              {result.subtitle}
            </span>
          )}
        </span>
        {result.badge && (
          <CommandShortcut className="normal-case tracking-normal">
            {result.badge}
          </CommandShortcut>
        )}
      </CommandItem>
    )
  }

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        className={cn(
          "min-w-0 justify-start gap-2 border-border/80 bg-card/75 text-muted-foreground shadow-none",
          "active:scale-[0.98] sm:w-56 md:w-72 lg:w-80",
        )}
      >
        <Search className="size-3.5 shrink-0" />
        <span className="hidden truncate text-left font-normal sm:block">
          Rechercher...
        </span>
        <kbd className="ml-auto hidden rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[0.6rem] font-medium text-muted-foreground sm:inline-flex">
          {shortcutLabel}
        </kbd>
      </Button>

      <CommandDialog
        open={open}
        onOpenChange={setOpen}
        title="Recherche globale"
        description="Rechercher une page, une demande, un patient ou un dossier."
        className="top-[18%] max-w-2xl translate-y-0"
        showCloseButton
      >
        <Command shouldFilter={false}>
          <CommandInput
            value={query}
            onValueChange={setQuery}
            placeholder="Rechercher une page, un patient, une demande..."
          />
          <CommandList className="max-h-[min(28rem,70vh)]">
            {visibleNavigationItems.length > 0 && (
              <CommandGroup heading="Navigation">
                {visibleNavigationItems.map(renderItem)}
              </CommandGroup>
            )}

            {visibleConfigurationItems.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup heading="Configurations">
                  {visibleConfigurationItems.map(renderItem)}
                </CommandGroup>
              </>
            )}

            {businessSearchQuery.isFetching && debouncedQuery.length >= 2 && (
              <>
                <CommandSeparator />
                <div className="px-3 py-4 text-center text-xs text-muted-foreground">
                  Recherche...
                </div>
              </>
            )}

            {businessSearchQuery.isError && (
              <>
                <CommandSeparator />
                <div className="px-3 py-4 text-center text-xs text-destructive">
                  Impossible de charger les résultats.
                </div>
              </>
            )}

            {groupedBusinessResults.map(([label, results]) => (
              <CommandGroup key={label} heading={label}>
                {results.map(renderBusinessResult)}
              </CommandGroup>
            ))}

            {showTypeMore && (
              <div className="px-3 py-4 text-center text-xs text-muted-foreground">
                Saisissez au moins 2 caractères pour rechercher les dossiers.
              </div>
            )}

            {!hasResults &&
              !businessSearchQuery.isFetching &&
              !showTypeMore && (
                <CommandEmpty>Aucun résultat trouvé.</CommandEmpty>
              )}
          </CommandList>
        </Command>
      </CommandDialog>
    </>
  )
}
