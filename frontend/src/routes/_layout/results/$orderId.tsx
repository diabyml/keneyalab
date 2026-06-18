import { createFileRoute } from "@tanstack/react-router"

import { ResultWorkspaceView } from "@/components/Results/ResultWorkspaceView"

export const Route = createFileRoute("/_layout/results/$orderId")({
  component: ResultWorkspacePage,
  head: () => ({ meta: [{ title: "Saisie des résultats - KeneyaLab" }] }),
})

function ResultWorkspacePage() {
  const { orderId } = Route.useParams()
  return <ResultWorkspaceView orderId={orderId} />
}
