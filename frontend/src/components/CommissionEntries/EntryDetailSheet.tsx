import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { useState } from "react"

import { DoctorCommissionEntriesService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { usePermission } from "@/hooks/usePermission"
import { AdjustmentDialog } from "./AdjustmentDialog"
import {
  formatDateTime,
  formatMoney,
  formatRate,
  PAYOUT_STATUS_LABELS,
} from "./utils"

interface EntryDetailSheetProps {
  entryId: string | null
  onOpenChange: (open: boolean) => void
}

export function EntryDetailSheet({
  entryId,
  onOpenChange,
}: EntryDetailSheetProps) {
  const canAdjust = usePermission("commissions", "adjust")
  const [adjustmentOpen, setAdjustmentOpen] = useState(false)
  const query = useQuery({
    queryKey: ["commission-entry", entryId],
    queryFn: () => DoctorCommissionEntriesService.readEntry({ id: entryId! }),
    enabled: entryId !== null,
  })
  const entry = query.data

  return (
    <>
      <Sheet open={entryId !== null} onOpenChange={onOpenChange}>
        <SheetContent className="w-[calc(100vw-1rem)] overflow-hidden p-0 sm:max-w-2xl lg:max-w-3xl">
          <SheetHeader className="border-b pr-12">
            <SheetTitle>
              {entry ? `Commission ${entry.accession_number}` : "Commission"}
            </SheetTitle>
            <SheetDescription>
              {entry
                ? `${entry.doctor_name} · ${entry.patient_name}`
                : "Chargement du détail…"}
            </SheetDescription>
          </SheetHeader>

          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            {query.isLoading && (
              <div className="space-y-3">
                {Array.from({ length: 8 }).map((_, index) => (
                  <Skeleton key={index} className="h-12 w-full" />
                ))}
              </div>
            )}

            {entry && (
              <div className="space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">
                      {PAYOUT_STATUS_LABELS[entry.payout_status ?? "pending"]}
                    </Badge>
                    <Badge variant="secondary">
                      {entry.adjustment_count} ajustement
                      {entry.adjustment_count !== 1 && "s"}
                    </Badge>
                  </div>
                  {canAdjust && (
                    <Button onClick={() => setAdjustmentOpen(true)}>
                      <Plus className="size-4" />
                      Ajouter un ajustement
                    </Button>
                  )}
                </div>

                <Card className="grid gap-4 p-4 sm:grid-cols-2">
                  <DetailItem
                    label="Demande"
                    value={
                      <Link
                        to="/orders/$orderId"
                        params={{ orderId: entry.order_id }}
                        className="text-primary hover:underline"
                      >
                        {entry.accession_number}
                      </Link>
                    }
                  />
                  <DetailItem label="Facture" value={entry.invoice_number} />
                  <DetailItem label="Médecin" value={entry.doctor_name} />
                  <DetailItem
                    label="Patient"
                    value={
                      <Link
                        to="/patients/$patientId"
                        params={{ patientId: entry.patient_id }}
                        className="text-primary hover:underline"
                      >
                        {entry.patient_name}
                      </Link>
                    }
                  />
                  <DetailItem
                    label="Net assuré"
                    value={formatMoney(entry.insured_net_amount ?? 0)}
                    detail={`Taux ${formatRate(entry.insured_rate_applied)} · Commission ${formatMoney(entry.insured_commission_amount ?? 0)}`}
                  />
                  <DetailItem
                    label="Net non assuré"
                    value={formatMoney(entry.non_insured_net_amount ?? 0)}
                    detail={`Taux ${formatRate(entry.non_insured_rate_applied)} · Commission ${formatMoney(entry.non_insured_commission_amount ?? 0)}`}
                  />
                </Card>

                <div className="divide-y rounded-md border">
                  <Metric
                    label="Commission calculée"
                    value={entry.commission_amount}
                  />
                  <Metric
                    label="Ajustements ouverts"
                    value={entry.unsettled_adjustments}
                  />
                  <Metric
                    label="Solde ouvert"
                    value={entry.outstanding_amount}
                  />
                </div>

                <div className="space-y-3">
                  <h3 className="font-semibold">Historique des ajustements</h3>
                  {(entry.adjustments ?? []).length === 0 ? (
                    <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
                      Aucun ajustement enregistré.
                    </div>
                  ) : (
                    (entry.adjustments ?? []).map((adjustment) => (
                      <Card key={adjustment.id} className="space-y-3 p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="font-medium">
                              {adjustment.source === "manual"
                                ? "Ajustement manuel"
                                : "Révision de demande"}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {adjustment.created_by_name ??
                                "Généré automatiquement"}{" "}
                              · {formatDateTime(adjustment.created_at)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold tabular-nums">
                              {formatMoney(adjustment.amount)}
                            </div>
                            <Badge
                              variant={
                                adjustment.is_settled ? "secondary" : "outline"
                              }
                            >
                              {adjustment.is_settled ? "Soldé" : "À régler"}
                            </Badge>
                          </div>
                        </div>
                        <p className="text-sm">{adjustment.reason}</p>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {entryId && (
        <AdjustmentDialog
          entryId={entryId}
          open={adjustmentOpen}
          onOpenChange={setAdjustmentOpen}
        />
      )}
    </>
  )
}

function DetailItem({
  label,
  value,
  detail,
}: {
  label: string
  value: React.ReactNode
  detail?: string
}) {
  return (
    <div>
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="mt-1 font-medium">{value}</div>
      {detail && (
        <div className="mt-1 text-xs text-muted-foreground">{detail}</div>
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold tabular-nums">
        {formatMoney(value)}
      </div>
    </div>
  )
}
