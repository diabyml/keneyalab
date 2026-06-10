import type { InvoiceDetailPublic } from "@/client"
import { Code128Barcode } from "@/components/Orders/Code128Barcode"
import { formatDateTime, formatMoney } from "@/components/Orders/utils"
import { Separator } from "@/components/ui/separator"

export function InvoiceThermalReceipt({
  invoice,
}: {
  invoice: InvoiceDetailPublic
}) {
  return (
    <article className="thermal-receipt print-only">
      <header className="text-center">
        <h1 className="text-base font-bold">KENEYA LAB</h1>
        <p>Laboratoire d'analyses médicales</p>
        <p>Facture / reçu</p>
      </header>
      <Separator className="my-2" />
      <div>Facture : {invoice.invoice_number}</div>
      <div>Version : {invoice.version}</div>
      <div>Demande : {invoice.accession_number}</div>
      <div>Date : {formatDateTime(invoice.created_at)}</div>
      <div>Patient : {invoice.patient_name}</div>
      <div>ID : {invoice.patient_identifier}</div>
      {invoice.doctor_name && <div>Médecin : {invoice.doctor_name}</div>}
      {invoice.insurance_provider_name && (
        <div className="mt-1 font-bold">
          Assurance : {invoice.insurance_provider_name}
          {invoice.insurance_policy_number
            ? ` (${invoice.insurance_policy_number})`
            : ""}
        </div>
      )}
      <Separator className="my-2" />
      <div className="space-y-1">
        {(invoice.lines ?? []).map((line) => (
          <div key={line.id}>
            <div className="flex justify-between gap-2">
              <span>
                {line.catalog_code} {line.catalog_name}
              </span>
              <span className="shrink-0">{Number(line.amount).toFixed(2)}</span>
            </div>
            {line.is_covered_by_insurance && (
              <div className="text-[9px]">
                Tarif assurance :{" "}
                {line.insurance_provider_name ??
                  invoice.insurance_provider_name}
              </div>
            )}
          </div>
        ))}
      </div>
      <Separator className="my-2" />
      <ReceiptAmount label="Total" value={invoice.total_amount} />
      <ReceiptAmount label="Remise" value={invoice.discount ?? "0"} negative />
      <ReceiptAmount label="Net à payer" value={invoice.net_amount} strong />
      <ReceiptAmount label="Payé" value={invoice.amount_paid ?? "0"} />
      <ReceiptAmount label="Solde" value={invoice.balance_due} strong />
      {(invoice.payments ?? []).map((payment) => (
        <div key={payment.id} className="mt-1 text-[9px]">
          {payment.payment_method_name} · {formatMoney(payment.amount)} ·{" "}
          {formatDateTime(payment.created_at)} · Réf.{" "}
          {payment.id.slice(0, 8).toUpperCase()}
        </div>
      ))}
      <div className="my-3">
        <Code128Barcode value={invoice.invoice_number} />
      </div>
      <p className="text-center">Merci pour votre confiance.</p>
    </article>
  )
}

function ReceiptAmount({
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
    <div className={`flex justify-between ${strong ? "font-bold" : ""}`}>
      <span>{label}</span>
      <span>
        {negative ? "-" : ""}
        {Number(value).toFixed(2)}
      </span>
    </div>
  )
}
