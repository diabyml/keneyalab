import { createFileRoute } from "@tanstack/react-router"

import { InvoicesView } from "@/components/Invoices/InvoicesView"

export const Route = createFileRoute("/_layout/invoices/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Factures - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Factures</h1>
        <p className="text-muted-foreground">
          Suivre les encaissements, remboursements et corrections
        </p>
      </div>
      <InvoicesView />
    </div>
  )
}
