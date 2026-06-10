import { createFileRoute } from "@tanstack/react-router"

import { InvoiceDetailView } from "@/components/Invoices/InvoiceDetailView"

export const Route = createFileRoute("/_layout/invoices/$invoiceId")({
  component: RouteComponent,
  head: () => ({ meta: [{ title: "Détail facture - KeneyaLab" }] }),
})

function RouteComponent() {
  const { invoiceId } = Route.useParams()
  return <InvoiceDetailView invoiceId={invoiceId} />
}
