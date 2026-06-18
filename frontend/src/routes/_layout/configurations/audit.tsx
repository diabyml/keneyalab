import { createFileRoute, redirect } from "@tanstack/react-router"

import { AuditLogsView } from "@/components/AuditLogs/AuditLogsView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/configurations/audit")({
  component: AuditLogsView,
  beforeLoad: async () => {
    if (!(await ensurePermission("audit", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Journal d'audit - KeneyaLab" }],
  }),
})
