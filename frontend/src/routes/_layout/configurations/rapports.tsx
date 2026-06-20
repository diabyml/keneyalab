import { createFileRoute, redirect } from "@tanstack/react-router"

import { ReportDesignerView } from "@/components/Reports/ReportDesignerView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/rapports")({
  component: ReportDesignerView,
  beforeLoad: async () => {
    if (!(await ensurePermission("reports", "manage_templates"))) {
      throw redirect({ to: "/configurations" })
    }
  },
  head: () => ({
    meta: [{ title: "Conception des rapports - KeneyaLab" }],
  }),
})
