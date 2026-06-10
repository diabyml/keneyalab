import { createFileRoute, redirect } from "@tanstack/react-router"

import { CommissionsLayout } from "@/components/CommissionEntries/CommissionsLayout"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/commissions")({
  component: CommissionsLayout,
  beforeLoad: async () => {
    if (!(await ensurePermission("commissions", "view"))) {
      throw redirect({ to: "/" })
    }
  },
})
