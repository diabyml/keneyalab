import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CheckCheck,
  FileText,
  ImageUp,
  Info,
  Loader2,
  MessageSquarePlus,
  Pencil,
  Save,
} from "lucide-react"
import type { ReactNode } from "react"
import { useEffect, useMemo, useRef, useState } from "react"

import type {
  OrderAnalyteDetailPublic,
  ResultAnalyteWorkspacePublic,
  ResultTestWorkspacePublic,
  ResultVerificationSkipPublic,
} from "@/client"
import { OrdersService, ResultsService } from "@/client"
import {
  AddAnalyteControl,
  TestAnalyteActionsMenu,
} from "@/components/Orders/TestAnalyteEditor"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { CriticalEscalationDialog } from "./CriticalEscalationDialog"

export function ResultWorkspaceView({ orderId }: { orderId: string }) {
  const queryClient = useQueryClient()
  const workspaceRef = useRef<HTMLDivElement>(null)
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const canEnter = usePermission("results", "enter")
  const canEdit = usePermission("results", "edit")
  const canVerify = usePermission("results", "verify")
  const canCustomize = usePermission("orders", "edit")
  const canViewReports = usePermission("reports", "view")
  const [values, setValues] = useState<Record<string, string>>({})
  const [dirty, setDirty] = useState<Set<string>>(new Set())
  const [criticalResultId, setCriticalResultId] = useState<string | null>(null)
  const [commentResultId, setCommentResultId] = useState<string | null>(null)
  const [comment, setComment] = useState("")
  const [pendingCustomization, setPendingCustomization] = useState<{
    test: ResultTestWorkspacePublic
    analyteIds: string[]
  } | null>(null)
  const [customizationReason, setCustomizationReason] = useState("")
  const [correctionAnalyte, setCorrectionAnalyte] =
    useState<ResultAnalyteWorkspacePublic | null>(null)
  const [correctionValue, setCorrectionValue] = useState("")
  const [correctionReason, setCorrectionReason] = useState("")
  const [correctionFile, setCorrectionFile] = useState<File | null>(null)
  const [verificationSkips, setVerificationSkips] = useState<
    ResultVerificationSkipPublic[]
  >([])
  const query = useQuery({
    queryKey: ["result-workspace", orderId],
    queryFn: () => ResultsService.readResultWorkspace({ orderId }),
  })

  useEffect(() => {
    if (!query.data) return
    const initial: Record<string, string> = {}
    for (const test of query.data.tests ?? []) {
      for (const analyte of test.analytes ?? []) {
        initial[analyteKey(test, analyte)] = analyte.result_value ?? ""
      }
    }
    setValues(initial)
    setDirty(new Set())
  }, [query.data])

  useEffect(() => {
    const protect = (event: BeforeUnloadEvent) => {
      if (!dirty.size) return
      event.preventDefault()
    }
    window.addEventListener("beforeunload", protect)
    return () => window.removeEventListener("beforeunload", protect)
  }, [dirty.size])

  const saveMutation = useMutation({
    mutationFn: (test: ResultTestWorkspacePublic) =>
      ResultsService.enterResults({
        orderId,
        requestBody: {
          order_item_id: test.order_item_id,
          values: (test.analytes ?? [])
            .filter((analyte) => dirty.has(analyteKey(test, analyte)))
            .filter((analyte) => analyte.data_type !== "image")
            .map((analyte) => ({
              analyte_id: analyte.analyte_id,
              specimen_id: analyte.specimen_id,
              result_value: values[analyteKey(test, analyte)] ?? "",
            })),
        },
      }),
    onSuccess: (response, test) => {
      showSuccessToast("Résultats enregistrés")
      const savedKeys = new Set(
        (test.analytes ?? [])
          .filter((analyte) => dirty.has(analyteKey(test, analyte)))
          .map((analyte) => analyteKey(test, analyte)),
      )
      setDirty(
        (current) => new Set([...current].filter((key) => !savedKeys.has(key))),
      )
      queryClient.setQueryData(
        ["result-workspace", orderId],
        response.workspace,
      )
      setCriticalResultId(response.critical_result_ids?.[0] ?? null)
      queryClient.invalidateQueries({ queryKey: ["result-queue"] })
    },
    onError: handleError.bind(showErrorToast),
  })
  const verifyOneMutation = useMutation({
    mutationFn: (resultId: string) => ResultsService.verifyResult({ resultId }),
    onSuccess: (workspace) => {
      showSuccessToast("Résultat vérifié")
      setVerificationSkips([])
      queryClient.setQueryData(["result-workspace", orderId], workspace)
      queryClient.invalidateQueries({ queryKey: ["result-queue"] })
    },
    onError: handleError.bind(showErrorToast),
  })
  const verifyAllMutation = useMutation({
    mutationFn: async () => {
      const dirtySnapshot = new Set(dirty)
      const criticalResultIds: string[] = []
      for (const test of query.data?.tests ?? []) {
        const testValues = (test.analytes ?? [])
          .filter((analyte) => dirtySnapshot.has(analyteKey(test, analyte)))
          .filter((analyte) => analyte.data_type !== "image")
          .map((analyte) => ({
            analyte_id: analyte.analyte_id,
            specimen_id: analyte.specimen_id,
            result_value: values[analyteKey(test, analyte)] ?? "",
          }))
        if (!testValues.length) continue
        const submission = await ResultsService.enterResults({
          orderId,
          requestBody: {
            order_item_id: test.order_item_id,
            values: testValues,
          },
        })
        criticalResultIds.push(...(submission.critical_result_ids ?? []))
      }
      const verification = await ResultsService.verifyOrder({ orderId })
      return { verification, criticalResultIds }
    },
    onSuccess: ({ verification, criticalResultIds }) => {
      const verifiedCount = verification.verified_count ?? 0
      const skippedCount = verification.skipped_count ?? 0
      showSuccessToast(
        skippedCount
          ? `${verifiedCount} résultat(s) vérifié(s), ${skippedCount} à traiter`
          : `${verifiedCount} résultat(s) vérifié(s)`,
      )
      setDirty(new Set())
      setVerificationSkips(verification.skipped ?? [])
      setCriticalResultId(criticalResultIds[0] ?? null)
      queryClient.setQueryData(
        ["result-workspace", orderId],
        verification.workspace,
      )
      queryClient.invalidateQueries({ queryKey: ["result-queue"] })
    },
    onError: handleError.bind(showErrorToast),
  })
  const commentMutation = useMutation({
    mutationFn: () =>
      ResultsService.addResultComment({
        resultId: commentResultId!,
        requestBody: { comment: comment.trim() },
      }),
    onSuccess: () => {
      showSuccessToast("Commentaire ajouté")
      setCommentResultId(null)
      setComment("")
      queryClient.invalidateQueries({ queryKey: ["result-workspace", orderId] })
    },
    onError: handleError.bind(showErrorToast),
  })
  const customizationMutation = useMutation({
    mutationFn: ({
      test,
      analyteIds,
      reason,
    }: {
      test: ResultTestWorkspacePublic
      analyteIds: string[]
      reason?: string
    }) =>
      OrdersService.customizeOrderItemAnalytes({
        id: orderId,
        itemId: test.order_item_id,
        requestBody: {
          analyte_ids: analyteIds,
          expected_revision: query.data!.revision_number ?? 1,
          reason: reason || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Analytes de l'examen mis à jour")
      setPendingCustomization(null)
      setCustomizationReason("")
      queryClient.invalidateQueries({ queryKey: ["result-workspace", orderId] })
      queryClient.invalidateQueries({ queryKey: ["order", orderId] })
      queryClient.invalidateQueries({ queryKey: ["result-queue"] })
    },
    onError: handleError.bind(showErrorToast),
  })
  const correctionMutation = useMutation({
    mutationFn: () =>
      correctionAnalyte?.data_type === "image"
        ? ResultsService.correctVerifiedImageResult({
            resultId: correctionAnalyte.result_id!,
            formData: {
              file: correctionFile!,
              reason: correctionReason.trim(),
            },
          })
        : ResultsService.correctVerifiedResult({
            resultId: correctionAnalyte!.result_id!,
            requestBody: {
              result_value: correctionValue,
              reason: correctionReason.trim(),
            },
          }),
    onSuccess: (workspace) => {
      showSuccessToast(
        "Résultat corrigé, une nouvelle vérification est requise",
      )
      setCorrectionAnalyte(null)
      setCorrectionValue("")
      setCorrectionReason("")
      setCorrectionFile(null)
      queryClient.setQueryData(["result-workspace", orderId], workspace)
      queryClient.invalidateQueries({ queryKey: ["result-queue"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const workspace = query.data
  const resultEntries = (workspace?.tests ?? []).flatMap((test) =>
    (test.analytes ?? []).map((analyte) => ({ test, analyte })),
  )
  const eligibleCount = resultEntries.filter(
    ({ test, analyte }) =>
      analyte.status !== "verified" &&
      (analyte.verification_eligible || dirty.has(analyteKey(test, analyte))),
  ).length
  const hasUnverifiedValue = resultEntries.some(
    ({ test, analyte }) =>
      analyte.status !== "verified" &&
      (Boolean(analyte.result_id) || dirty.has(analyteKey(test, analyte))),
  )
  const moveToNextResultEditor = (currentEditor: HTMLElement) => {
    const editors = Array.from(
      workspaceRef.current?.querySelectorAll<HTMLElement>(
        '[data-result-editor="true"]:not([disabled])',
      ) ?? [],
    )
    const currentIndex = editors.indexOf(currentEditor)
    if (currentIndex < 0) return
    editors[currentIndex + 1]?.focus()
  }

  if (query.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    )
  }
  if (!workspace) return <div>Demande introuvable.</div>

  return (
    <>
      <div
        ref={workspaceRef}
        className="-mt-4 space-y-5 lg:-mt-5"
        data-result-workspace="true"
      >
        <header className="sticky -top-4 z-10 -mx-4 border-b bg-background/95 px-4 py-2 backdrop-blur lg:-top-5 lg:-mx-5 lg:px-5">
          <div className="flex min-h-10 flex-wrap items-center gap-x-2 gap-y-2 lg:flex-nowrap">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    asChild
                    aria-label="Retour aux résultats"
                    className="shrink-0"
                  >
                    <Link to="/results">
                      <ArrowLeft className="size-4" />
                    </Link>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Retour aux résultats</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <div className="flex min-w-0 flex-1 flex-col items-start gap-0.5 lg:flex-row lg:items-center lg:gap-2">
              <div className="flex min-w-0 items-center gap-2">
                <h1 className="shrink-0 font-mono text-sm font-bold sm:text-base">
                  {workspace.accession_number}
                </h1>
                <Badge variant="outline" className="shrink-0">
                  {workspace.order_status}
                </Badge>
              </div>
              <div className="w-full min-w-0 truncate whitespace-nowrap text-xs lg:w-auto lg:border-l lg:pl-2 lg:text-sm">
                <span className="font-medium">{workspace.patient_name}</span>
                <span className="text-muted-foreground">
                  {" "}
                  · {workspace.patient_identifier}
                </span>
              </div>
            </div>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Afficher les détails du patient"
                  className="size-8 shrink-0 text-muted-foreground"
                >
                  <Info className="size-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="start" className="w-72">
                <PopoverHeader>
                  <PopoverTitle>{workspace.patient_name}</PopoverTitle>
                  <PopoverDescription>
                    Informations d'identification du patient
                  </PopoverDescription>
                </PopoverHeader>
                <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2">
                  <dt className="text-muted-foreground">Identifiant</dt>
                  <dd className="text-right font-medium">
                    {workspace.patient_identifier}
                  </dd>
                  <dt className="text-muted-foreground">Date de naissance</dt>
                  <dd className="text-right font-medium">
                    {workspace.patient_date_of_birth}
                  </dd>
                  {workspace.patient_context_name && (
                    <>
                      <dt className="text-muted-foreground">Contexte</dt>
                      <dd className="text-right font-medium">
                        {workspace.patient_context_name}
                      </dd>
                    </>
                  )}
                </dl>
              </PopoverContent>
            </Popover>

            <div className="flex w-full items-center justify-between gap-2 border-t pt-2 lg:ml-auto lg:w-auto lg:shrink-0 lg:border-t-0 lg:pt-0">
              <p className="whitespace-nowrap text-xs text-muted-foreground">
                <span className="font-medium text-foreground">
                  {workspace.resulted_count}/{workspace.total_count}
                </span>{" "}
                saisis ·{" "}
                <span className="font-medium text-foreground">
                  {workspace.verified_count}
                </span>{" "}
                vérifiés
              </p>
              {canVerify && (
                <LoadingButton
                  size="sm"
                  loading={verifyAllMutation.isPending}
                  disabled={!hasUnverifiedValue || saveMutation.isPending}
                  onClick={() => verifyAllMutation.mutate()}
                >
                  <CheckCheck className="size-4" />
                  {eligibleCount
                    ? `Vérifier ${eligibleCount}`
                    : "Tout vérifier"}
                </LoadingButton>
              )}
              {canViewReports && (
                <Button size="sm" variant="outline" asChild>
                  <Link to="/orders/$orderId/report" params={{ orderId }}>
                    <FileText className="size-4" />
                    Rapport
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </header>

        {(workspace.consistency_outcomes ?? []).map((outcome) => (
          <div
            key={outcome.rule_id}
            className="flex gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950"
          >
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <span>{outcome.message}</span>
          </div>
        ))}

        {verificationSkips.length > 0 && (
          <section className="border-l-2 border-amber-500 bg-amber-50 px-3 py-2 text-sm text-amber-950">
            <p className="font-semibold">
              {verificationSkips.length} résultat(s) non vérifié(s)
            </p>
            <ul className="mt-1 space-y-0.5">
              {verificationSkips.map((skip) => (
                <li
                  key={`${skip.order_item_id}:${skip.analyte_id}:${skip.specimen_id}`}
                >
                  <span className="font-medium">{skip.analyte_name}</span>
                  {" : "}
                  {skip.message}
                </li>
              ))}
            </ul>
          </section>
        )}

        {(workspace.tests ?? []).map((test) => {
          const analytes = test.analytes ?? []
          const orderedAnalytes: OrderAnalyteDetailPublic[] = []
          const actionRowKeys = new Set<string>()
          for (const analyte of analytes) {
            const existing = orderedAnalytes.find(
              (item) => item.analyte_id === analyte.analyte_id,
            )
            if (existing) {
              existing.has_result ||= Boolean(analyte.result_id)
              existing.has_verified_result ||= analyte.status === "verified"
              continue
            }
            orderedAnalytes.push({
              analyte_id: analyte.analyte_id,
              analyte_code: analyte.analyte_code,
              analyte_name: analyte.analyte_name,
              analyte_data_type: analyte.data_type,
              unit_name: analyte.unit_name,
              sort_order: orderedAnalytes.length,
              has_result: Boolean(analyte.result_id),
              has_verified_result: analyte.status === "verified",
            })
            actionRowKeys.add(analyteKey(test, analyte))
          }
          const updateAnalytes = (
            analyteIds: string[],
            removed?: OrderAnalyteDetailPublic,
          ) => {
            const requiresReason =
              workspace.order_status === "completed" ||
              Boolean(removed?.has_result)
            if (requiresReason) {
              setPendingCustomization({ test, analyteIds })
              setCustomizationReason("")
              return
            }
            customizationMutation.mutate({ test, analyteIds })
          }
          const isMultiParameter = analytes.length > 1
          const dirtyForTest = analytes.some((analyte) =>
            dirty.has(analyteKey(test, analyte)),
          )
          const isSavingTest =
            saveMutation.isPending &&
            saveMutation.variables?.order_item_id === test.order_item_id
          const saveAction =
            (canEnter || canEdit) && dirtyForTest ? (
              <Button
                size="icon"
                disabled={saveMutation.isPending || verifyAllMutation.isPending}
                onClick={() => saveMutation.mutate(test)}
                aria-label={
                  isSavingTest
                    ? "Enregistrement des résultats"
                    : "Enregistrer les résultats"
                }
                title={
                  isSavingTest ? "Enregistrement…" : "Enregistrer les résultats"
                }
              >
                {isSavingTest ? <Loader2 className="animate-spin" /> : <Save />}
              </Button>
            ) : null
          return (
            <section
              key={test.order_item_id}
              className="overflow-hidden rounded-md border"
            >
              {isMultiParameter && (
                <div className="flex min-h-11 items-center justify-between gap-3 border-b bg-muted/30 px-3 py-1.5">
                  <div className="min-w-0">
                    <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                      Test
                    </p>
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="truncate text-sm font-semibold">
                        {test.catalog_name}
                      </span>
                      {test.is_reflex_added && (
                        <Badge variant="secondary">Réflexe</Badge>
                      )}
                    </div>
                  </div>
                  {saveAction}
                </div>
              )}
              <div className="grid divide-y xl:grid-cols-[minmax(180px,32fr)_minmax(220px,42fr)_100px_240px_136px]">
                {analytes.map((analyte) => {
                  const key = analyteKey(test, analyte)
                  const customizationIndex = orderedAnalytes.findIndex(
                    (item) => item.analyte_id === analyte.analyte_id,
                  )
                  const customizationAnalyte =
                    orderedAnalytes[customizationIndex]
                  const canModifyResults = canEnter || canEdit
                  return (
                    <AnalyteRow
                      key={key}
                      test={test}
                      analyte={analyte}
                      title={
                        isMultiParameter
                          ? analyte.analyte_name
                          : test.catalog_name
                      }
                      showReflex={
                        !isMultiParameter && Boolean(test.is_reflex_added)
                      }
                      saveAction={!isMultiParameter ? saveAction : null}
                      value={values[key] ?? ""}
                      editable={
                        canModifyResults &&
                        analyte.status !== "verified" &&
                        !analyte.is_calculated
                      }
                      imageDisabledReason={imageUploadDisabledReason(
                        analyte,
                        canModifyResults,
                      )}
                      onChange={(value) => {
                        setVerificationSkips([])
                        setValues((current) => ({ ...current, [key]: value }))
                        setDirty((current) => new Set(current).add(key))
                      }}
                      onAdvanceResult={moveToNextResultEditor}
                      onImageUploaded={(criticalId) => {
                        setVerificationSkips([])
                        setCriticalResultId(criticalId)
                      }}
                      onVerify={() =>
                        analyte.result_id &&
                        verifyOneMutation.mutate(analyte.result_id)
                      }
                      onComment={() =>
                        setCommentResultId(analyte.result_id ?? null)
                      }
                      onCorrect={() => {
                        setCorrectionAnalyte(analyte)
                        setCorrectionValue(analyte.result_value ?? "")
                        setCorrectionReason("")
                        setCorrectionFile(null)
                      }}
                      customization={
                        canCustomize &&
                        actionRowKeys.has(key) &&
                        customizationAnalyte
                          ? {
                              analyte: customizationAnalyte,
                              index: customizationIndex,
                              length: orderedAnalytes.length,
                              busy: customizationMutation.isPending,
                              onMove: (direction) => {
                                const next = orderedAnalytes.map(
                                  (item) => item.analyte_id,
                                )
                                const target = customizationIndex + direction
                                ;[next[customizationIndex], next[target]] = [
                                  next[target],
                                  next[customizationIndex],
                                ]
                                updateAnalytes(next)
                              },
                              onRemove: () =>
                                updateAnalytes(
                                  orderedAnalytes
                                    .filter(
                                      (item) =>
                                        item.analyte_id !== analyte.analyte_id,
                                    )
                                    .map((item) => item.analyte_id),
                                  customizationAnalyte,
                                ),
                            }
                          : null
                      }
                      canVerify={canVerify}
                      canCorrect={canEdit}
                      verifying={verifyOneMutation.isPending}
                      orderId={orderId}
                    />
                  )
                })}
              </div>
              {canCustomize && (
                <div className="border-t bg-muted/10 px-3 py-2">
                  <AddAnalyteControl
                    analytes={orderedAnalytes}
                    busy={customizationMutation.isPending}
                    onAdd={(analyteId) =>
                      updateAnalytes([
                        ...orderedAnalytes.map((item) => item.analyte_id),
                        analyteId,
                      ])
                    }
                  />
                </div>
              )}
            </section>
          )
        })}
      </div>
      <CriticalEscalationDialog
        resultId={criticalResultId}
        orderId={orderId}
        onOpenChange={(open) => !open && setCriticalResultId(null)}
      />
      <Dialog
        open={commentResultId !== null}
        onOpenChange={(open) => !open && setCommentResultId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter un commentaire</DialogTitle>
          </DialogHeader>
          <Textarea
            value={comment}
            onChange={(event) => setComment(event.currentTarget.value)}
            autoFocus
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCommentResultId(null)}>
              Annuler
            </Button>
            <LoadingButton
              loading={commentMutation.isPending}
              disabled={!comment.trim()}
              onClick={() => commentMutation.mutate()}
            >
              Ajouter
            </LoadingButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={pendingCustomization !== null}
        onOpenChange={(open) => !open && setPendingCustomization(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmer la modification des analytes</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Motif clinique *</Label>
            <Textarea
              value={customizationReason}
              onChange={(event) =>
                setCustomizationReason(event.currentTarget.value)
              }
              autoFocus
              placeholder="Expliquez pourquoi la composition de l'examen change…"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setPendingCustomization(null)}
            >
              Annuler
            </Button>
            <LoadingButton
              loading={customizationMutation.isPending}
              disabled={!customizationReason.trim()}
              onClick={() =>
                pendingCustomization &&
                customizationMutation.mutate({
                  ...pendingCustomization,
                  reason: customizationReason.trim(),
                })
              }
            >
              Confirmer
            </LoadingButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={correctionAnalyte !== null}
        onOpenChange={(open) => !open && setCorrectionAnalyte(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Corriger {correctionAnalyte?.analyte_name ?? "le résultat"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {correctionAnalyte?.data_type === "image" ? (
              <div className="space-y-2">
                <Label>Nouvelle image *</Label>
                <Input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(event) =>
                    setCorrectionFile(event.currentTarget.files?.[0] ?? null)
                  }
                  autoFocus
                />
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Nouvelle valeur *</Label>
                <Input
                  value={correctionValue}
                  onChange={(event) =>
                    setCorrectionValue(event.currentTarget.value)
                  }
                  placeholder={
                    correctionAnalyte?.data_type === "numeric"
                      ? "Saisir une valeur…"
                      : "Saisir un résultat…"
                  }
                  autoFocus
                />
              </div>
            )}
            <div className="space-y-2">
              <Label>Motif de correction *</Label>
              <Textarea
                value={correctionReason}
                onChange={(event) =>
                  setCorrectionReason(event.currentTarget.value)
                }
                placeholder="Justification visible dans l'audit…"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCorrectionAnalyte(null)}
            >
              Annuler
            </Button>
            <LoadingButton
              loading={correctionMutation.isPending}
              disabled={
                !correctionReason.trim() ||
                (correctionAnalyte?.data_type === "image"
                  ? !correctionFile
                  : !correctionValue.trim())
              }
              onClick={() => correctionMutation.mutate()}
            >
              Corriger et rouvrir
            </LoadingButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

function AnalyteRow({
  test,
  analyte,
  title,
  showReflex,
  saveAction,
  value,
  editable,
  onChange,
  onAdvanceResult,
  onImageUploaded,
  imageDisabledReason,
  onVerify,
  onComment,
  onCorrect,
  customization,
  canVerify,
  canCorrect,
  verifying,
  orderId,
}: {
  test: ResultTestWorkspacePublic
  analyte: ResultAnalyteWorkspacePublic
  title: string
  showReflex: boolean
  saveAction: ReactNode
  value: string
  editable: boolean
  onChange: (value: string) => void
  onAdvanceResult: (currentEditor: HTMLElement) => void
  onImageUploaded: (criticalId: string | null) => void
  imageDisabledReason: string | null
  onVerify: () => void
  onComment: () => void
  onCorrect: () => void
  customization: {
    analyte: OrderAnalyteDetailPublic
    index: number
    length: number
    busy: boolean
    onMove: (direction: -1 | 1) => void
    onRemove: () => void
  } | null
  canVerify: boolean
  canCorrect: boolean
  verifying: boolean
  orderId: string
}) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      ResultsService.uploadResultImage({
        orderId,
        formData: {
          order_item_id: test.order_item_id,
          analyte_id: analyte.analyte_id,
          specimen_id: analyte.specimen_id,
          file,
        },
      }),
    onSuccess: (response) => {
      showSuccessToast("Image enregistrée")
      queryClient.setQueryData(
        ["result-workspace", orderId],
        response.workspace,
      )
      queryClient.invalidateQueries({ queryKey: ["result-queue"] })
      if (fileInputRef.current) fileInputRef.current.value = ""
      onImageUploaded(response.critical_result_ids?.[0] ?? null)
    },
    onError: handleError.bind(showErrorToast),
  })
  const options = useMemo(
    () =>
      Array.isArray(analyte.options_data)
        ? analyte.options_data.filter(
            (option): option is string => typeof option === "string",
          )
        : [],
    [analyte.options_data],
  )
  return (
    <div className="col-span-full grid gap-2 px-3 py-2 xl:grid-cols-subgrid xl:items-center">
      <div className="min-w-0 xl:border-l xl:border-border/70 xl:pl-3">
        <div className="flex min-w-0 items-center gap-2">
          <span className="truncate text-[13px] font-medium">{title}</span>
          {showReflex && <Badge variant="secondary">Réflexe</Badge>}
        </div>
      </div>
      <div className="min-w-0">
        {analyte.data_type === "numeric" && (
          <Input
            inputMode="decimal"
            value={value}
            placeholder="Saisir une valeur…"
            disabled={!editable}
            data-result-editor="true"
            onChange={(event) => onChange(event.currentTarget.value)}
            onKeyDown={(event) => {
              if (event.key !== "Enter") return
              event.preventDefault()
              onAdvanceResult(event.currentTarget)
            }}
            className="h-8 font-mono"
          />
        )}
        {analyte.data_type === "text" && (
          <Textarea
            value={value}
            placeholder="Saisir un résultat…"
            disabled={!editable}
            data-result-editor="true"
            onChange={(event) => onChange(event.currentTarget.value)}
            onKeyDown={(event) => {
              if (event.key !== "Enter" || !event.ctrlKey) return
              event.preventDefault()
              onAdvanceResult(event.currentTarget)
            }}
            className="min-h-8 py-1.5"
          />
        )}
        {analyte.data_type === "options" && (
          <Select value={value} disabled={!editable} onValueChange={onChange}>
            <SelectTrigger
              className="h-8 w-full"
              data-result-editor="true"
              onKeyDown={(event) => {
                if (event.key !== "Enter") return
                event.preventDefault()
                onAdvanceResult(event.currentTarget)
              }}
            >
              <SelectValue placeholder="Sélectionner…" />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {analyte.data_type === "image" && (
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="flex min-w-0 items-center gap-2">
              {analyte.image_url ? (
                <a
                  href={analyte.image_url}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded border bg-muted/20 p-0.5"
                  title="Ouvrir l'image"
                >
                  <img
                    src={analyte.image_url}
                    alt={analyte.analyte_name}
                    className="size-10 rounded-sm object-cover"
                  />
                </a>
              ) : (
                <div className="flex size-10 items-center justify-center rounded border border-dashed bg-muted/20 text-muted-foreground">
                  <ImageUp className="size-4" />
                </div>
              )}
              <div className="min-w-0">
                <p className="truncate text-xs font-medium">
                  {analyte.image_url ? "Image enregistrée" : "Aucune image"}
                </p>
                {imageDisabledReason && (
                  <p className="truncate text-[11px] text-muted-foreground">
                    {imageDisabledReason}
                  </p>
                )}
              </div>
            </div>
            <Button
              type="button"
              variant={analyte.image_url ? "outline" : "default"}
              size="lg"
              disabled={!editable || uploadMutation.isPending}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploadMutation.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <ImageUp className="size-4" />
              )}
              {uploadMutation.isPending
                ? "Envoi..."
                : analyte.image_url
                  ? "Remplacer l'image"
                  : "Téléverser une image"}
            </Button>
            <Input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="sr-only"
              disabled={!editable || uploadMutation.isPending}
              onChange={(event) => {
                const file = event.currentTarget.files?.[0]
                if (file) uploadMutation.mutate(file)
              }}
            />
          </div>
        )}
      </div>
      <div className="min-w-0 truncate text-sm text-muted-foreground">
        {analyte.unit_name ?? ""}
      </div>
      <div className="flex min-h-8 flex-wrap items-center justify-start gap-1">
        {analyte.is_abnormal && <Badge variant="outline">Anormal</Badge>}
        {analyte.delta_flag && <Badge variant="secondary">Delta</Badge>}
        {analyte.is_critical && <Badge variant="destructive">Critique</Badge>}
        {analyte.escalation_required && (
          <Badge variant="destructive">
            <AlertTriangle className="size-3" />À notifier
          </Badge>
        )}
        {canCorrect && analyte.status === "verified" && (
          <Badge variant="outline">
            <Check className="size-3" />
            Vérifié
          </Badge>
        )}
      </div>
      <div className="flex min-h-8 w-full min-w-0 items-center justify-end gap-1 pr-2">
        {analyte.result_id && (
          <Button
            variant="ghost"
            size="icon"
            aria-label="Ajouter un commentaire"
            onClick={onComment}
          >
            <MessageSquarePlus className="size-4" />
          </Button>
        )}
        {canCorrect && analyte.status === "verified" && (
          <Button
            variant="ghost"
            size="icon"
            aria-label="Corriger le résultat vérifié"
            title="Corriger le résultat vérifié"
            onClick={onCorrect}
          >
            <Pencil className="size-4" />
          </Button>
        )}
        {canVerify && analyte.result_id && analyte.status === "resulted" && (
          <Button
            size="icon"
            variant="outline"
            aria-label="Vérifier le résultat"
            title={analyte.verification_blocker ?? "Vérifier"}
            disabled={!analyte.verification_eligible || verifying}
            onClick={onVerify}
          >
            <Check className="size-4" />
          </Button>
        )}
        {customization && (
          <TestAnalyteActionsMenu
            analyte={customization.analyte}
            index={customization.index}
            length={customization.length}
            busy={customization.busy}
            onMove={customization.onMove}
            onRemove={customization.onRemove}
          />
        )}
        {saveAction}
      </div>
      {(analyte.comments ?? []).length > 0 && (
        <div className="space-y-1 text-xs text-muted-foreground xl:col-span-4 xl:col-start-2">
          {(analyte.comments ?? []).map((item) => (
            <p key={item.id}>
              <span className="font-medium text-foreground">
                {item.user_name}:
              </span>{" "}
              {item.comment}
            </p>
          ))}
        </div>
      )}
      {(analyte.corrections ?? []).length > 0 && (
        <div className="space-y-1 text-xs text-muted-foreground xl:col-span-4 xl:col-start-2">
          {(analyte.corrections ?? []).map((item) => (
            <p key={item.id}>
              <span className="font-medium text-foreground">
                Correction par {item.performed_by_name ?? "Utilisateur"}:
              </span>{" "}
              {item.old_value ?? "—"} → {item.new_value ?? "—"} · {item.reason}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

function analyteKey(
  test: ResultTestWorkspacePublic,
  analyte: ResultAnalyteWorkspacePublic,
) {
  return `${test.order_item_id}:${analyte.analyte_id}:${analyte.specimen_id}`
}

function imageUploadDisabledReason(
  analyte: ResultAnalyteWorkspacePublic,
  canModifyResults: boolean,
) {
  if (analyte.data_type !== "image") return null
  if (!canModifyResults) {
    return "Droits insuffisants pour saisir ou modifier ce résultat."
  }
  if (analyte.status === "verified") {
    return "Résultat vérifié : utilisez la correction pour remplacer l'image."
  }
  if (analyte.is_calculated) {
    return "Analyte calculé : image non modifiable."
  }
  return null
}
