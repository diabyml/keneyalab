import { createFileRoute } from "@tanstack/react-router"

import { ResultsView } from "@/components/Results/ResultsView"

export const Route = createFileRoute("/_layout/results/")({
  component: ResultsPage,
  head: () => ({ meta: [{ title: "Résultats - KeneyaLab" }] }),
})

function ResultsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Résultats</h1>
        <p className="text-muted-foreground">
          Saisir, contrôler et vérifier les résultats d'analyses
        </p>
      </div>
      <ResultsView />
    </div>
  )
}
