import { useQuery } from "@tanstack/react-query"
import {
  ClipboardList,
  FlaskConical,
  HandCoins,
  Home,
  Microscope,
  ReceiptText,
  Settings2,
  Stethoscope,
  UserRound,
} from "lucide-react"

import { CriticalNotificationsService } from "@/client"
import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { usePermission } from "@/hooks/usePermission"
import { type Item, Main } from "./Main"
import { User } from "./User"

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const canViewItems = usePermission("items", "view")
  const canViewPatients = usePermission("patients", "view")
  const canViewDoctors = usePermission("doctors", "view")
  const canViewOrders = usePermission("orders", "view")
  const canCreateOrders = usePermission("orders", "create")
  const canViewSpecimens = usePermission("specimens", "view")
  const canViewResults = usePermission("results", "view")
  const canViewCritical = usePermission("critical_notifications", "view")
  const canViewInvoices = usePermission("invoices", "view")
  const canViewCommissions = usePermission("commissions", "view")
  const criticalCountQuery = useQuery({
    queryKey: ["critical-notifications", "unacknowledged-count"],
    queryFn: () => CriticalNotificationsService.readUnacknowledgedCount(),
    enabled: canViewCritical,
    refetchInterval: 30_000,
  })

  const items: Item[] = [{ icon: Home, title: "Tableau de bord", path: "/" }]

  if (canViewOrders || canCreateOrders) {
    items.push({ icon: ClipboardList, title: "Demandes", path: "/orders" })
  }

  if (canViewSpecimens) {
    items.push({
      icon: FlaskConical,
      title: "Prélèvements",
      path: "/specimens",
    })
  }

  if (canViewResults) {
    items.push({
      icon: Microscope,
      title: "Résultats",
      path: "/results",
      badge: criticalCountQuery.data?.count,
    })
  }

  if (canViewInvoices) {
    items.push({ icon: ReceiptText, title: "Factures", path: "/invoices" })
  }

  if (canViewCommissions) {
    items.push({
      icon: HandCoins,
      title: "Commissions",
      path: "/commissions/payments",
    })
  }

  if (canViewPatients) {
    items.push({ icon: UserRound, title: "Patients", path: "/patients" })
  }

  if (canViewDoctors) {
    items.push({ icon: Stethoscope, title: "Médecins", path: "/doctors" })
  }

  if (canViewItems) {
    // items.push({ icon: Briefcase, title: "Tâches", path: "/items" })
  }

  items.push({
    icon: Settings2,
    title: "Configurations",
    path: "/configurations",
  })

  return (
    <Sidebar collapsible="icon" className="border-sidebar-border/70">
      <SidebarHeader className="border-b border-sidebar-border/70 px-3 py-4 group-data-[collapsible=icon]:items-center group-data-[collapsible=icon]:px-0">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter className="gap-1 border-t border-sidebar-border/70 p-2">
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
