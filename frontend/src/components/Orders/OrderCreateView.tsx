import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Plus, ShieldCheck, UserRound, X } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import type {
  CatalogDetailPublic,
  DoctorWithTitlePublic,
  OrderLineOverride,
  OrderPreviewRequest,
  OrderUpdate,
  PatientInsuranceWithProviderPublic,
  PatientPublic,
} from "@/client"
import {
  DoctorsService,
  OrdersService,
  PatientContextsService,
  PatientsService,
  SpecimensService,
} from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { DoctorDialog } from "@/components/Doctors/DoctorDialog"
import { PatientDialog } from "@/components/Patients/PatientDialog"
import { PatientInsuranceDialog } from "@/components/Patients/PatientInsuranceDialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { CatalogPicker } from "./CatalogPicker"
import { TestAnalyteEditor } from "./TestAnalyteEditor"
import { formatMoney } from "./utils"

function normalizeNonNegativeAmount(value: string): string | null {
  const normalized = value.trim().replace(",", ".")
  if (!normalized) return "0"
  if (!/^\d+(?:\.\d{0,2})?$/.test(normalized)) return null

  const amount = Number(normalized)
  return Number.isFinite(amount) && amount >= 0 ? normalized : null
}

export function OrderCreateView({ orderId }: { orderId?: string }) {
  const isEdit = !!orderId
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const canCreatePatient = usePermission("patients", "create")
  const canCreateDoctor = usePermission("doctors", "create")
  const canCreateInsurance = usePermission("patient_insurance", "create")
  const canManageCommission = usePermission("commissions", "manage_config")
  const canOverride = usePermission("order_items", "edit")
  const canDiscount = usePermission("invoices", "edit")
  const canCollect = usePermission("payments", "collect") && !isEdit
  const canViewSpecimens = usePermission("specimens", "view")

  const [patientId, setPatientId] = useState<string | null>(null)
  const [patientOption, setPatientOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [doctorId, setDoctorId] = useState<string | null>(null)
  const [doctorOption, setDoctorOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [insuranceId, setInsuranceId] = useState<string>("none")
  const [contextId, setContextId] = useState<string | null>(null)
  const [contextOption, setContextOption] = useState<SearchSelectOption | null>(
    null,
  )
  const [notes, setNotes] = useState("")
  const [selected, setSelected] = useState<Map<string, CatalogDetailPublic>>(
    new Map(),
  )
  const [overrides, setOverrides] = useState<Record<string, OrderLineOverride>>(
    {},
  )
  const [analyteOverrides, setAnalyteOverrides] = useState<
    Record<string, string[]>
  >({})
  const [discount, setDiscount] = useState("")
  const [discountReason, setDiscountReason] = useState("")
  const [paymentAmount, setPaymentAmount] = useState("")
  const [isPaymentAmountEdited, setIsPaymentAmountEdited] = useState(false)
  const [paymentMethodId, setPaymentMethodId] = useState("")
  const [patientDialogOpen, setPatientDialogOpen] = useState(false)
  const [doctorDialogOpen, setDoctorDialogOpen] = useState(false)
  const [insuranceDialogOpen, setInsuranceDialogOpen] = useState(false)
  const [correctionReason, setCorrectionReason] = useState("")
  const [revisionConfirmed, setRevisionConfirmed] = useState(false)
  const [initializedOrderId, setInitializedOrderId] = useState<string | null>(
    null,
  )

  const orderQuery = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => OrdersService.readOrder({ id: orderId! }),
    enabled: isEdit,
  })
  const specimenWorkspaceQuery = useQuery({
    queryKey: ["specimen-workspace", orderId],
    queryFn: () =>
      SpecimensService.readCollectionWorkspace({ orderId: orderId! }),
    enabled: isEdit && canViewSpecimens,
  })

  const identifierQuery = useQuery({
    queryKey: ["suggested-patient-identifier", patientDialogOpen],
    queryFn: () => OrdersService.suggestedPatientIdentifier(),
    enabled: patientDialogOpen,
  })
  const insuranceQuery = useQuery({
    queryKey: ["patient-insurance", patientId],
    queryFn: () =>
      PatientsService.readPatientInsurances({ id: patientId!, limit: 100 }),
    enabled: !!patientId,
  })
  const paymentMethodsQuery = useQuery({
    queryKey: ["order-payment-methods"],
    queryFn: () => OrdersService.readPaymentMethodOptions(),
    enabled: canCollect,
  })

  useEffect(() => {
    const order = orderQuery.data
    if (!order || initializedOrderId === order.id) return
    setPatientId(order.patient_id)
    setPatientOption({
      value: order.patient_id,
      label: order.patient_name,
      description: order.patient_identifier,
    })
    setDoctorId(order.doctor_id ?? null)
    setDoctorOption(
      order.doctor_id
        ? {
            value: order.doctor_id,
            label: order.doctor_name ?? "Médecin",
          }
        : null,
    )
    setInsuranceId(order.patient_insurance_id ?? "none")
    setContextId(order.patient_context_id ?? null)
    setContextOption(
      order.patient_context_id
        ? {
            value: order.patient_context_id,
            label: order.patient_context_name ?? "Contexte patient",
          }
        : null,
    )
    setNotes(order.notes ?? "")
    setDiscount(String(order.invoice.discount ?? "0"))
    setDiscountReason(order.invoice.discount_reason ?? "")
    setOverrides(
      Object.fromEntries(
        (order.items ?? [])
          .filter((item) => item.price_override_reason)
          .map((item) => [
            item.catalog_id,
            {
              catalog_id: item.catalog_id,
              price_charged: item.price_charged,
              reason: item.price_override_reason!,
            },
          ]),
      ),
    )
    setAnalyteOverrides(
      Object.fromEntries(
        (order.items ?? []).map((item) => [
          item.catalog_id,
          (item.analytes ?? []).map((analyte) => analyte.analyte_id),
        ]),
      ),
    )
    const sourceIds = [
      ...new Set(
        (order.items ?? []).flatMap((item) =>
          item.source_catalog_ids?.length
            ? item.source_catalog_ids
            : [item.catalog_id],
        ),
      ),
    ]
    void Promise.all(
      sourceIds.map((id) => OrdersService.readOrderCatalogOption({ id })),
    ).then((details) => {
      setSelected(new Map(details.map((detail) => [detail.id, detail])))
    })
    setInitializedOrderId(order.id)
  }, [initializedOrderId, orderQuery.data])

  const loadPatients = useCallback(
    async (search: string): Promise<SearchSelectOption[]> => {
      const response = await PatientsService.readPatients({
        search: search || undefined,
        limit: 20,
      })
      return response.data.map((patient) => ({
        value: patient.id,
        label: `${patient.first_name} ${patient.last_name}`,
        description: `${patient.identifier} · ${patient.date_of_birth}`,
      }))
    },
    [],
  )
  const loadDoctors = useCallback(
    async (search: string): Promise<SearchSelectOption[]> => {
      const response = await DoctorsService.readDoctors({
        search: search || undefined,
        limit: 20,
      })
      return response.data.map((doctor) => ({
        value: doctor.id,
        label: [doctor.title_name, doctor.first_name, doctor.last_name]
          .filter(Boolean)
          .join(" "),
        description: doctor.provenance ?? undefined,
      }))
    },
    [],
  )
  const loadContexts = useCallback(
    async (search: string): Promise<SearchSelectOption[]> => {
      const response = await PatientContextsService.readPatientContexts({
        search: search || undefined,
        limit: 20,
      })
      return response.data.map((context) => ({
        value: context.id,
        label: context.name,
      }))
    },
    [],
  )

  const completeOverrides = useMemo(
    () =>
      Object.values(overrides).filter((override) => {
        const price = Number(String(override.price_charged).replace(",", "."))
        return (
          Number.isFinite(price) &&
          price >= 0 &&
          override.reason.trim().length > 0
        )
      }),
    [overrides],
  )
  const hasIncompleteOverride =
    completeOverrides.length !== Object.keys(overrides).length

  const normalizedDiscount = useMemo(
    () => normalizeNonNegativeAmount(discount),
    [discount],
  )
  const hasDiscount =
    normalizedDiscount !== null && Number(normalizedDiscount) > 0
  const isDiscountReasonMissing =
    hasDiscount && discountReason.trim().length === 0

  const request = useMemo<OrderPreviewRequest | null>(() => {
    if (!patientId || selected.size === 0) return null
    if (normalizedDiscount === null) return null
    const initialPayment =
      canCollect &&
      Number(paymentAmount.replace(",", ".")) > 0 &&
      paymentMethodId
        ? {
            amount: paymentAmount.replace(",", "."),
            payment_method_id: paymentMethodId,
          }
        : null
    return {
      patient_id: patientId,
      doctor_id: doctorId,
      patient_insurance_id: insuranceId === "none" ? null : insuranceId,
      patient_context_id: contextId,
      notes: notes.trim() || null,
      catalog_ids: [...selected.keys()],
      item_analytes: Object.entries(analyteOverrides).map(
        ([catalog_id, analyte_ids]) => ({ catalog_id, analyte_ids }),
      ),
      line_overrides: completeOverrides,
      discount: normalizedDiscount,
      discount_reason: discountReason.trim() || null,
      initial_payment: initialPayment,
    }
  }, [
    canCollect,
    contextId,
    discountReason,
    doctorId,
    insuranceId,
    notes,
    completeOverrides,
    patientId,
    paymentAmount,
    paymentMethodId,
    selected,
    analyteOverrides,
    normalizedDiscount,
  ])

  const previewRequest = useMemo<OrderPreviewRequest | null>(() => {
    if (!request) return null

    return {
      ...request,
      notes: null,
      line_overrides: request.line_overrides?.map((override) => ({
        ...override,
        reason: "Aperçu de la modification de prix",
      })),
      discount_reason: hasDiscount ? "Aperçu de la remise" : null,
    }
  }, [hasDiscount, request])

  const previewQuery = useQuery({
    queryKey: ["order-preview", previewRequest],
    queryFn: () =>
      isEdit
        ? OrdersService.previewOrderUpdate({
            id: orderId!,
            requestBody: previewRequest!,
          })
        : OrdersService.previewOrder({ requestBody: previewRequest! }),
    enabled: previewRequest !== null,
    placeholderData: (previousData) => previousData,
    retry: false,
  })

  const createMutation = useMutation({
    mutationFn: () => {
      if (isEdit) {
        const requestBody: OrderUpdate = {
          ...request!,
          initial_payment: null,
          correction_reason: correctionReason.trim(),
          expected_revision: orderQuery.data?.revision_number ?? 1,
        }
        return OrdersService.updateOrder({ id: orderId!, requestBody })
      }
      return OrdersService.createOrder({ requestBody: request! })
    },
    onSuccess: (order) => {
      showSuccessToast(
        isEdit
          ? `Révision ${order.revision_number} enregistrée`
          : `Demande ${order.accession_number} créée`,
      )
      queryClient.invalidateQueries({ queryKey: ["orders"] })
      queryClient.invalidateQueries({ queryKey: ["order", order.id] })
      queryClient.invalidateQueries({ queryKey: ["order-revisions", order.id] })
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      queryClient.invalidateQueries({
        queryKey: ["specimen-workspace", order.id],
      })
      navigate({ to: "/orders/$orderId", params: { orderId: order.id } })
    },
    onError: handleError.bind(showErrorToast),
  })

  const selectPatient = (patient: PatientPublic) => {
    setPatientId(patient.id)
    setPatientOption({
      value: patient.id,
      label: `${patient.first_name} ${patient.last_name}`,
      description: patient.identifier,
    })
    setInsuranceId("none")
  }
  const selectDoctor = (doctor: DoctorWithTitlePublic) => {
    setDoctorId(doctor.id)
    setDoctorOption({
      value: doctor.id,
      label: [doctor.title_name, doctor.first_name, doctor.last_name]
        .filter(Boolean)
        .join(" "),
      description: doctor.provenance ?? undefined,
    })
  }
  const selectInsurance = (insurance: PatientInsuranceWithProviderPublic) => {
    setInsuranceId(insurance.id)
  }

  const preview = previewQuery.data

  useEffect(() => {
    if (!preview || isPaymentAmountEdited) return
    setPaymentAmount(preview.net_amount)
  }, [isPaymentAmountEdited, preview])

  const updateDiscount = (value: string) => {
    setDiscount(value)
    if (!preview || isPaymentAmountEdited) return

    const normalized = normalizeNonNegativeAmount(value)
    if (normalized === null) return

    const nextNetAmount = Math.max(
      Number(preview.total_amount) - Number(normalized),
      0,
    )
    setPaymentAmount(nextNetAmount.toFixed(2))
  }

  if (isEdit && orderQuery.isLoading) {
    return <Skeleton className="h-[560px] w-full" />
  }

  return (
    <>
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_580px]">
        <div className="space-y-6">
          <section className="space-y-4 border-b pb-6">
            <div>
              <h2 className="text-base font-semibold">
                Patient et prescription
              </h2>
              <p className="text-sm text-muted-foreground">
                Identifiez le patient et les informations de prescription.
              </p>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-2">
                <Label>Patient *</Label>
                <div className="flex gap-2">
                  <div className="min-w-0 flex-1">
                    <SearchSelect
                      value={patientId}
                      selectedOption={patientOption}
                      onValueChange={(value, option) => {
                        setPatientId(value)
                        setPatientOption(option ?? null)
                        setInsuranceId("none")
                      }}
                      loadOptions={loadPatients}
                      placeholder="Rechercher un patient"
                      searchPlaceholder="Nom, identifiant, téléphone…"
                    />
                  </div>
                  {canCreatePatient && (
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => setPatientDialogOpen(true)}
                      aria-label="Créer un patient"
                    >
                      <Plus className="size-4" />
                    </Button>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <Label>Médecin prescripteur</Label>
                <div className="flex gap-2">
                  <div className="min-w-0 flex-1">
                    <SearchSelect
                      value={doctorId}
                      selectedOption={doctorOption}
                      onValueChange={(value, option) => {
                        setDoctorId(value)
                        setDoctorOption(option ?? null)
                      }}
                      loadOptions={loadDoctors}
                      placeholder="Sans prescripteur"
                      searchPlaceholder="Rechercher un médecin…"
                    />
                  </div>
                  {canCreateDoctor && (
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => setDoctorDialogOpen(true)}
                      aria-label="Créer un médecin"
                    >
                      <Plus className="size-4" />
                    </Button>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <Label>Assurance</Label>
                <div className="flex gap-2">
                  <Select
                    value={insuranceId}
                    onValueChange={setInsuranceId}
                    disabled={!patientId}
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue
                        placeholder={
                          patientId
                            ? "Paiement direct"
                            : "Sélectionnez d'abord un patient"
                        }
                      />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Paiement direct</SelectItem>
                      {(insuranceQuery.data?.data ?? []).map((insurance) => (
                        <SelectItem key={insurance.id} value={insurance.id}>
                          {insurance.insurance_provider_name} ·{" "}
                          {insurance.policy_number}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {patientId && canCreateInsurance && (
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => setInsuranceDialogOpen(true)}
                      aria-label="Ajouter une assurance"
                    >
                      <Plus className="size-4" />
                    </Button>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <Label>Contexte patient</Label>
                <SearchSelect
                  value={contextId}
                  selectedOption={contextOption}
                  onValueChange={(value, option) => {
                    setContextId(value)
                    setContextOption(option ?? null)
                  }}
                  loadOptions={loadContexts}
                  placeholder="Aucun contexte"
                  searchPlaceholder="Rechercher un contexte…"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={notes}
                onChange={(event) => setNotes(event.currentTarget.value)}
                rows={2}
                placeholder="Informations utiles pour le laboratoire…"
              />
            </div>
          </section>

          <section className="space-y-4">
            <div>
              <h2 className="text-base font-semibold">Examens demandés</h2>
              <p className="text-sm text-muted-foreground">
                Recherchez les tests ou ajoutez plusieurs résultats avec Entrée.
              </p>
            </div>
            <CatalogPicker
              selected={selected}
              onChange={(next) => {
                setSelected(next)
                const selectedIds = new Set(next.keys())
                setAnalyteOverrides((current) =>
                  Object.fromEntries(
                    Object.entries(current).filter(([catalogId]) => {
                      const previewItem = preview?.items.find(
                        (item) => item.catalog_id === catalogId,
                      )
                      return (
                        !previewItem ||
                        (previewItem.source_catalog_ids ?? []).some(
                          (sourceId) => selectedIds.has(sourceId),
                        )
                      )
                    }),
                  ),
                )
              }}
            />
          </section>
        </div>

        <aside className="sticky top-4 overflow-hidden rounded-md border bg-card">
          <div className="border-b px-4 py-3">
            <h2 className="font-semibold">Résumé de la demande</h2>
            <p className="text-xs text-muted-foreground">
              Calculé et validé par le serveur
            </p>
          </div>
          <div className="max-h-[calc(100vh-15rem)] space-y-4 overflow-y-auto p-4">
            {!request ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                <UserRound className="mx-auto mb-3 size-8" />
                Sélectionnez un patient et au moins un examen.
              </div>
            ) : previewQuery.isLoading && !preview ? (
              <div className="space-y-4 py-2">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="size-4" />
                </div>
                {Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="space-y-2 border-b pb-3">
                    <div className="flex justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-20" />
                      </div>
                      <Skeleton className="h-4 w-20" />
                    </div>
                  </div>
                ))}
                <Skeleton className="h-16 w-full" />
              </div>
            ) : previewQuery.isError ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                Impossible de calculer la demande. Vérifiez les montants et les
                sélections.
              </div>
            ) : preview ? (
              <div className="relative">
                {previewQuery.isFetching && (
                  <div
                    className="pointer-events-none absolute inset-x-0 top-0 z-10 space-y-2 bg-card/85 pb-3 backdrop-blur-[1px]"
                    role="status"
                  >
                    <span className="sr-only">Actualisation du résumé</span>
                    <Skeleton className="h-3 w-28" />
                    <Skeleton className="h-1.5 w-full" />
                  </div>
                )}
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                      <span>Examens</span>
                      <span>{preview.items.length}</span>
                    </div>
                    {preview.items.map((item) => (
                      <div
                        key={item.catalog_id}
                        className="space-y-2 border-b pb-2"
                      >
                        <div className="flex items-start justify-between gap-3 text-sm">
                          <span className="min-w-0">
                            <span className="block truncate font-medium">
                              {item.catalog_name}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {item.catalog_code}
                            </span>
                            {item.is_covered_by_insurance && (
                              <span className="mt-1 flex items-center gap-1 text-xs text-emerald-700 dark:text-emerald-400">
                                <ShieldCheck className="size-3" />
                                {item.insurance_provider_name}
                              </span>
                            )}
                          </span>
                          <span className="shrink-0 tabular-nums">
                            {formatMoney(item.price_charged)}
                          </span>
                        </div>
                        <TestAnalyteEditor
                          analytes={item.analytes ?? []}
                          busy={previewQuery.isFetching}
                          onChange={(analyteIds) =>
                            setAnalyteOverrides((current) => ({
                              ...current,
                              [item.catalog_id]: analyteIds,
                            }))
                          }
                        />
                        {canOverride && (
                          <div className="space-y-1">
                            <div className="grid grid-cols-[90px_minmax(0,1fr)_auto] gap-1">
                              <Input
                                inputMode="decimal"
                                className="h-8 text-xs"
                                value={
                                  overrides[
                                    item.catalog_id
                                  ]?.price_charged?.toString() ?? ""
                                }
                                onChange={(event) => {
                                  const value = event.currentTarget.value
                                  setOverrides((current) => {
                                    if (!value) {
                                      const next = { ...current }
                                      delete next[item.catalog_id]
                                      return next
                                    }
                                    return {
                                      ...current,
                                      [item.catalog_id]: {
                                        catalog_id: item.catalog_id,
                                        price_charged: value.replace(",", "."),
                                        reason:
                                          current[item.catalog_id]?.reason ??
                                          "",
                                      },
                                    }
                                  })
                                }}
                                placeholder="Nouveau prix"
                              />
                              <Input
                                className="h-8 text-xs"
                                value={overrides[item.catalog_id]?.reason ?? ""}
                                onChange={(event) => {
                                  const reason = event.currentTarget.value
                                  setOverrides((current) => ({
                                    ...current,
                                    [item.catalog_id]: {
                                      catalog_id: item.catalog_id,
                                      price_charged:
                                        current[item.catalog_id]
                                          ?.price_charged ?? item.price_charged,
                                      reason,
                                    },
                                  }))
                                }}
                                placeholder="Motif obligatoire"
                              />
                              {overrides[item.catalog_id] && (
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  className="size-8"
                                  onClick={() =>
                                    setOverrides((current) => {
                                      const next = { ...current }
                                      delete next[item.catalog_id]
                                      return next
                                    })
                                  }
                                >
                                  <X className="size-3.5" />
                                </Button>
                              )}
                            </div>
                            {overrides[item.catalog_id] &&
                              !completeOverrides.some(
                                (override) =>
                                  override.catalog_id === item.catalog_id,
                              ) && (
                                <p className="text-xs text-destructive">
                                  Saisissez un prix valide et le motif.
                                </p>
                              )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  {preview.specimens.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-xs font-medium text-muted-foreground">
                        Prélèvements
                      </div>
                      {preview.specimens.map((specimen) => (
                        <div
                          key={specimen.specimen_type_id}
                          className="flex items-start gap-2 text-sm"
                        >
                          <span
                            className="mt-1 size-3 shrink-0 rounded-full border"
                            style={{
                              backgroundColor:
                                specimen.specimen_type_color ?? "transparent",
                            }}
                          />
                          <span>
                            {specimen.specimen_type_name}
                            {specimen.required_volume_ml
                              ? ` · ${Number(specimen.required_volume_ml).toFixed(2)} ml`
                              : ""}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                  {isEdit && orderQuery.data && (
                    <div className="space-y-2 rounded-md border border-amber-500/40 bg-amber-500/5 p-3 text-xs">
                      <div className="font-medium text-foreground">
                        Conséquences de la révision
                      </div>
                      {patientId !== orderQuery.data.patient_id && (
                        <p className="text-amber-800 dark:text-amber-300">
                          Le patient lié à la demande sera remplacé. Cette
                          correction d'identité sera conservée dans l'audit.
                        </p>
                      )}
                      <p>
                        {
                          preview.specimens.filter((candidate) =>
                            (
                              specimenWorkspaceQuery.data?.specimens ??
                              orderQuery.data?.specimens ??
                              []
                            ).some(
                              (specimen) =>
                                specimen.specimen_type_id ===
                                  candidate.specimen_type_id &&
                                specimen.status === "collected" &&
                                specimen.is_active_attempt !== false,
                            ),
                          ).length
                        }{" "}
                        prélèvement(s) déjà collecté(s) seront réutilisés.
                      </p>
                      <p>
                        {
                          preview.specimens.filter(
                            (candidate) =>
                              !(
                                specimenWorkspaceQuery.data?.specimens ??
                                orderQuery.data?.specimens ??
                                []
                              ).some(
                                (specimen) =>
                                  specimen.specimen_type_id ===
                                    candidate.specimen_type_id &&
                                  specimen.status === "collected" &&
                                  specimen.is_active_attempt !== false,
                              ),
                          ).length
                        }{" "}
                        prélèvement(s) resteront ou deviendront en attente.
                      </p>
                      {Number(orderQuery.data.invoice.amount_paid) >
                        Number(preview.net_amount) && (
                        <p className="font-medium text-amber-800 dark:text-amber-300">
                          Un avoir de{" "}
                          {formatMoney(
                            Number(orderQuery.data.invoice.amount_paid) -
                              Number(preview.net_amount),
                          )}{" "}
                          sera créé pour remboursement.
                        </p>
                      )}
                    </div>
                  )}
                  <Separator />
                  {canDiscount && (
                    <div className="grid gap-2">
                      <Label className="text-xs">Remise</Label>
                      <Input
                        inputMode="decimal"
                        value={discount}
                        onChange={(event) =>
                          updateDiscount(event.currentTarget.value)
                        }
                        placeholder="0,00"
                      />
                      {normalizedDiscount === null && (
                        <p className="text-xs text-destructive">
                          Saisissez un montant valide avec deux décimales
                          maximum.
                        </p>
                      )}
                      {hasDiscount && (
                        <Input
                          value={discountReason}
                          onChange={(event) =>
                            setDiscountReason(event.currentTarget.value)
                          }
                          placeholder="Motif de remise obligatoire"
                        />
                      )}
                      {isDiscountReasonMissing && (
                        <p className="text-xs text-destructive">
                          Le motif de remise est obligatoire.
                        </p>
                      )}
                    </div>
                  )}
                  {canCollect && (
                    <div className="grid gap-2">
                      <Label className="text-xs">Paiement initial</Label>
                      <div className="grid grid-cols-2 gap-2">
                        <Input
                          inputMode="decimal"
                          value={paymentAmount}
                          onChange={(event) => {
                            setIsPaymentAmountEdited(true)
                            setPaymentAmount(event.currentTarget.value)
                          }}
                          placeholder="0,00"
                        />
                        <Select
                          value={paymentMethodId}
                          onValueChange={setPaymentMethodId}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Méthode" />
                          </SelectTrigger>
                          <SelectContent>
                            {(paymentMethodsQuery.data?.data ?? []).map(
                              (method) => (
                                <SelectItem key={method.id} value={method.id}>
                                  {method.name}
                                </SelectItem>
                              ),
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                  <Separator />
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total</span>
                      <span>{formatMoney(preview.total_amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Remise</span>
                      <span>- {formatMoney(preview.discount)}</span>
                    </div>
                    <div className="flex justify-between text-base font-semibold">
                      <span>Net</span>
                      <span>{formatMoney(preview.net_amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Solde</span>
                      <span>{formatMoney(preview.balance_due)}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
          <div className="border-t p-4">
            {isEdit && (
              <div className="mb-4 space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="order-correction-reason">
                    Motif de correction *
                  </Label>
                  <Textarea
                    id="order-correction-reason"
                    value={correctionReason}
                    onChange={(event) =>
                      setCorrectionReason(event.currentTarget.value)
                    }
                    rows={3}
                    placeholder="Décrivez précisément la correction apportée…"
                  />
                </div>
                <label
                  htmlFor="confirm-order-revision"
                  className="flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/5 p-3 text-sm"
                >
                  <Checkbox
                    id="confirm-order-revision"
                    checked={revisionConfirmed}
                    onCheckedChange={(checked) =>
                      setRevisionConfirmed(checked === true)
                    }
                    className="mt-0.5"
                  />
                  <span>
                    Je confirme cette révision. Les prélèvements, résultats,
                    rapports et écritures financières antérieurs seront
                    conservés dans l'historique.
                  </span>
                </label>
              </div>
            )}
            <LoadingButton
              className="w-full"
              loading={createMutation.isPending}
              disabled={
                !request ||
                !preview ||
                previewQuery.isError ||
                hasIncompleteOverride ||
                normalizedDiscount === null ||
                isDiscountReasonMissing ||
                (isEdit &&
                  (correctionReason.trim().length === 0 || !revisionConfirmed))
              }
              onClick={() => createMutation.mutate()}
            >
              {isEdit ? "Enregistrer la révision" : "Enregistrer la demande"}
            </LoadingButton>
          </div>
        </aside>
      </div>

      <PatientDialog
        open={patientDialogOpen}
        onOpenChange={setPatientDialogOpen}
        patient={null}
        initialIdentifier={identifierQuery.data?.identifier}
        onSaved={selectPatient}
      />
      <DoctorDialog
        open={doctorDialogOpen}
        onOpenChange={setDoctorDialogOpen}
        doctor={null}
        allowCommissionConfig={canManageCommission}
        onSaved={selectDoctor}
      />
      {patientId && (
        <PatientInsuranceDialog
          patientId={patientId}
          open={insuranceDialogOpen}
          onOpenChange={setInsuranceDialogOpen}
          insurance={null}
          onSaved={selectInsurance}
        />
      )}
    </>
  )
}
