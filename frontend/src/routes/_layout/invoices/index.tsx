import { createFileRoute } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
import { InvoicesView } from "@/components/Invoices/InvoicesView"

export const Route = createFileRoute("/_layout/invoices/")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Factures - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Gestion financière"
        title="Factures"
        description="Suivre les encaissements, remboursements et corrections"
      />
      <InvoicesView />
    </div>
  )
}
