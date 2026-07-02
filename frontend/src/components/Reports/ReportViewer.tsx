import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  History,
  Mail,
  MessageCircle,
  Printer,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

import type { ReportChannel, ReportPublic } from "@/client"
import { ReportsService } from "@/client"
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
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"
import { ReportDocument, type ReportDocumentHandle } from "./ReportDocument"
import {
  ReportRenderSettingsContent,
  ReportRenderSettingsSheet,
} from "./ReportRenderSettingsSheet"
import {
  asReportSnapshot,
  asTemplateSnapshot,
  defaultReportRenderConfig,
  normalizeReportRenderConfig,
  type ReportRenderConfig,
} from "./reportTypes"

export function ReportViewer({ orderId }: { orderId: string }) {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const canRelease = usePermission("reports", "release")
  const [selectedReport, setSelectedReport] = useState<ReportPublic | null>(
    null,
  )
  const [deliveryChannel, setDeliveryChannel] = useState<ReportChannel | null>(
    null,
  )
  const [recipient, setRecipient] = useState("")
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [canUseInlineSettings, setCanUseInlineSettings] = useState(false)
  const [reportReady, setReportReady] = useState(false)
  const reportDocumentRef = useRef<ReportDocumentHandle>(null)
  const [draftRenderConfig, setDraftRenderConfig] =
    useState<ReportRenderConfig>(() => defaultReportRenderConfig())

  useEffect(() => {
    if (!orderId) return
    setDraftRenderConfig(defaultReportRenderConfig())
    setSelectedReport(null)
    setReportReady(false)
  }, [orderId])

  useEffect(() => {
    const query = window.matchMedia("(min-width: 1024px)")
    const update = () => setCanUseInlineSettings(query.matches)
    update()
    query.addEventListener("change", update)
    return () => query.removeEventListener("change", update)
  }, [])

  const printReport = useCallback(() => {
    reportDocumentRef.current?.print()
  }, [])

  const previewQuery = useQuery({
    queryKey: ["report-preview", orderId],
    queryFn: () => ReportsService.readOrderReportPreview({ orderId }),
  })
  const historyQuery = useQuery({
    queryKey: ["order-reports", orderId],
    queryFn: () => ReportsService.readOrderReports({ orderId }),
  })
  const releaseMutation = useMutation({
    mutationFn: () =>
      ReportsService.releaseOrderReport({
        orderId,
        requestBody: { channel: "print", render_config: draftRenderConfig },
      }),
    onSuccess: (report) => {
      setSelectedReport(report)
      showSuccessToast(`Rapport version ${report.version} publié`)
      queryClient.invalidateQueries({ queryKey: ["order-reports", orderId] })
    },
    onError: handleError.bind(showErrorToast),
  })
  const deliveryMutation = useMutation({
    mutationFn: () => {
      const requestBody = {
        channel: deliveryChannel!,
        recipient: recipient.trim(),
        ...(!selectedReport ? { render_config: draftRenderConfig } : {}),
      }
      return selectedReport
        ? ReportsService.deliverReport({
            reportId: selectedReport.id,
            requestBody,
          })
        : ReportsService.releaseOrderReport({
            orderId,
            requestBody,
          })
    },
    onSuccess: (report) => {
      setSelectedReport(report)
      setDeliveryChannel(null)
      setRecipient("")
      showSuccessToast(
        deliveryChannel === "email"
          ? selectedReport
            ? "Rapport envoyé par e-mail"
            : "Rapport publié et envoyé par e-mail"
          : selectedReport
            ? "Rapport envoyé par WhatsApp"
            : "Rapport publié et envoyé par WhatsApp",
      )
      queryClient.invalidateQueries({ queryKey: ["order-reports", orderId] })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["order-reports", orderId] })
    },
  })

  const preview = previewQuery.data
  const activeReport =
    selectedReport ??
    historyQuery.data?.data.find((report) => !report.is_voided) ??
    null
  const snapshot = activeReport?.snapshot ?? preview?.snapshot
  const templates =
    activeReport?.template_snapshot ?? preview?.template_snapshot
  const reportSnapshot = useMemo(
    () => (snapshot ? asReportSnapshot(snapshot) : null),
    [snapshot],
  )
  const templateSnapshot = useMemo(
    () => (templates ? asTemplateSnapshot(templates) : null),
    [templates],
  )
  const renderConfig = useMemo(
    () =>
      activeReport
        ? normalizeReportRenderConfig(
            activeReport.render_config as Partial<ReportRenderConfig> | null,
          )
        : draftRenderConfig,
    [activeReport, draftRenderConfig],
  )
  const accessionNumber = reportSnapshot?.order.accession_number ?? ""

  if (previewQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="mx-auto h-[800px] max-w-3xl" />
      </div>
    )
  }

  return (
    <>
      <div className="report-screen -mt-4 space-y-4 lg:-mt-5">
        <header className="sticky -top-4 z-20 -mx-4 flex flex-wrap items-center gap-2 border-b bg-background/95 px-4 py-3 backdrop-blur lg:-top-5 lg:-mx-5 lg:px-5">
          <Button variant="ghost" size="icon" asChild aria-label="Retour">
            <Link to="/orders/$orderId" params={{ orderId }}>
              <ArrowLeft className="size-4" />
            </Link>
          </Button>
          <div className="mr-auto">
            <div className="flex items-center gap-2">
              <h1 className="font-semibold">Compte rendu</h1>
              {activeReport ? (
                <>
                  <Badge
                    variant={activeReport.is_voided ? "destructive" : "outline"}
                  >
                    Version {activeReport.version}
                    {activeReport.is_voided ? " · Annulée" : ""}
                  </Badge>
                  {activeReport.channel === "email" && (
                    <Badge
                      variant={
                        activeReport.delivery_status === "failed"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {activeReport.delivery_status === "sent"
                        ? "E-mail envoyé"
                        : activeReport.delivery_status === "failed"
                          ? "Échec e-mail"
                          : "E-mail en attente"}
                    </Badge>
                  )}
                  {activeReport.channel === "whatsapp" && (
                    <Badge
                      variant={
                        activeReport.delivery_status === "failed"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {activeReport.delivery_status === "sent"
                        ? "WhatsApp envoyé"
                        : activeReport.delivery_status === "failed"
                          ? "Échec WhatsApp"
                          : "WhatsApp en attente"}
                    </Badge>
                  )}
                </>
              ) : (
                <Badge variant="secondary">Aperçu</Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">{accessionNumber}</p>
          </div>

          <div className="flex items-center gap-2">
            {(historyQuery.data?.data.length ?? 0) > 0 && (
              <div className="flex items-center gap-1 rounded-md border p-1">
                <History className="mx-1 size-4 text-muted-foreground" />
                {(historyQuery.data?.data ?? []).map((report) => (
                  <Button
                    key={report.id}
                    size="sm"
                    variant={
                      activeReport?.id === report.id ? "secondary" : "ghost"
                    }
                    onClick={() => setSelectedReport(report)}
                  >
                    v{report.version}
                  </Button>
                ))}
              </div>
            )}
            <Button
              variant="outline"
              disabled={!reportReady}
              onClick={printReport}
            >
              <Printer className="size-4" />
              Imprimer
            </Button>
            {reportSnapshot && (
              <Button
                variant={settingsOpen ? "secondary" : "outline"}
                onClick={() => setSettingsOpen((open) => !open)}
              >
                <SlidersHorizontal className="size-4" />
                Configurer le rendu
              </Button>
            )}
            {activeReport && !activeReport.is_voided && (
              <>
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Envoyer par e-mail"
                  onClick={() => setDeliveryChannel("email")}
                >
                  <Mail className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Envoyer par WhatsApp"
                  onClick={() => setDeliveryChannel("whatsapp")}
                >
                  <MessageCircle className="size-4" />
                </Button>
              </>
            )}
            {canRelease && !activeReport && (
              <>
                <LoadingButton
                  loading={releaseMutation.isPending}
                  disabled={!preview?.can_release}
                  onClick={() => releaseMutation.mutate()}
                >
                  <ShieldCheck className="size-4" />
                  Publier
                </LoadingButton>
                <Button
                  disabled={!preview?.can_release}
                  onClick={() => setDeliveryChannel("email")}
                >
                  <Mail className="size-4" />
                  Publier et envoyer
                </Button>
                <Button
                  disabled={!preview?.can_release}
                  variant="outline"
                  onClick={() => setDeliveryChannel("whatsapp")}
                >
                  <MessageCircle className="size-4" />
                  Publier via WhatsApp
                </Button>
              </>
            )}
          </div>
        </header>

        {!activeReport && (preview?.blockers?.length ?? 0) > 0 && (
          <div className="mx-auto flex max-w-[210mm] gap-3 border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <div>
              <p className="font-medium">Publication indisponible</p>
              <ul className="mt-1 list-disc pl-4">
                {preview?.blockers?.map((blocker) => (
                  <li key={blocker}>{blocker}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {reportSnapshot && templateSnapshot ? (
          <div
            className={
              settingsOpen && canUseInlineSettings
                ? "grid min-w-0 items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(22rem,25rem)]"
                : "min-w-0"
            }
          >
            <div className="min-w-0 overflow-x-auto pb-4">
              <ReportDocument
                ref={reportDocumentRef}
                snapshot={reportSnapshot}
                templates={templateSnapshot}
                renderConfig={renderConfig}
                voided={activeReport?.is_voided}
                onReadyChange={setReportReady}
              />
            </div>
            {settingsOpen && canUseInlineSettings && reportSnapshot && (
              <aside className="sticky top-16 hidden h-[calc(100vh-5rem)] min-h-0 w-full justify-self-end overflow-hidden rounded-md border bg-popover text-xs/relaxed text-popover-foreground shadow-sm lg:flex lg:flex-col">
                <div className="flex shrink-0 items-start justify-between gap-3 border-b p-4">
                  <div>
                    <h2 className="font-heading text-sm font-medium text-foreground">
                      Configurer le rendu
                    </h2>
                    <p className="mt-1 text-xs/relaxed text-muted-foreground">
                      {activeReport
                        ? "Configuration figée pour cette version publiée."
                        : "Ces réglages seront enregistrés avec la version publiée."}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    aria-label="Fermer la configuration"
                    onClick={() => setSettingsOpen(false)}
                  >
                    <X className="size-4" />
                  </Button>
                </div>
                <ReportRenderSettingsContent
                  snapshot={reportSnapshot}
                  value={renderConfig}
                  onChange={setDraftRenderConfig}
                  readOnly={Boolean(activeReport)}
                />
              </aside>
            )}
          </div>
        ) : (
          <p className="py-20 text-center text-muted-foreground">
            Aperçu indisponible.
          </p>
        )}
      </div>

      {reportSnapshot && !canUseInlineSettings && (
        <ReportRenderSettingsSheet
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          snapshot={reportSnapshot}
          value={renderConfig}
          onChange={setDraftRenderConfig}
          readOnly={Boolean(activeReport)}
        />
      )}

      <Dialog
        open={Boolean(deliveryChannel)}
        onOpenChange={(open) => {
          if (!open) setDeliveryChannel(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Envoyer par {deliveryChannel === "email" ? "e-mail" : "WhatsApp"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="report-recipient">
              {deliveryChannel === "email" ? "Adresse e-mail" : "Numéro"}
            </Label>
            <Input
              id="report-recipient"
              type={deliveryChannel === "email" ? "email" : "tel"}
              value={recipient}
              onChange={(event) => setRecipient(event.currentTarget.value)}
              placeholder={
                deliveryChannel === "email"
                  ? "patient@example.com"
                  : "+223 70 00 00 00"
              }
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              {deliveryChannel === "email"
                ? "Le compte rendu sera envoyé immédiatement par e-mail."
                : "Le compte rendu PDF sera envoyé immédiatement par WhatsApp si le service est configuré."}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeliveryChannel(null)}>
              Annuler
            </Button>
            <LoadingButton
              loading={deliveryMutation.isPending}
              disabled={!recipient.trim()}
              onClick={() => deliveryMutation.mutate()}
            >
              <Send className="size-4" />
              {selectedReport ? "Envoyer" : "Publier et envoyer"}
            </LoadingButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
