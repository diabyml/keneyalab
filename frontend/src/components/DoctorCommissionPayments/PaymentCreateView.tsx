import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Printer, Search } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  type DoctorCommissionPaymentCreate,
  type DoctorCommissionPaymentPreviewPublic,
  DoctorCommissionPaymentsService,
} from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { PaymentDocument } from "./PaymentDocument"
import { formatMoney } from "./utils"

const PAGE_SIZE = 50

export function PaymentCreateView() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [doctorId, setDoctorId] = useState<string | null>(null)
  const [doctorOption, setDoctorOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [methodId, setMethodId] = useState<string | null>(null)
  const [methodOption, setMethodOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [reference, setReference] = useState("")
  const [note, setNote] = useState("")
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [page, setPage] = useState(0)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [preview, setPreview] =
    useState<DoctorCommissionPaymentPreviewPublic | null>(null)

  useEffect(() => {
    const timeout = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      300,
    )
    return () => window.clearTimeout(timeout)
  }, [search])
  useEffect(() => setSelectedIds(new Set()), [])
  useEffect(() => {
    if (!preview) return
    document.body.dataset.printTarget = "commission-payment"
    const timeout = window.setTimeout(() => window.print(), 50)
    const reset = () => {
      delete document.body.dataset.printTarget
      setPreview(null)
    }
    window.addEventListener("afterprint", reset, { once: true })
    return () => {
      window.clearTimeout(timeout)
      window.removeEventListener("afterprint", reset)
      delete document.body.dataset.printTarget
    }
  }, [preview])

  const linesQuery = useQuery({
    queryKey: [
      "doctor-commission-payments",
      "payable-lines",
      { doctorId, page, debouncedSearch },
    ],
    queryFn: () =>
      DoctorCommissionPaymentsService.readPayableLines({
        doctorId,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
        search: debouncedSearch || undefined,
        sortBy: "created_at",
        sortOrder: "desc",
      }),
    enabled: Boolean(doctorId),
  })
  const lines = linesQuery.data?.data ?? []
  const selectedLines = lines.filter((line) => selectedIds.has(line.id))
  const selectedTotal = useMemo(
    () => selectedLines.reduce((sum, line) => sum + Number(line.amount), 0),
    [selectedLines],
  )
  const pageCount = Math.max(
    1,
    Math.ceil((linesQuery.data?.count ?? 0) / PAGE_SIZE),
  )
  const allSelected =
    lines.length > 0 && lines.every((line) => selectedIds.has(line.id))

  const loadDoctors = useCallback(async (value: string) => {
    const response = await DoctorCommissionPaymentsService.readDoctorOptions({
      search: value || undefined,
      limit: 20,
    })
    return response.data.map((doctor) => ({
      value: doctor.id,
      label: `${doctor.first_name} ${doctor.last_name}`,
    }))
  }, [])
  const loadMethods = useCallback(async (value: string) => {
    const response =
      await DoctorCommissionPaymentsService.readPaymentMethodOptions({
        search: value || undefined,
        limit: 20,
      })
    return response.data.map((method) => ({
      value: method.id,
      label: method.name,
    }))
  }, [])
  const request = (): DoctorCommissionPaymentCreate => ({
    line_ids: Array.from(selectedIds),
    payment_method_id: methodId || "",
    reference: reference.trim() || null,
    note: note.trim() || null,
  })
  const previewMutation = useMutation({
    mutationFn: () =>
      DoctorCommissionPaymentsService.previewPayment({
        requestBody: request(),
      }),
    onSuccess: setPreview,
    onError: (error) =>
      showErrorToast(
        error instanceof Error ? error.message : "Aperçu impossible",
      ),
  })
  const createMutation = useMutation({
    mutationFn: () =>
      DoctorCommissionPaymentsService.createPayment({ requestBody: request() }),
    onSuccess: async (payment) => {
      await queryClient.invalidateQueries({
        queryKey: ["doctor-commission-payments"],
      })
      showSuccessToast("Paiement de commissions enregistré")
      await navigate({
        to: "/commissions/payments/$paymentId",
        params: { paymentId: payment.id },
      })
    },
    onError: (error) =>
      showErrorToast(
        error instanceof Error ? error.message : "Paiement impossible",
      ),
  })
  const canSubmit = Boolean(
    methodId && selectedIds.size > 0 && selectedTotal > 0,
  )

  return (
    <div className="space-y-5">
      <Card className="grid gap-4 p-4 lg:grid-cols-2">
        <div className="space-y-2">
          <Label>Médecin</Label>
          <SearchSelect
            value={doctorId}
            selectedOption={doctorOption}
            onValueChange={(value, option) => {
              setDoctorId(value)
              setDoctorOption(option ?? null)
              setPage(0)
            }}
            loadOptions={loadDoctors}
            placeholder="Sélectionner un médecin"
            searchPlaceholder="Rechercher un médecin…"
          />
        </div>
        <div className="space-y-2">
          <Label>Méthode de paiement</Label>
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
          <Label htmlFor="reference">Référence</Label>
          <Input
            id="reference"
            value={reference}
            onChange={(event) => setReference(event.target.value)}
            maxLength={255}
            placeholder="Facultative"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="note">Note</Label>
          <Textarea
            id="note"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            maxLength={2000}
            placeholder="Facultative"
          />
        </div>
      </Card>
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => {
            setSearch(event.target.value)
            setPage(0)
          }}
          disabled={!doctorId}
          placeholder="Rechercher une demande ou une facture…"
          className="pl-9"
        />
      </div>
      <Card className="overflow-hidden p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-muted/20 p-3 text-sm">
          <span>
            <strong>{selectedIds.size}</strong> ligne
            {selectedIds.size !== 1 && "s"} sélectionnée
            {selectedIds.size !== 1 && "s"} sur cette page
          </span>
          <span>
            Total net :{" "}
            <strong className="tabular-nums">
              {formatMoney(selectedTotal)}
            </strong>
          </span>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <Checkbox
                  checked={allSelected}
                  onCheckedChange={() =>
                    setSelectedIds(
                      allSelected
                        ? new Set()
                        : new Set(lines.map((line) => line.id)),
                    )
                  }
                  aria-label="Sélectionner la page visible"
                />
              </TableHead>
              <TableHead>Demande / facture</TableHead>
              <TableHead>Nature</TableHead>
              <TableHead className="text-right">Assuré</TableHead>
              <TableHead className="text-right">Non assuré</TableHead>
              <TableHead className="text-right">Commission nette</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!doctorId ? (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="h-32 text-center text-muted-foreground"
                >
                  Sélectionnez un médecin pour afficher ses lignes payables.
                </TableCell>
              </TableRow>
            ) : lines.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="h-32 text-center text-muted-foreground"
                >
                  Aucune ligne payable.
                </TableCell>
              </TableRow>
            ) : (
              lines.map((line) => (
                <TableRow key={line.id}>
                  <TableCell>
                    <Checkbox
                      checked={selectedIds.has(line.id)}
                      onCheckedChange={() =>
                        setSelectedIds((current) => {
                          const next = new Set(current)
                          next.has(line.id)
                            ? next.delete(line.id)
                            : next.add(line.id)
                          return next
                        })
                      }
                      aria-label={`Sélectionner ${line.accession_number}`}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{line.accession_number}</div>
                    <div className="text-xs text-muted-foreground">
                      {line.invoice_number}
                    </div>
                  </TableCell>
                  <TableCell>
                    {line.line_type === "adjustment"
                      ? "Ajustement"
                      : "Commission"}
                    <div className="max-w-xs truncate text-xs text-muted-foreground">
                      {line.description}
                    </div>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(line.insured_net_amount)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(line.non_insured_net_amount)}
                  </TableCell>
                  <TableCell className="text-right font-medium tabular-nums">
                    {formatMoney(line.amount)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <div className="flex items-center justify-between border-t bg-muted/20 p-3 text-sm">
          <span>{linesQuery.data?.count ?? 0} lignes, 50 par page</span>
          <div className="flex items-center gap-2">
            <span>
              Page {page + 1} sur {pageCount}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
            >
              Précédente
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page + 1 >= pageCount}
              onClick={() => setPage(page + 1)}
            >
              Suivante
            </Button>
          </div>
        </div>
      </Card>
      <div className="flex justify-end gap-2">
        <Button
          variant="outline"
          disabled={!canSubmit || previewMutation.isPending}
          onClick={() => previewMutation.mutate()}
        >
          <Printer className="size-4" />
          {previewMutation.isPending ? "Préparation…" : "Imprimer l’aperçu"}
        </Button>
        <Button
          disabled={!canSubmit || createMutation.isPending}
          onClick={() => createMutation.mutate()}
        >
          {createMutation.isPending ? "Validation…" : "Valider le paiement"}
        </Button>
      </div>
      {preview && (
        <div className="commission-payment-print-container hidden">
          <PaymentDocument
            preview
            doctorName={preview.doctor_name}
            paymentMethodName={preview.payment_method_name}
            reference={preview.reference}
            note={preview.note}
            lines={preview.lines}
            total={preview.total_commission_amount}
          />
        </div>
      )}
    </div>
  )
}
