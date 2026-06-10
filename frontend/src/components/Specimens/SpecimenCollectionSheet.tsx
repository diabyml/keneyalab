import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { AlertTriangle, Ban, Clock, TestTube } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import type { OrderSpecimenDetailPublic } from "@/client"
import { SpecimensService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { formatDateTime, formatMoney } from "@/components/Orders/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { SPECIMEN_STATUS_LABELS, toLocalDateTimeInput } from "./utils"

interface SpecimenCollectionSheetProps {
  orderId: string | null
  onOpenChange: (open: boolean) => void
}

export function SpecimenCollectionSheet({
  orderId,
  onOpenChange,
}: SpecimenCollectionSheetProps) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const canCollect = usePermission("specimens", "collect")
  const canReject = usePermission("specimens", "reject")
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [collectionTime, setCollectionTime] = useState(toLocalDateTimeInput())
  const [rejecting, setRejecting] = useState<OrderSpecimenDetailPublic | null>(
    null,
  )

  const workspaceQuery = useQuery({
    queryKey: ["specimen-workspace", orderId],
    queryFn: () =>
      SpecimensService.readCollectionWorkspace({ orderId: orderId! }),
    enabled: orderId !== null,
  })
  const pending = useMemo(
    () =>
      (workspaceQuery.data?.specimens ?? []).filter(
        (item) => item.is_active_attempt && item.status === "pending",
      ),
    [workspaceQuery.data],
  )

  useEffect(() => {
    if (!orderId) return
    setSelectedIds(new Set())
    setCollectionTime(toLocalDateTimeInput())
    setRejecting(null)
  }, [orderId])

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["specimen-workspace", orderId] })
    queryClient.invalidateQueries({ queryKey: ["specimen-queue"] })
    queryClient.invalidateQueries({ queryKey: ["order", orderId] })
  }
  const collectMutation = useMutation({
    mutationFn: () =>
      SpecimensService.collectSpecimens({
        requestBody: {
          specimen_ids: [...selectedIds],
          collection_time: new Date(collectionTime).toISOString(),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Prélèvement enregistré")
      setSelectedIds(new Set())
      refresh()
    },
    onError: handleError.bind(showErrorToast),
  })

  const toggle = (id: string) => {
    setSelectedIds((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }
  const allSelected =
    pending.length > 0 && pending.every((item) => selectedIds.has(item.id))

  const active = (workspaceQuery.data?.specimens ?? []).filter(
    (item) => item.is_active_attempt,
  )
  const history = (workspaceQuery.data?.specimens ?? []).filter(
    (item) => !item.is_active_attempt,
  )
  const hasBalance = Number(workspaceQuery.data?.balance_due ?? 0) > 0

  return (
    <>
      <Sheet open={orderId !== null} onOpenChange={onOpenChange}>
        <SheetContent className="w-[calc(100vw-1rem)] overflow-hidden p-0 sm:max-w-xl">
          <SheetHeader className="border-b pr-12">
            <SheetTitle>
              {workspaceQuery.data?.accession_number ?? "Prélèvements"}
            </SheetTitle>
            <SheetDescription>
              {workspaceQuery.data
                ? `${workspaceQuery.data.patient_name} · ${workspaceQuery.data.patient_identifier}`
                : "Chargement de la demande…"}
            </SheetDescription>
          </SheetHeader>

          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
            {workspaceQuery.isLoading && (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-20 w-full" />
                ))}
              </div>
            )}
            {hasBalance && (
              <div className="flex gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>
                  Solde restant :{" "}
                  {formatMoney(workspaceQuery.data!.balance_due)}. Le
                  prélèvement reste autorisé.
                </span>
              </div>
            )}
            {canCollect && pending.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="collection-time">Heure de prélèvement</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCollectionTime(toLocalDateTimeInput())}
                  >
                    <Clock className="size-4" />
                    Maintenant
                  </Button>
                </div>
                <Input
                  id="collection-time"
                  type="datetime-local"
                  value={collectionTime}
                  onChange={(event) =>
                    setCollectionTime(event.currentTarget.value)
                  }
                />
                <div className="flex items-center gap-2 py-2">
                  <Checkbox
                    id="select-all-pending-specimens"
                    checked={allSelected}
                    onCheckedChange={() =>
                      setSelectedIds(
                        allSelected
                          ? new Set()
                          : new Set(pending.map((item) => item.id)),
                      )
                    }
                  />
                  <Label htmlFor="select-all-pending-specimens">
                    Sélectionner tous les prélèvements en attente
                  </Label>
                </div>
              </div>
            )}

            {active.map((specimen) => (
              <div key={specimen.id} className="rounded-md border p-3">
                <div className="flex items-start gap-3">
                  {canCollect && specimen.status === "pending" && (
                    <Checkbox
                      className="mt-1"
                      checked={selectedIds.has(specimen.id)}
                      onCheckedChange={() => toggle(specimen.id)}
                      aria-label={`Sélectionner ${specimen.specimen_type_name}`}
                    />
                  )}
                  <span
                    className="mt-1 size-3 shrink-0 rounded-full border"
                    style={{
                      backgroundColor:
                        specimen.specimen_type_color ?? "transparent",
                    }}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">
                        {specimen.specimen_type_name}
                      </span>
                      <Badge variant="outline">
                        {SPECIMEN_STATUS_LABELS[specimen.status ?? "pending"]}
                      </Badge>
                      {(specimen.attempt_number ?? 1) > 1 && (
                        <Badge variant="secondary">
                          Tentative {specimen.attempt_number}
                        </Badge>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {specimen.required_volume_ml
                        ? `${Number(specimen.required_volume_ml).toFixed(2)} ml`
                        : "Volume non précisé"}
                      {specimen.collection_instructions
                        ? ` · ${specimen.collection_instructions}`
                        : ""}
                    </p>
                    {specimen.collection_time && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Prélevé le {formatDateTime(specimen.collection_time)}
                        {specimen.collected_by_name
                          ? ` par ${specimen.collected_by_name}`
                          : ""}
                      </p>
                    )}
                  </div>
                  {canReject &&
                    ["pending", "collected"].includes(
                      specimen.status ?? "pending",
                    ) && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setRejecting(specimen)}
                        aria-label="Rejeter le prélèvement"
                      >
                        <Ban className="size-4" />
                      </Button>
                    )}
                </div>
              </div>
            ))}

            {history.length > 0 && (
              <section className="space-y-2 border-t pt-4">
                <h3 className="text-sm font-semibold">
                  Historique des tentatives
                </h3>
                {history.map((specimen) => (
                  <div
                    key={specimen.id}
                    className="flex items-start justify-between gap-3 py-2 text-sm"
                  >
                    <div>
                      <div className="font-medium">
                        {specimen.specimen_type_name} · Tentative{" "}
                        {specimen.attempt_number}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {specimen.rejection_reason_name ??
                          "Prélèvement remplacé"}
                        {specimen.rejected_at
                          ? ` · ${formatDateTime(specimen.rejected_at)}`
                          : ""}
                      </div>
                    </div>
                    <Badge variant="destructive">Rejeté</Badge>
                  </div>
                ))}
              </section>
            )}
          </div>

          {canCollect && pending.length > 0 && (
            <SheetFooter className="border-t">
              <LoadingButton
                className="w-full"
                loading={collectMutation.isPending}
                disabled={selectedIds.size === 0 || !collectionTime}
                onClick={() => collectMutation.mutate()}
              >
                <TestTube className="size-4" />
                Enregistrer {selectedIds.size || ""} prélèvement
                {selectedIds.size !== 1 && "s"}
              </LoadingButton>
            </SheetFooter>
          )}
        </SheetContent>
      </Sheet>
      <RejectSpecimenDialog
        specimen={rejecting}
        onOpenChange={(open) => !open && setRejecting(null)}
        onSuccess={refresh}
      />
    </>
  )
}

