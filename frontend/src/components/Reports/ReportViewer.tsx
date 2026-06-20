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
} from "lucide-react"
import { useEffect, useState } from "react"

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
import { ReportDocument } from "./ReportDocument"
import { asReportSnapshot, asTemplateSnapshot } from "./reportTypes"

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

  useEffect(() => {
    const startReportPrint = () => {
      document.body.dataset.printTarget = "report"
    }
    const finishReportPrint = () => {
      if (document.body.dataset.printTarget === "report") {
        delete document.body.dataset.printTarget
      }
    }

    window.addEventListener("beforeprint", startReportPrint)
    window.addEventListener("afterprint", finishReportPrint)
    return () => {
      window.removeEventListener("beforeprint", startReportPrint)
      window.removeEventListener("afterprint", finishReportPrint)
      finishReportPrint()
    }
  }, [])

  const printReport = () => {
    document.body.dataset.printTarget = "report"
    window.print()
  }

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
        requestBody: { channel: "print" },
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
          : "Demande d’envoi WhatsApp enregistrée",
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
  const accessionNumber = snapshot
    ? asReportSnapshot(snapshot).order.accession_number
    : ""

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
            <Button variant="outline" onClick={printReport}>
              <Printer className="size-4" />
              Imprimer
            </Button>
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

        {snapshot && templates ? (
          <ReportDocument
            snapshot={asReportSnapshot(snapshot)}
            templates={asTemplateSnapshot(templates)}
            voided={activeReport?.is_voided}
          />
        ) : (
          <p className="py-20 text-center text-muted-foreground">
            Aperçu indisponible.
          </p>
        )}
      </div>

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
                : "L’envoi WhatsApp restera en attente de configuration."}
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
