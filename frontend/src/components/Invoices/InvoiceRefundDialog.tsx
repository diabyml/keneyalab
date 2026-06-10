import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useState } from "react"

import type { PaymentTransactionPublic } from "@/client"
import { InvoicesService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
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
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export function InvoiceRefundDialog({
  invoiceId,
  orderId,
  payment,
  onOpenChange,
}: {
  invoiceId: string
  orderId?: string
  payment: PaymentTransactionPublic | null
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [amount, setAmount] = useState("")
  const [reason, setReason] = useState("")
  const [methodId, setMethodId] = useState<string | null>(null)
  const [methodOption, setMethodOption] = useState<SearchSelectOption | null>(
    null,
  )

  useEffect(() => {
    if (!payment) return
    setAmount(Number(payment.refundable_amount ?? 0).toFixed(2))
    setReason("")
    setMethodId(payment.payment_method_id)
    setMethodOption({
      value: payment.payment_method_id,
      label: payment.payment_method_name,
    })
  }, [payment])

  const loadMethods = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await InvoicesService.readInvoicePaymentMethodOptions({
        search: query || undefined,
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
      InvoicesService.refundInvoicePayment({
        id: invoiceId,
        paymentId: payment!.id,
        requestBody: {
          amount: amount.replace(",", "."),
          payment_method_id: methodId!,
          reason: reason.trim(),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Remboursement enregistré")
      onOpenChange(false)
      queryClient.invalidateQueries({ queryKey: ["invoice", invoiceId] })
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      if (orderId) {
        queryClient.invalidateQueries({ queryKey: ["order", orderId] })
      }
    },
    onError: handleError.bind(showErrorToast),
  })
  const numericAmount = Number(amount.replace(",", "."))
  const valid =
    payment &&
    Number.isFinite(numericAmount) &&
    numericAmount > 0 &&
    numericAmount <= Number(payment.refundable_amount ?? 0) &&
    methodId &&
    reason.trim()

  return (
    <Dialog open={payment !== null} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Rembourser le paiement</DialogTitle>
          <DialogDescription>
            Remboursement partiel ou total, conservé dans le journal financier.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="refund-amount">Montant *</Label>
            <Input
              id="refund-amount"
              inputMode="decimal"
              value={amount}
              onChange={(event) => setAmount(event.currentTarget.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Méthode de remboursement *</Label>
            <SearchSelect
              value={methodId}
              selectedOption={methodOption}
              onValueChange={(value, option) => {
                setMethodId(value)
                setMethodOption(option ?? null)
              }}
              loadOptions={loadMethods}
              placeholder="Sélectionner une méthode"
              searchPlaceholder="Rechercher une méthode…"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="refund-reason">Motif *</Label>
            <Textarea
              id="refund-reason"
              value={reason}
              onChange={(event) => setReason(event.currentTarget.value)}
              placeholder="Motif du remboursement…"
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
            disabled={!valid}
            onClick={() => mutation.mutate()}
          >
            Rembourser
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
