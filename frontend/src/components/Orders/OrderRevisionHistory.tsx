import { useQuery } from "@tanstack/react-query"
import { History } from "lucide-react"

import { OrdersService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDateTime, formatMoney } from "./utils"

type RevisionEffects = {
  superseded_item_count?: number
  reused_collected_specimen_count?: number
  created_pending_specimen_count?: number
  voided_report_count?: number
  invoice_reissued?: boolean
  customer_credit?: string
  commission_adjustment?: string
}

export function OrderRevisionHistory({ orderId }: { orderId: string }) {
  const query = useQuery({
    queryKey: ["order-revisions", orderId],
    queryFn: () => OrdersService.readOrderRevisions({ id: orderId }),
  })

  if (query.isLoading) return <Skeleton className="h-28 w-full" />
  if (!query.data?.count) return null

  return (
    <section className="overflow-hidden rounded-md border">
      <div className="flex items-center gap-2 border-b bg-muted/20 px-4 py-3 font-semibold">
        <History className="size-4" />
        Historique des révisions
      </div>
      <div className="divide-y">
        {query.data.data.map((revision) => {
          const effects = revision.effects as RevisionEffects
          return (
            <article key={revision.id} className="space-y-2 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">
                  Révision {revision.revision_number}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {formatDateTime(revision.created_at)} par{" "}
                  {revision.performed_by_name ?? "Utilisateur"}
                </span>
              </div>
              <p className="text-sm">{revision.correction_reason}</p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                {!!effects.superseded_item_count && (
                  <span>
                    {effects.superseded_item_count} examen(s) remplacé(s)
                  </span>
                )}
                {!!effects.reused_collected_specimen_count && (
                  <span>
                    {effects.reused_collected_specimen_count} prélèvement(s)
                    réutilisé(s)
                  </span>
                )}
                {!!effects.created_pending_specimen_count && (
                  <span>
                    {effects.created_pending_specimen_count} prélèvement(s) à
                    effectuer
                  </span>
                )}
                {!!effects.voided_report_count && (
                  <span>
                    {effects.voided_report_count} rapport(s) annulé(s)
                  </span>
                )}
                {effects.invoice_reissued && <span>Facture réémise</span>}
                {Number(effects.customer_credit ?? 0) > 0 && (
                  <span>
                    Avoir à rembourser : {formatMoney(effects.customer_credit!)}
                  </span>
                )}
                {Number(effects.commission_adjustment ?? 0) !== 0 && (
                  <span>
                    Ajustement commission :{" "}
                    {formatMoney(effects.commission_adjustment!)}
                  </span>
                )}
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
