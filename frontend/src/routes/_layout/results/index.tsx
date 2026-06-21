import { createFileRoute } from "@tanstack/react-router"

import { PageHeader } from "@/components/Common/PageHeader"
import { ResultsView } from "@/components/Results/ResultsView"

export const Route = createFileRoute("/_layout/results/")({
  component: ResultsPage,
  head: () => ({ meta: [{ title: "Résultats - KeneyaLab" }] }),
})

function ResultsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Phase analytique"
        title="Résultats"
        description="Saisir, contrôler et vérifier les résultats d'analyses"
      />
      <ResultsView />
    </div>
  )
}
