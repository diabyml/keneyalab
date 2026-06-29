import { createFileRoute, redirect } from "@tanstack/react-router"
import { FlaskConical } from "lucide-react"

import { PageHeader } from "@/components/Common/PageHeader"
import { ReagentsView } from "@/components/Reagents/ReagentsView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute("/_layout/reagents")({
  component: ReagentsPage,
  beforeLoad: async () => {
    if (!(await ensurePermission("reagents", "view"))) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({ meta: [{ title: "Réactifs - KeneyaLab" }] }),
})

function ReagentsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Stock laboratoire"
        title="Réactifs"
        description="Suivre les lots, les mouvements, les seuils et les dates d'expiration"
        icon={FlaskConical}
      />
      <ReagentsView />
    </div>
  )
}