function RejectSpecimenDialog({
  specimen,
  onOpenChange,
  onSuccess,
}: {
  specimen: OrderSpecimenDetailPublic | null
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}) {
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [reasonId, setReasonId] = useState<string | null>(null)
  const [reasonOption, setReasonOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [notes, setNotes] = useState("")

  useEffect(() => {
    if (!specimen) return
    setReasonId(null)
    setReasonOption(null)
    setNotes("")
  }, [specimen])

  const loadReasons = useCallback(
    async (search: string): Promise<SearchSelectOption[]> => {
      const response = await SpecimensService.readRejectionReasonOptions({
        search: search || undefined,
        limit: 20,
      })
      return response.data.map((item) => ({
        value: item.id,
        label: item.name,
      }))
    },
    [],
  )
  const mutation = useMutation({
    mutationFn: () =>
      SpecimensService.rejectSpecimen({
        specimenId: specimen!.id,
        requestBody: {
          rejection_reason_id: reasonId!,
          notes: notes.trim() || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Prélèvement rejeté et remplacement créé")
      onOpenChange(false)
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={specimen !== null} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Rejeter le prélèvement</DialogTitle>
          <DialogDescription>
            {specimen?.specimen_type_name}. Une nouvelle tentative en attente
            sera créée automatiquement.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Motif de rejet *</Label>
            <SearchSelect
              value={reasonId}
              selectedOption={reasonOption}
              onValueChange={(value, option) => {
                setReasonId(value)
                setReasonOption(option ?? null)
              }}
              loadOptions={loadReasons}
              placeholder="Sélectionner un motif"
              searchPlaceholder="Rechercher un motif…"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="rejection-notes">Notes</Label>
            <Textarea
              id="rejection-notes"
              value={notes}
              onChange={(event) => setNotes(event.currentTarget.value)}
              placeholder="Précisions facultatives…"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <LoadingButton
            variant="destructive"
            loading={mutation.isPending}
            disabled={!reasonId}
            onClick={() => mutation.mutate()}
          >
            Rejeter et recréer
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
