import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Banknote,
  ExternalLink,
  Printer,
  RefreshCw,
  RotateCcw,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import type {
  InvoiceDetailPublic,
  PaymentRefundPublic,
  PaymentTransactionPublic,
} from "@/client"
import { InvoicesService } from "@/client"
import { formatDateTime, formatMoney } from "@/components/Orders/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { usePermission } from "@/hooks/usePermission"
import { InvoicePaymentDialog } from "./InvoicePaymentDialog"
import { InvoiceRefundDialog } from "./InvoiceRefundDialog"
import { InvoiceReissueDialog } from "./InvoiceReissueDialog"
import { InvoiceThermalReceipt } from "./InvoiceThermalReceipt"
import { INVOICE_STATUS_LABELS } from "./utils"

type LedgerEntry = {
  id: string
  date?: string | null
  type: "payment" | "refund" | "transfer-in" | "transfer-out"
  label: string
  operator?: string | null
  amount: number
  reason?: string
}

export function InvoiceDetailView({ invoiceId }: { invoiceId: string }) {
  const canCollect = usePermission("payments", "collect")
  const canRefund = usePermission("payments", "refund")
  const canEdit = usePermission("invoices", "edit")
  const canVoid = usePermission("invoices", "void")
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [refundPayment, setRefundPayment] =
    useState<PaymentTransactionPublic | null>(null)
  const [reissueOpen, setReissueOpen] = useState(false)
  const [printing, setPrinting] = useState(false)
  const invoiceQuery = useQuery({
    queryKey: ["invoice", invoiceId],
    queryFn: () => InvoicesService.readInvoice({ id: invoiceId }),
  })

  useEffect(() => {
    if (!printing) return
    document.body.dataset.printTarget = "receipt"
    const timeout = window.setTimeout(() => window.print(), 50)
    const reset = () => {
      delete document.body.dataset.printTarget
      setPrinting(false)
    }
    window.addEventListener("afterprint", reset, { once: true })
    return () => {
      window.clearTimeout(timeout)
      window.removeEventListener("afterprint", reset)
    }
  }, [printing])

  if (invoiceQuery.isLoading) return <InvoiceDetailSkeleton />
  if (!invoiceQuery.data) {
    return (
      <div className="rounded-md border p-6 text-sm text-muted-foreground">
        Facture introuvable.
      </div>
    )
  }

  const invoice = invoiceQuery.data
  const active = !invoice.is_voided
  const canReissue = active && canEdit && canVoid

  return (
    <>
      <div className="space-y-6">
        <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <Button variant="ghost" size="sm" asChild className="-ml-3">
              <Link to="/invoices">
                <ArrowLeft className="size-4" />
                Factures
              </Link>
            </Button>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="font-mono text-2xl font-bold">
                {invoice.invoice_number}
              </h1>
              <Badge variant="outline">Version {invoice.version}</Badge>
              <Badge variant={invoice.is_voided ? "destructive" : "outline"}>
                {invoice.is_voided
                  ? "Annulée"
                  : INVOICE_STATUS_LABELS[invoice.payment_status ?? "unpaid"]}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Créée le {formatDateTime(invoice.created_at)} par{" "}
              {invoice.created_by_name ?? "Utilisateur"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" asChild>
              <Link
                to="/orders/$orderId"
                params={{ orderId: invoice.order_id }}
              >
                <ExternalLink className="size-4" />
                Demande
              </Link>
            </Button>
            <Button variant="outline" onClick={() => setPrinting(true)}>
              <Printer className="size-4" />
              Imprimer
            </Button>
            {canReissue && (
              <Button variant="outline" onClick={() => setReissueOpen(true)}>
                <RefreshCw className="size-4" />
                Corriger
              </Button>
            )}
            {active && canCollect && Number(invoice.balance_due) > 0 && (
              <Button onClick={() => setPaymentOpen(true)}>
                <Banknote className="size-4" />
                Encaisser
              </Button>
            )}
          </div>
        </header>

        {invoice.is_voided && (
          <div className="border-l-4 border-destructive bg-destructive/5 px-4 py-3 text-sm">
            Cette version est annulée. Consultez la version active dans
            l'historique.
          </div>
        )}

        <section className="grid gap-6 border-y py-5 md:grid-cols-2 xl:grid-cols-4">
          <Info label="Patient">
            <Link
              to="/patients/$patientId"
              params={{ patientId: invoice.patient_id }}
              className="font-medium hover:underline"
            >
              {invoice.patient_name}
            </Link>
            <span>{invoice.patient_identifier}</span>
          </Info>
          <Info label="Prescription">
            <span className="font-medium">
              {invoice.doctor_name ?? "Sans prescripteur"}
            </span>
            <span>{invoice.accession_number}</span>
          </Info>
          <Info label="Couverture">
            <span className="font-medium">
              {invoice.insurance_provider_name ?? "Paiement direct"}
            </span>
            <span>{invoice.insurance_policy_number ?? "Aucune police"}</span>
          </Info>
          <Info label="Situation">
            <span className="font-medium">
              {INVOICE_STATUS_LABELS[invoice.payment_status ?? "unpaid"]}
            </span>
            <span>Solde {formatMoney(invoice.balance_due)}</span>
          </Info>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-6">
            <InvoiceLines invoice={invoice} />
            <FinancialLedger
              invoice={invoice}
              canRefund={active && canRefund}
              onRefund={setRefundPayment}
            />
          </div>
          <aside className="space-y-6">
            <InvoiceTotals invoice={invoice} />
            <VersionHistory invoice={invoice} />
          </aside>
        </div>
      </div>

      <InvoiceThermalReceipt invoice={invoice} />
      <InvoicePaymentDialog
        invoiceId={invoice.id}
        orderId={invoice.order_id}
        balance={invoice.balance_due}
        open={paymentOpen}
        onOpenChange={setPaymentOpen}
      />
      <InvoiceRefundDialog
        invoiceId={invoice.id}
        orderId={invoice.order_id}
        payment={refundPayment}
        onOpenChange={(open) => {
          if (!open) setRefundPayment(null)
        }}
      />
      <InvoiceReissueDialog
        invoice={invoice}
        open={reissueOpen}
        onOpenChange={setReissueOpen}
      />
    </>
  )
}

function Info({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex min-w-0 flex-col gap-1 text-sm">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </div>
  )
}

function InvoiceLines({ invoice }: { invoice: InvoiceDetailPublic }) {
  return (
    <section>
      <h2 className="mb-3 font-semibold">Prestations facturées</h2>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Examen</TableHead>
              <TableHead>Tarification</TableHead>
              <TableHead className="text-right">Montant</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(invoice.lines ?? []).map((line) => (
              <TableRow key={line.id}>
                <TableCell className="font-mono text-xs">
                  {line.catalog_code}
                </TableCell>
                <TableCell className="font-medium">
                  {line.catalog_name}
                </TableCell>
                <TableCell>
                  {line.is_covered_by_insurance
                    ? (line.insurance_provider_name ?? "Assurance")
                    : "Standard"}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(line.amount)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  )
}

function FinancialLedger({
  invoice,
  canRefund,
  onRefund,
}: {
  invoice: InvoiceDetailPublic
  canRefund: boolean
  onRefund: (payment: PaymentTransactionPublic) => void
}) {
  const entries = useMemo(() => buildLedger(invoice), [invoice])
  const paymentsById = new Map(
    (invoice.payments ?? []).map((payment) => [payment.id, payment]),
  )

  return (
    <section>
      <h2 className="mb-3 font-semibold">Journal financier</h2>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Opération</TableHead>
              <TableHead>Opérateur</TableHead>
              <TableHead className="text-right">Montant</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="h-20 text-center text-muted-foreground"
                >
                  Aucune opération financière.
                </TableCell>
              </TableRow>
            ) : (
              entries.map((entry) => {
                const payment =
                  entry.type === "payment"
                    ? paymentsById.get(entry.id)
                    : undefined
                return (
                  <TableRow key={`${entry.type}-${entry.id}`}>
                    <TableCell>{formatDateTime(entry.date)}</TableCell>
                    <TableCell>
                      <div className="font-medium">{entry.label}</div>
                      {entry.reason && (
                        <div className="max-w-md text-xs text-muted-foreground">
                          {entry.reason}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>{entry.operator ?? "Utilisateur"}</TableCell>
                    <TableCell
                      className={`text-right font-medium tabular-nums ${
                        entry.amount < 0 ? "text-destructive" : ""
                      }`}
                    >
                      {entry.amount < 0 ? "-" : "+"}
                      {formatMoney(Math.abs(entry.amount))}
                    </TableCell>
                    <TableCell>
                      {canRefund &&
                        payment &&
                        Number(payment.refundable_amount) > 0 && (
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Rembourser ce paiement"
                            title="Rembourser"
                            onClick={() => onRefund(payment)}
                          >
                            <RotateCcw className="size-4" />
                          </Button>
                        )}
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  )
}

function buildLedger(invoice: InvoiceDetailPublic): LedgerEntry[] {
  const payments: LedgerEntry[] = (invoice.payments ?? []).map((payment) => ({
    id: payment.id,
    date: payment.created_at,
    type: "payment",
    label: `Paiement · ${payment.payment_method_name}`,
    operator: payment.collected_by_name,
    amount: Number(payment.amount),
  }))
  const refunds: LedgerEntry[] = (invoice.refunds ?? []).map(
    (refund: PaymentRefundPublic) => ({
      id: refund.id,
      date: refund.created_at,
      type: "refund",
      label: `Remboursement · ${refund.payment_method_name}`,
      operator: refund.refunded_by_name,
      amount: -Number(refund.amount),
      reason: refund.reason,
    }),
  )
  const transfers: LedgerEntry[] = (invoice.transfers ?? []).map((transfer) => {
    const incoming = transfer.target_invoice_id === invoice.id
    return {
      id: transfer.id,
      date: transfer.created_at,
      type: incoming ? "transfer-in" : "transfer-out",
      label: incoming
        ? "Solde transféré depuis une version antérieure"
        : "Solde transféré vers la version suivante",
      operator: transfer.created_by_name,
      amount: Number(transfer.amount) * (incoming ? 1 : -1),
    }
  })
  return [...payments, ...refunds, ...transfers].sort(
    (a, b) => new Date(b.date ?? 0).getTime() - new Date(a.date ?? 0).getTime(),
  )
}

function InvoiceTotals({ invoice }: { invoice: InvoiceDetailPublic }) {
  return (
    <section className="rounded-md border">
      <h2 className="border-b px-4 py-3 font-semibold">Totaux</h2>
      <div className="space-y-3 p-4 text-sm">
        <Amount label="Total" value={invoice.total_amount} />
        <Amount label="Remise" value={invoice.discount ?? "0"} negative />
        {invoice.discount_reason && (
          <p className="text-xs text-muted-foreground">
            {invoice.discount_reason}
          </p>
        )}
        <div className="border-t pt-3">
          <Amount label="Net" value={invoice.net_amount} strong />
        </div>
        <Amount label="Payé" value={invoice.amount_paid ?? "0"} />
        <div className="border-t pt-3">
          <Amount label="Solde" value={invoice.balance_due} strong />
        </div>
      </div>
    </section>
  )
}

function Amount({
  label,
  value,
  negative = false,
  strong = false,
}: {
  label: string
  value: string
  negative?: boolean
  strong?: boolean
}) {
  return (
    <div
      className={`flex items-center justify-between ${
        strong ? "text-base font-semibold" : ""
      }`}
    >
      <span>{label}</span>
      <span className="tabular-nums">
        {negative && Number(value) > 0 ? "-" : ""}
        {formatMoney(value)}
      </span>
    </div>
  )
}

function VersionHistory({ invoice }: { invoice: InvoiceDetailPublic }) {
  return (
    <section className="rounded-md border">
      <h2 className="border-b px-4 py-3 font-semibold">
        Historique des versions
      </h2>
      <div className="divide-y">
        {(invoice.versions ?? []).map((version) => (
          <Link
            key={version.id}
            to="/invoices/$invoiceId"
            params={{ invoiceId: version.id }}
            className="flex items-center justify-between px-4 py-3 text-sm hover:bg-muted/50"
          >
            <span className="font-medium">Version {version.version}</span>
            <span className="text-muted-foreground">
              {version.is_voided ? "Annulée" : "Active"}
            </span>
          </Link>
        ))}
      </div>
    </section>
  )
}

function InvoiceDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-72" />
      <Skeleton className="h-24 w-full" />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <Skeleton className="h-96 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    </div>
  )
}
