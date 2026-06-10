import { useQuery } from "@tanstack/react-query"
import { Printer } from "lucide-react"
import { useEffect, useState } from "react"
import { DoctorCommissionPaymentsService } from "@/client"
import { Button } from "@/components/ui/button"
import { PaymentDocument } from "./PaymentDocument"

export function PaymentDetailView({ paymentId }: { paymentId: string }) {
  const [printing, setPrinting] = useState(false)
  const query = useQuery({
    queryKey: ["doctor-commission-payments", paymentId],
    queryFn: () =>
      DoctorCommissionPaymentsService.readPayment({ id: paymentId }),
  })
  useEffect(() => {
    if (!printing) return
    document.body.dataset.printTarget = "commission-payment"
    const timeout = window.setTimeout(() => window.print(), 50)
    const reset = () => {
      delete document.body.dataset.printTarget
      setPrinting(false)
    }
    window.addEventListener("afterprint", reset, { once: true })
    return () => {
      window.clearTimeout(timeout)
      window.removeEventListener("afterprint", reset)
      delete document.body.dataset.printTarget
    }
  }, [printing])
  if (query.isLoading)
    return <div className="text-muted-foreground">Chargement…</div>
  if (!query.data)
    return <div className="text-destructive">Paiement introuvable.</div>
  const payment = query.data
  return (
    <div className="space-y-4">
      <div className="flex justify-end print:hidden">
        <Button onClick={() => setPrinting(true)}>
          <Printer className="size-4" />
          Imprimer
        </Button>
      </div>
      <PaymentDocument
        doctorName={payment.doctor_name}
        date={payment.created_at}
        operatorName={payment.created_by_name}
        paymentMethodName={payment.payment_method_name}
        reference={payment.reference}
        note={payment.note}
        lines={payment.lines ?? []}
        total={payment.total_commission_amount}
      />
    </div>
  )
}
