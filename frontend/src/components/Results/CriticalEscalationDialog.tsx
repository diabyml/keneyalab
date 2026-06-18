import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useState } from "react"

import type { CriticalMethod } from "@/client"
import { CriticalNotificationsService } from "@/client"
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
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export function CriticalEscalationDialog({
  resultId,
  orderId,
  onOpenChange,
}: {
  resultId: string | null
  orderId: string
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [recipientId, setRecipientId] = useState<string | null>(null)
  const [recipient, setRecipient] = useState<SearchSelectOption | null>(null)
  const [method, setMethod] = useState<CriticalMethod>("call")
  const [notes, setNotes] = useState("")

  useEffect(() => {
    if (!resultId) return
    setRecipientId(null)
    setRecipient(null)
    setMethod("call")
    setNotes("")
  }, [resultId])

  const loadRecipients = useCallback(async (search: string) => {
    const response = await CriticalNotificationsService.readCriticalRecipients({
      search: search || undefined,
      limit: 20,
    })
    return response.data.map((user) => ({
      value: user.id,
      label: user.name,
      description: user.email,
    }))
  }, [])

  const mutation = useMutation({
    mutationFn: () =>
      CriticalNotificationsService.createCriticalNotification({
        resultId: resultId!,
        requestBody: {
          notified_to_id: recipientId!,
          method,
          notes: notes.trim() || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Valeur critique notifiée")
      queryClient.invalidateQueries({ queryKey: ["result-workspace", orderId] })
      queryClient.invalidateQueries({
        queryKey: ["critical-notifications"],
      })
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={resultId !== null} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Escalader la valeur critique</DialogTitle>
          <DialogDescription>
            Enregistrez le destinataire et le canal utilisé avant vérification.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Destinataire *</Label>
            <SearchSelect
              value={recipientId}
              selectedOption={recipient}
              onValueChange={(value, option) => {
                setRecipientId(value)
                setRecipient(option ?? null)
              }}
              loadOptions={loadRecipients}
              placeholder="Sélectionner un destinataire"
            />
          </div>
          <div className="space-y-2">
            <Label>Canal *</Label>
            <Select
              value={method}
              onValueChange={(value) => setMethod(value as CriticalMethod)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="call">Appel</SelectItem>
                <SelectItem value="sms">SMS</SelectItem>
                <SelectItem value="in_app">Application</SelectItem>
                <SelectItem value="email">E-mail</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="critical-notes">Notes</Label>
            <Textarea
              id="critical-notes"
              value={notes}
              onChange={(event) => setNotes(event.currentTarget.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Plus tard
          </Button>
          <LoadingButton
            loading={mutation.isPending}
            disabled={!recipientId}
            onClick={() => mutation.mutate()}
          >
            Enregistrer la notification
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
