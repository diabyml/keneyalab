import { createFileRoute } from "@tanstack/react-router"

import { CommissionEntriesView } from "@/components/CommissionEntries/CommissionEntriesView"

export const Route = createFileRoute("/_layout/commissions/entries")({
  component: CommissionEntriesView,
  head: () => ({
    meta: [{ title: "Écritures de commissions - KeneyaLab" }],
  }),
})
