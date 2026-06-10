import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useState } from "react"

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
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export function InvoicePaymentDialog({
  invoiceId,
  orderId,
  balance,
  open,
  onOpenChange,
}: {
  invoiceId: string
  orderId?: string
  balance: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [amount, setAmount] = useState("")
  const [methodId, setMethodId] = useState<string | null>(null)
  const [methodOption, setMethodOption] = useState<SearchSelectOption | null>(
    null,
  )

  useEffect(() => {
    if (!open) return
    setAmount(Number(balance).toFixed(2))
    setMethodId(null)
    setMethodOption(null)
  }, [balance, open])

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
      InvoicesService.collectInvoicePayment({
        id: invoiceId,
        requestBody: {
          amount: amount.replace(",", "."),
          payment_method_id: methodId!,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Paiement enregistré")
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
    Number.isFinite(numericAmount) &&
    numericAmount > 0 &&
    numericAmount <= Number(balance) &&
    methodId

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Encaisser un paiement</DialogTitle>
          <DialogDescription>
            Le montant ne peut pas dépasser le solde restant.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="invoice-payment-amount">Montant *</Label>
            <Input
              id="invoice-payment-amount"
              inputMode="decimal"
              value={amount}
              onChange={(event) => setAmount(event.currentTarget.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Méthode *</Label>
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
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <LoadingButton
            loading={mutation.isPending}
            disabled={!valid}
            onClick={() => mutation.mutate()}
          >
            Enregistrer
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
