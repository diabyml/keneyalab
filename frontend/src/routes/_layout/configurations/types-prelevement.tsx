import { createFileRoute, redirect } from "@tanstack/react-router"
import { TypesPrelevementView } from "@/components/TypesPrelevement/TypesPrelevementView"
import { ensurePermission } from "@/hooks/usePermission"

export const Route = createFileRoute(
  "/_layout/configurations/types-prelevement",
)({
  component: RouteComponent,
  beforeLoad: async () => {
    if (!(await ensurePermission("reference_data", "manage")))
      throw redirect({ to: "/configurations" })
  },
  head: () => ({ meta: [{ title: "Types de prélèvement - KeneyaLab" }] }),
})

function RouteComponent() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Types de prélèvement
        </h1>
        <p className="text-muted-foreground">
          Gérer les types de prélèvement (Sang veineux, Urine, etc.)
        </p>
      </div>
      <TypesPrelevementView />
    </div>
  )
}
