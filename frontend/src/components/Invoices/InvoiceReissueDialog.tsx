import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import type { InvoiceDetailPublic } from "@/client"
import { InvoicesService } from "@/client"
import { formatMoney } from "@/components/Orders/utils"
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

export function InvoiceReissueDialog({
  invoice,
  open,
  onOpenChange,
}: {
  invoice: InvoiceDetailPublic
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [discount, setDiscount] = useState("")
  const [reason, setReason] = useState("")

  useEffect(() => {
    if (!open) return
    setDiscount(Number(invoice.discount ?? 0).toFixed(2))
    setReason("")
  }, [invoice.discount, open])

  const mutation = useMutation({
    mutationFn: () =>
      InvoicesService.reissueInvoice({
        id: invoice.id,
        requestBody: {
          discount: discount.replace(",", "."),
          reason: reason.trim(),
        },
      }),
    onSuccess: (replacement) => {
      showSuccessToast(`Facture réémise en version ${replacement.version}`)
      onOpenChange(false)
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      window.location.assign(`/invoices/${replacement.id}`)
    },
    onError: handleError.bind(showErrorToast),
  })
  const numericDiscount = Number(discount.replace(",", "."))
  const newNet = Number(invoice.total_amount) - numericDiscount
  const excess = Math.max(0, Number(invoice.amount_paid ?? 0) - newNet)
  const valid =
    Number.isFinite(numericDiscount) &&
    numericDiscount >= 0 &&
    numericDiscount <= Number(invoice.total_amount) &&
    reason.trim().length > 0 &&
    excess === 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Corriger et réémettre</DialogTitle>
          <DialogDescription>
            La version actuelle sera annulée et son solde encaissé transféré à
            la nouvelle version.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 rounded-md border p-3 text-sm">
            <span className="text-muted-foreground">Net actuel</span>
            <span className="text-right">
              {formatMoney(invoice.net_amount)}
            </span>
            <span className="text-muted-foreground">Nouveau net</span>
            <span className="text-right font-semibold">
              {formatMoney(Math.max(0, newNet))}
            </span>
            <span className="text-muted-foreground">Solde transféré</span>
            <span className="text-right">
              {formatMoney(invoice.amount_paid ?? 0)}
            </span>
          </div>
          <div className="space-y-2">
            <Label htmlFor="reissue-discount">Nouvelle remise *</Label>
            <Input
              id="reissue-discount"
              inputMode="decimal"
              value={discount}
              onChange={(event) => setDiscount(event.currentTarget.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reissue-reason">Motif de correction *</Label>
            <Textarea
              id="reissue-reason"
              value={reason}
              onChange={(event) => setReason(event.currentTarget.value)}
              placeholder="Expliquez la correction…"
            />
          </div>
          {excess > 0 && (
            <p className="text-sm text-destructive">
              Remboursez d'abord {formatMoney(excess)} avant la réémission.
            </p>
          )}
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
            Réémettre
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
