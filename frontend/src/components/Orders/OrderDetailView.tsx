import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  CheckCheck,
  CreditCard,
  FileText,
  Microscope,
  Pencil,
  Printer,
  ReceiptText,
  ShieldCheck,
  TestTube,
  XCircle,
} from "lucide-react"
import { useEffect, useState } from "react"

import type { OrderDetailPublic } from "@/client"
import { InvoicesService, OrdersService, SpecimensService } from "@/client"
import {
  LabDocumentFooter,
  LabDocumentHeader,
  LabDocumentName,
} from "@/components/Common/LabDocumentIdentity"
import { CollectAllSpecimensDialog } from "@/components/Specimens/CollectAllSpecimensDialog"
import { SpecimenCollectionSheet } from "@/components/Specimens/SpecimenCollectionSheet"
import { SPECIMEN_STATUS_LABELS } from "@/components/Specimens/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { Code128Barcode } from "./Code128Barcode"
import { OrderDetailSkeleton } from "./OrderDetailSkeleton"
import { OrderRevisionHistory } from "./OrderRevisionHistory"
import {
  formatDateTime,
  formatMoney,
  ORDER_STATUS_LABELS,
  PAYMENT_STATUS_LABELS,
} from "./utils"

export function OrderDetailView({ orderId }: { orderId: string }) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const canCollectPayment = usePermission("payments", "collect")
  const canViewSpecimens = usePermission("specimens", "view")
  const canCollectSpecimens = usePermission("specimens", "collect")
  const canEnterResults = usePermission("results", "enter")
  const canEditOrder = usePermission("orders", "edit")
  const canCancelOrder = usePermission("orders", "cancel")
  const canRefundPayment = usePermission("payments", "refund")
  const canViewAudit = usePermission("audit", "view")
  const canViewReports = usePermission("reports", "view")
  const [printTarget, setPrintTarget] = useState<"receipt" | "labels" | null>(
    null,
  )
  const [paymentAmount, setPaymentAmount] = useState("")
  const [paymentMethodId, setPaymentMethodId] = useState("")
  const [collectionSheetOpen, setCollectionSheetOpen] = useState(false)
  const [collectAllOpen, setCollectAllOpen] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [cancelReason, setCancelReason] = useState("")
  const orderQuery = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => OrdersService.readOrder({ id: orderId }),
  })
  const methodsQuery = useQuery({
    queryKey: ["order-payment-methods"],
    queryFn: () => OrdersService.readPaymentMethodOptions(),
    enabled: canCollectPayment,
  })
  const specimenWorkspaceQuery = useQuery({
    queryKey: ["specimen-workspace", orderId],
    queryFn: () => SpecimensService.readCollectionWorkspace({ orderId }),
    enabled: canViewSpecimens,
  })

  useEffect(() => {
    if (!printTarget) return
    document.body.dataset.printTarget = printTarget
    const timeout = window.setTimeout(() => window.print(), 50)
    const reset = () => {
      delete document.body.dataset.printTarget
      setPrintTarget(null)
    }
    window.addEventListener("afterprint", reset, { once: true })
    return () => {
      window.clearTimeout(timeout)
      window.removeEventListener("afterprint", reset)
    }
  }, [printTarget])

  const paymentMutation = useMutation({
    mutationFn: () =>
      InvoicesService.collectInvoicePayment({
        id: orderQuery.data!.invoice.id,
        requestBody: {
          amount: paymentAmount.replace(",", "."),
          payment_method_id: paymentMethodId,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Paiement enregistré")
      setPaymentAmount("")
      setPaymentMethodId("")
      queryClient.invalidateQueries({ queryKey: ["order", orderId] })
    },
    onError: handleError.bind(showErrorToast),
  })
  const cancelMutation = useMutation({
    mutationFn: () =>
      OrdersService.cancelOrder({
        id: orderId,
        requestBody: {
          reason: cancelReason.trim(),
          expected_revision: orderQuery.data!.revision_number ?? 1,
        },
      }),
    onSuccess: (updated) => {
      showSuccessToast("Demande annulée")
      setCancelOpen(false)
      setCancelReason("")
      queryClient.setQueryData(["order", orderId], updated)
      queryClient.invalidateQueries({ queryKey: ["orders"] })
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      queryClient.invalidateQueries({
        queryKey: ["invoice", updated.invoice.id],
      })
      queryClient.invalidateQueries({ queryKey: ["result-queue"] })
      queryClient.invalidateQueries({ queryKey: ["collection-queue"] })
      queryClient.invalidateQueries({
        queryKey: ["doctor-commission-payments"],
      })
      queryClient.invalidateQueries({ queryKey: ["order-revisions", orderId] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const order = orderQuery.data
  if (orderQuery.isLoading) {
    return <OrderDetailSkeleton />
  }
  if (!order) {
    return <div className="py-16 text-center">Demande introuvable.</div>
  }
  const balance =
    Number(order.invoice.net_amount) - Number(order.invoice.amount_paid)
  const activeSpecimens = (
    specimenWorkspaceQuery.data?.specimens ??
    order.specimens ??
    []
  ).filter((specimen) => specimen.is_active_attempt !== false)
  const pendingCount = activeSpecimens.filter(
    (specimen) => specimen.status === "pending",
  ).length
  const isCancelled = order.status === "cancelled"
  const canCancel =
    !isCancelled &&
    canCancelOrder &&
    canRefundPayment &&
    !cancelMutation.isPending

  return (
    <>
      <div className="screen-order-detail space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <Button variant="ghost" size="sm" asChild className="-ml-3 mb-2">
              <Link to="/orders">
                <ArrowLeft className="size-4" />
                Demandes
              </Link>
            </Button>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="font-mono text-2xl font-bold">
                {order.accession_number}
              </h1>
              <Badge variant="outline">
                {ORDER_STATUS_LABELS[order.status]}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              Créée le {formatDateTime(order.created_at)} par{" "}
              {order.created_by_name ?? "Utilisateur"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {canViewReports && !isCancelled && (
              <Button variant="outline" asChild>
                <Link to="/orders/$orderId/report" params={{ orderId }}>
                  <FileText className="size-4" />
                  Compte rendu
                </Link>
              </Button>
            )}
            {canEditOrder && !isCancelled && (
              <Button variant="outline" asChild>
                <Link to="/orders/$orderId/edit" params={{ orderId }}>
                  <Pencil className="size-4" />
                  Modifier
                </Link>
              </Button>
            )}
            {canCollectSpecimens && !isCancelled && pendingCount > 0 && (
              <>
                <Button
                  variant="outline"
                  onClick={() => setCollectionSheetOpen(true)}
                >
                  <TestTube className="size-4" />
                  Prélever
                </Button>
                <Button onClick={() => setCollectAllOpen(true)}>
                  <CheckCheck className="size-4" />
                  Tout prélever
                </Button>
              </>
            )}
            {canEnterResults &&
              !isCancelled &&
              ["collected", "in_progress", "partial_results"].includes(
                order.status,
              ) && (
                <Button asChild>
                  <Link to="/results/$orderId" params={{ orderId }}>
                    <Microscope className="size-4" />
                    Saisir les résultats
                  </Link>
                </Button>
              )}
            {canCancel && (
              <Button variant="destructive" onClick={() => setCancelOpen(true)}>
                <XCircle className="size-4" />
                Annuler
              </Button>
            )}
            <Button variant="outline" onClick={() => setPrintTarget("labels")}>
              <Printer className="size-4" />
              Étiquettes
            </Button>
            <Button onClick={() => setPrintTarget("receipt")}>
              <ReceiptText className="size-4" />
              Facture thermique
            </Button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="space-y-3 border-t pt-4">
            <h2 className="font-semibold">Patient</h2>
            <div>
              <div className="font-medium">{order.patient_name}</div>
              <div className="text-sm text-muted-foreground">
                {order.patient_identifier} · {order.patient_date_of_birth}
              </div>
            </div>
            {order.insurance_provider_name && (
              <div className="flex items-start gap-2 text-sm">
                <ShieldCheck className="mt-0.5 size-4 text-emerald-600" />
                <span>
                  {order.insurance_provider_name}
                  <span className="block text-muted-foreground">
                    {order.insurance_policy_number}
                  </span>
                </span>
              </div>
            )}
          </section>
          <section className="space-y-3 border-t pt-4">
            <h2 className="font-semibold">Prescription</h2>
            <div className="text-sm">
              <span className="text-muted-foreground">Médecin : </span>
              {order.doctor_name ?? "Sans prescripteur"}
            </div>
            <div className="text-sm">
              <span className="text-muted-foreground">Contexte : </span>
              {order.patient_context_name ?? "Aucun"}
            </div>
            {order.notes && <p className="text-sm">{order.notes}</p>}
          </section>
          <section className="space-y-3 border-t pt-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold">Facturation</h2>
              <Button variant="link" size="sm" asChild className="h-auto p-0">
                <Link
                  to="/invoices/$invoiceId"
                  params={{ invoiceId: order.invoice.id }}
                >
                  Voir la facture
                </Link>
              </Button>
            </div>
            <div className="flex justify-between text-sm">
              <span>Net</span>
              <span className="font-medium">
                {formatMoney(order.invoice.net_amount)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Payé</span>
              <span>{formatMoney(order.invoice.amount_paid ?? 0)}</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span>Solde</span>
              <span>{formatMoney(balance)}</span>
            </div>
            <Badge variant="outline">
              {PAYMENT_STATUS_LABELS[order.invoice.payment_status ?? "unpaid"]}
            </Badge>
          </section>
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="overflow-hidden rounded-md border">
            <div className="border-b bg-muted/20 px-4 py-3 font-semibold">
              Examens ({(order.items ?? []).length})
            </div>
            {(order.items ?? []).map((item) => (
              <div
                key={item.id}
                className="flex items-start justify-between gap-4 border-b px-4 py-3 last:border-b-0"
              >
                <div>
                  <div className="font-medium">{item.catalog_name}</div>
                  <div className="text-xs text-muted-foreground">
                    {item.catalog_code}
                  </div>
                  {item.is_covered_by_insurance && (
                    <div className="mt-1 text-xs text-emerald-700 dark:text-emerald-400">
                      Tarif {item.insurance_provider_name}
                    </div>
                  )}
                </div>
                <div className="text-right tabular-nums">
                  <div>{formatMoney(item.price_charged)}</div>
                  {Number(item.catalog_price) !==
                    Number(item.price_charged) && (
                    <div className="text-xs text-muted-foreground line-through">
                      {formatMoney(item.catalog_price)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </section>

          <div className="space-y-6">
            <section className="overflow-hidden rounded-md border">
              <div className="border-b bg-muted/20 px-4 py-3 font-semibold">
                Prélèvements ({(order.specimens ?? []).length})
              </div>
              {activeSpecimens.map((specimen) => (
                <div
                  key={specimen.id}
                  className="border-b px-4 py-3 last:border-b-0"
                >
                  <div className="flex items-center gap-2 font-medium">
                    <span
                      className="size-3 rounded-full border"
                      style={{
                        backgroundColor:
                          specimen.specimen_type_color ?? "transparent",
                      }}
                    />
                    {specimen.specimen_type_name}
                    <Badge variant="outline" className="ml-auto">
                      {SPECIMEN_STATUS_LABELS[specimen.status ?? "pending"]}
                    </Badge>
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {specimen.required_volume_ml
                      ? `${Number(specimen.required_volume_ml).toFixed(2)} ml`
                      : "Volume non précisé"}
                    {specimen.collection_instructions
                      ? ` · ${specimen.collection_instructions}`
                      : ""}
                  </div>
                </div>
              ))}
            </section>

            {canCollectPayment && !isCancelled && balance > 0 && (
              <section className="space-y-3 rounded-md border p-4">
                <div className="flex items-center gap-2 font-semibold">
                  <CreditCard className="size-4" />
                  Encaisser un paiement
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Montant</Label>
                    <Input
                      inputMode="decimal"
                      value={paymentAmount}
                      onChange={(event) =>
                        setPaymentAmount(event.currentTarget.value)
                      }
                      placeholder="0,00"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Méthode</Label>
                    <Select
                      value={paymentMethodId}
                      onValueChange={setPaymentMethodId}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choisir" />
                      </SelectTrigger>
                      <SelectContent>
                        {(methodsQuery.data?.data ?? []).map((method) => (
                          <SelectItem key={method.id} value={method.id}>
                            {method.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <LoadingButton
                  className="w-full"
                  loading={paymentMutation.isPending}
                  disabled={!paymentAmount || !paymentMethodId}
                  onClick={() => paymentMutation.mutate()}
                >
                  Enregistrer le paiement
                </LoadingButton>
              </section>
            )}
          </div>
        </div>
        {canViewAudit && <OrderRevisionHistory orderId={orderId} />}
      </div>

      <ThermalReceipt order={order} />
      <SpecimenLabels order={order} />
      <SpecimenCollectionSheet
        orderId={collectionSheetOpen ? orderId : null}
        onOpenChange={setCollectionSheetOpen}
      />
      <CollectAllSpecimensDialog
        orderId={orderId}
        open={collectAllOpen}
        onOpenChange={setCollectAllOpen}
        pendingCount={pendingCount}
        balanceDue={specimenWorkspaceQuery.data?.balance_due}
      />
      <OrderCancelDialog
        open={cancelOpen}
        reason={cancelReason}
        accessionNumber={order.accession_number}
        loading={cancelMutation.isPending}
        onReasonChange={setCancelReason}
        onOpenChange={(open) => {
          setCancelOpen(open)
          if (!open) setCancelReason("")
        }}
        onConfirm={() => cancelMutation.mutate()}
      />
    </>
  )
}

function OrderCancelDialog({
  open,
  reason,
  accessionNumber,
  loading,
  onReasonChange,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  reason: string
  accessionNumber: string
  loading: boolean
  onReasonChange: (value: string) => void
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Annuler la demande {accessionNumber}</DialogTitle>
          <DialogDescription>
            Les paiements seront remboursés automatiquement avec leur méthode
            d'origine. Les résultats et prélèvements resteront dans
            l'historique.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="cancel-reason">Motif d'annulation *</Label>
          <Textarea
            id="cancel-reason"
            value={reason}
            onChange={(event) => onReasonChange(event.currentTarget.value)}
            placeholder="Indiquer le motif de l'annulation..."
            autoFocus
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Fermer
          </Button>
          <LoadingButton
            variant="destructive"
            loading={loading}
            disabled={!reason.trim()}
            onClick={onConfirm}
          >
            Annuler la demande
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ThermalReceipt({ order }: { order: OrderDetailPublic }) {
  const balance =
    Number(order.invoice.net_amount) - Number(order.invoice.amount_paid)
  return (
    <article className="thermal-receipt print-only">
      <LabDocumentHeader title="Facture / reçu" compact />
      <Separator className="my-2" />
      <div>Demande : {order.accession_number}</div>
      <div>Date : {formatDateTime(order.created_at)}</div>
      <div>Patient : {order.patient_name}</div>
      <div>ID : {order.patient_identifier}</div>
      {order.doctor_name && <div>Médecin : {order.doctor_name}</div>}
      {order.insurance_provider_name && (
        <div className="mt-1 font-bold">
          Assurance : {order.insurance_provider_name}
          {order.insurance_policy_number
            ? ` (${order.insurance_policy_number})`
            : ""}
        </div>
      )}
      <Separator className="my-2" />
      <div className="space-y-1">
        {(order.items ?? []).map((item) => (
          <div key={item.id}>
            <div className="flex justify-between gap-2">
              <span>
                {item.catalog_code} {item.catalog_name}
              </span>
              <span className="shrink-0">
                {Number(item.price_charged).toFixed(2)}
              </span>
            </div>
            {item.is_covered_by_insurance && (
              <div className="text-[9px]">
                Tarif assurance : {item.insurance_provider_name}
                {Number(item.catalog_price) !== Number(item.price_charged)
                  ? ` · Standard ${Number(item.catalog_price).toFixed(2)}`
                  : ""}
              </div>
            )}
          </div>
        ))}
      </div>
      <Separator className="my-2" />
      <div className="flex justify-between">
        <span>Total</span>
        <span>{Number(order.invoice.total_amount).toFixed(2)}</span>
      </div>
      <div className="flex justify-between">
        <span>Remise</span>
        <span>-{Number(order.invoice.discount).toFixed(2)}</span>
      </div>
      <div className="flex justify-between text-sm font-bold">
        <span>Net à payer</span>
        <span>{Number(order.invoice.net_amount).toFixed(2)}</span>
      </div>
      <div className="flex justify-between">
        <span>Payé</span>
        <span>{Number(order.invoice.amount_paid).toFixed(2)}</span>
      </div>
      <div className="flex justify-between font-bold">
        <span>Solde</span>
        <span>{balance.toFixed(2)}</span>
      </div>
      {(order.payments ?? []).map((payment) => (
        <div key={payment.id} className="mt-1 text-[9px]">
          {payment.payment_method_name} · {Number(payment.amount).toFixed(2)} ·{" "}
          {formatDateTime(payment.created_at)} · Réf.{" "}
          {payment.id.slice(0, 8).toUpperCase()}
        </div>
      ))}
      <div className="my-3">
        <Code128Barcode value={order.accession_number} />
      </div>
      <LabDocumentFooter compact />
    </article>
  )
}

function SpecimenLabels({ order }: { order: OrderDetailPublic }) {
  return (
    <section className="specimen-labels print-only">
      {(order.specimens ?? []).map((specimen) => (
        <article key={specimen.id} className="specimen-label">
          <div className="mb-1 truncate text-center text-[8px] font-semibold uppercase">
            <LabDocumentName />
          </div>
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-bold">{order.patient_name}</div>
              <div>{order.patient_identifier}</div>
            </div>
            <div className="text-right font-bold">
              {specimen.specimen_type_name}
            </div>
          </div>
          <Code128Barcode value={order.accession_number} height={32} />
          <div className="flex justify-between text-[9px]">
            <span>{order.accession_number}</span>
            <span>
              {specimen.required_volume_ml
                ? `${Number(specimen.required_volume_ml).toFixed(2)} ml`
                : ""}
            </span>
          </div>
        </article>
      ))}
    </section>
  )
}
