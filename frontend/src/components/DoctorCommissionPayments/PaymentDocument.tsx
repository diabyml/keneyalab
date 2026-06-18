import type {
  DoctorCommissionPayableLinePublic,
  DoctorCommissionPaymentLinePublic,
} from "@/client"
import {
  LabDocumentFooter,
  LabDocumentHeader,
} from "@/components/Common/LabDocumentIdentity"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatDate, formatDateTime, formatMoney } from "./utils"

type Props = {
  preview?: boolean
  doctorName: string
  date?: string | null
  operatorName?: string | null
  paymentMethodName: string
  reference?: string | null
  note?: string | null
  lines: Array<
    DoctorCommissionPayableLinePublic | DoctorCommissionPaymentLinePublic
  >
  total: string
}

export function PaymentDocument({
  preview,
  doctorName,
  date,
  operatorName,
  paymentMethodName,
  reference,
  note,
  lines,
  total,
}: Props) {
  return (
    <article className="commission-payment-document mx-auto max-w-4xl space-y-6 bg-background p-6 print:max-w-none print:p-0">
      <div>
        {preview && (
          <div className="mb-3 text-center font-semibold tracking-wide text-destructive">
            APERÇU - NON PAYÉ
          </div>
        )}
        <LabDocumentHeader title="Paiement de commissions" />
      </div>
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <Field label="Médecin" value={doctorName} />
        <Field
          label="Date"
          value={preview ? "À la validation" : formatDateTime(date)}
        />
        <Field
          label="Opérateur"
          value={operatorName || (preview ? "Utilisateur actuel" : "—")}
        />
        <Field label="Méthode" value={paymentMethodName} />
        <Field label="Référence" value={reference || "—"} />
        <Field label="Nombre de lignes" value={String(lines.length)} />
      </dl>
      <div className="overflow-hidden rounded-md border">
        <Table className="table-fixed">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[16%]">Date demande</TableHead>
              <TableHead className="w-[30%]">Patient</TableHead>
              <TableHead className="w-[18%] text-right">Assuré</TableHead>
              <TableHead className="w-[18%] text-right">Non assuré</TableHead>
              <TableHead className="w-[18%] text-right">Total ligne</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lines.map((line) => (
              <TableRow key={line.id}>
                <TableCell>{formatDate(line.order_date)}</TableCell>
                <TableCell className="break-words font-medium">
                  {line.patient_first_name} {line.patient_last_name}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(line.insured_commission_amount)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(line.non_insured_commission_amount)}
                </TableCell>
                <TableCell className="text-right font-medium tabular-nums">
                  {formatMoney(line.amount)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex justify-end border-t pt-4">
        <div className="text-right">
          <div className="text-sm text-muted-foreground">Total net payé</div>
          <div className="text-2xl font-bold tabular-nums">
            {formatMoney(total)}
          </div>
        </div>
      </div>
      {note && (
        <div className="rounded-md border p-4 text-sm">
          <div className="mb-1 font-medium">Note</div>
          <p className="whitespace-pre-wrap text-muted-foreground">{note}</p>
        </div>
      )}
      <LabDocumentFooter />
    </article>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  )
}
