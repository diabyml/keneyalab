import { createFileRoute, redirect } from "@tanstack/react-router"

import { ReportViewer } from "@/components/Reports/ReportViewer"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/orders/$orderId/report")({
  component: ReportPage,
  beforeLoad: async () => {
    if (!(await ensurePermission("reports", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({ meta: [{ title: "Compte rendu - KeneyaLab" }] }),
})

function ReportPage() {
  const { orderId } = Route.useParams()
  return <ReportViewer orderId={orderId} />
}
