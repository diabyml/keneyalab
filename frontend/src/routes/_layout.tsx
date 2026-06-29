import {
  createFileRoute,
  Outlet,
  redirect,
  useRouterState,
} from "@tanstack/react-router"
import { Activity, FlaskConical } from "lucide-react"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const section =
    [
      ["/orders", "Demandes"],
      ["/specimens", "Prélèvements"],
      ["/results", "Résultats"],
      ["/reagents", "Réactifs"],
      ["/invoices", "Facturation"],
      ["/commissions", "Commissions"],
      ["/patients", "Patients"],
      ["/doctors", "Médecins"],
      ["/configurations", "Configurations"],
      ["/user-account", "Compte utilisateur"],
    ].find(([path]) => pathname.startsWith(path))?.[1] ?? "Tableau de bord"

  return (
    <SidebarProvider className="h-svh overflow-hidden">
      <AppSidebar />
      <SidebarInset className="min-w-0">
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border/80 bg-background/90 px-4 backdrop-blur-lg">
          <div className="flex min-w-0 items-center gap-3">
            <SidebarTrigger className="-ml-1 text-muted-foreground" />
            <div className="h-5 w-px bg-border" />
            <div className="flex min-w-0 items-center gap-2">
              <FlaskConical className="size-4 shrink-0 text-primary" />
              <span className="truncate font-heading text-sm font-semibold">
                {section}
              </span>
            </div>
          </div>
          <div className="hidden items-center gap-2 rounded-full border border-success/20 bg-success/8 px-2.5 py-1 text-[0.65rem] font-semibold text-success sm:flex">
            <Activity className="size-3.5" />
            Système opérationnel
          </div>
        </header>
        <main className="scrollbar-hide flex-1 overflow-y-auto p-4 sm:p-5 lg:p-6">
          <div className="mx-auto w-full max-w-[1600px]">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
