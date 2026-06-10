import { Link, Outlet, useRouterState } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"

export function CommissionsLayout() {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const paymentsActive = pathname.startsWith("/commissions/payments")

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Commissions</h1>
        <p className="text-muted-foreground">
          Suivi des écritures, ajustements et règlements médecins
        </p>
      </div>
      <div className="flex gap-2 border-b pb-3">
        <Button variant={paymentsActive ? "secondary" : "ghost"} asChild>
          <Link to="/commissions/payments">Paiements</Link>
        </Button>
        <Button variant={paymentsActive ? "ghost" : "secondary"} asChild>
          <Link to="/commissions/entries">Écritures</Link>
        </Button>
      </div>
      <Outlet />
    </div>
  )
}
