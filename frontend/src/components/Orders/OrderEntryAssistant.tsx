import { useMutation } from "@tanstack/react-query"
import {
  AlertTriangle,
  Check,
  FlaskConical,
  Loader2,
  Mic,
  MicOff,
  Sparkles,
  Stethoscope,
  UserRound,
} from "lucide-react"
import type { ReactNode } from "react"
import { useMemo, useState } from "react"

import type {
  ApiError,
  CatalogDetailPublic,
  DoctorWithTitlePublic,
  OrderEntryAssistantDoctorDraft,
  OrderEntryAssistantPatientDraft,
  OrderEntryAssistantResponse,
  PatientPublic,
} from "@/client"
import { OrdersService } from "@/client"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { handleError } from "@/utils"
import { formatMoney } from "./utils"

interface OrderEntryAssistantProps {
  selected: Map<string, CatalogDetailPublic>
  onCatalogsChange: (selected: Map<string, CatalogDetailPublic>) => void
  canCreatePatient: boolean
  canCreateDoctor: boolean
  onSelectPatient: (patient: PatientPublic) => void
  onDraftPatient: (draft: OrderEntryAssistantPatientDraft) => void
  onSelectDoctor: (doctor: DoctorWithTitlePublic) => void
  onDraftDoctor: (draft: OrderEntryAssistantDoctorDraft) => void
}

interface SpeechRecognitionResultItem {
  transcript: string
}

interface SpeechRecognitionAlternativeList {
  readonly length: number
  item(index: number): SpeechRecognitionResultItem
  [index: number]: SpeechRecognitionResultItem
}

interface SpeechRecognitionResultListLike {
  readonly length: number
  item(index: number): SpeechRecognitionAlternativeList
  [index: number]: SpeechRecognitionAlternativeList
}

interface SpeechRecognitionEventLike {
  resultIndex: number
  results: SpeechRecognitionResultListLike
}

interface SpeechRecognitionLike {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
  start: () => void
  stop: () => void
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionLike
}

type SpeechWindow = Window &
  typeof globalThis & {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }

export function OrderEntryAssistant({
  selected,
  onCatalogsChange,
  canCreatePatient,
  canCreateDoctor,
  onSelectPatient,
  onDraftPatient,
  onSelectDoctor,
  onDraftDoctor,
}: OrderEntryAssistantProps) {
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [open, setOpen] = useState(false)
  const [text, setText] = useState("")
  const [response, setResponse] = useState<OrderEntryAssistantResponse | null>(
    null,
  )
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(
    new Set(),
  )
  const [isApplying, setIsApplying] = useState(false)
  const [recognition, setRecognition] = useState<SpeechRecognitionLike | null>(
    null,
  )

  const SpeechRecognition = useMemo(() => {
    if (typeof window === "undefined") return undefined
    const speechWindow = window as SpeechWindow
    return (
      speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition
    )
  }, [])
  const canDictate = !!SpeechRecognition
  const isListening = recognition !== null

  const intakeMutation = useMutation({
    mutationFn: () =>
      OrdersService.generateOrderEntryIntake({
        requestBody: { text: text.trim() },
      }),
    onSuccess: (payload) => {
      setResponse(payload)
      setSelectedSuggestions(
        new Set(
          (payload.catalog_suggestions ?? [])
            .filter((suggestion) => suggestion.confidence >= 0.65)
            .map((suggestion) => suggestion.catalog.id),
        ),
      )
    },
    onError: handleError.bind(showErrorToast),
  })

  const resetAssistant = () => {
    if (recognition) {
      recognition.stop()
      setRecognition(null)
    }
    setText("")
    setResponse(null)
    setSelectedSuggestions(new Set())
    intakeMutation.reset()
  }

  const toggleDictation = () => {
    if (recognition) {
      recognition.stop()
      setRecognition(null)
      return
    }
    if (!SpeechRecognition) return
    const nextRecognition = new SpeechRecognition()
    nextRecognition.lang = "fr-FR"
    nextRecognition.interimResults = false
    nextRecognition.continuous = true
    nextRecognition.onresult = (event) => {
      const chunks: string[] = []
      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        const result = event.results[index] ?? event.results.item(index)
        const item = result[0] ?? result.item(0)
        if (item?.transcript) chunks.push(item.transcript)
      }
      if (chunks.length > 0) {
        setText((current) =>
          [current.trim(), chunks.join(" ").trim()].filter(Boolean).join(" "),
        )
      }
    }
    nextRecognition.onend = () => setRecognition(null)
    nextRecognition.onerror = () => {
      setRecognition(null)
      showErrorToast("La dictée vocale n'a pas pu démarrer.")
    }
    nextRecognition.start()
    setRecognition(nextRecognition)
  }

  const applySelectedCatalogs = async () => {
    const suggestions = response?.catalog_suggestions ?? []
    const selectedIds = suggestions
      .filter((suggestion) => selectedSuggestions.has(suggestion.catalog.id))
      .map((suggestion) => suggestion.catalog.id)
    if (selectedIds.length === 0) return

    setIsApplying(true)
    try {
      const next = new Map(selected)
      const missingIds = selectedIds.filter((id) => !next.has(id))
      const details = await Promise.all(
        missingIds.map((id) => OrdersService.readOrderCatalogOption({ id })),
      )
      for (const detail of details) next.set(detail.id, detail)
      onCatalogsChange(next)
      showSuccessToast("Examens ajoutés à la demande")
      resetAssistant()
      setOpen(false)
    } catch (error) {
      handleError.bind(showErrorToast)(error as ApiError)
    } finally {
      setIsApplying(false)
    }
  }

  const hasText = text.trim().length >= 3
  const suggestions = response?.catalog_suggestions ?? []

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline">
          <Sparkles className="size-4" />
          Assistant IA
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-6xl">
        <DialogHeader>
          <DialogTitle>Assistant de saisie rapide</DialogTitle>
          <DialogDescription>
            Dictez ou collez la demande, puis vérifiez les propositions avant de
            les appliquer.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="flex justify-end">
            {canDictate && (
              <Button
                type="button"
                variant={isListening ? "default" : "outline"}
                size="sm"
                onClick={toggleDictation}
              >
                {isListening ? (
                  <MicOff className="size-4" />
                ) : (
                  <Mic className="size-4" />
                )}
                {isListening ? "Arrêter" : "Dicter"}
              </Button>
            )}
          </div>

          <Textarea
            value={text}
            onChange={(event) => setText(event.currentTarget.value)}
            rows={3}
            placeholder="Ex. Patient Aminata Traoré, née le 12/05/1990, Dr Diallo, faire NFS, glycémie et bilan rénal."
          />

          <div className="flex flex-wrap items-center gap-2">
            <LoadingButton
              type="button"
              loading={intakeMutation.isPending}
              disabled={!hasText}
              onClick={() => intakeMutation.mutate()}
            >
              <Sparkles className="size-4" />
              Analyser
            </LoadingButton>
            {!canDictate && (
              <span className="text-xs text-muted-foreground">
                Dictée vocale indisponible dans ce navigateur.
              </span>
            )}
            {isListening && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Loader2 className="size-3 animate-spin" />
                Écoute en cours…
              </span>
            )}
          </div>

          {response && (
            <div className="grid gap-3 xl:grid-cols-3">
              <ReviewPanel
                icon={<UserRound className="size-4" />}
                title="Patient"
                confidence={response.patient_draft?.confidence}
                warnings={response.patient_draft?.warnings}
              >
                {response.patient_matches?.length ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">
                      Patients possibles
                    </p>
                    {response.patient_matches.map((patient) => (
                      <button
                        key={patient.id}
                        type="button"
                        onClick={() => onSelectPatient(patient)}
                        className="w-full rounded-md border px-3 py-2 text-left text-sm hover:bg-muted/50"
                      >
                        <span className="block font-medium">
                          {patient.first_name} {patient.last_name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {patient.identifier} · {patient.date_of_birth}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Aucun patient existant trouvé.
                  </p>
                )}
                {response.patient_draft && canCreatePatient && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => onDraftPatient(response.patient_draft!)}
                  >
                    Préremplir un patient
                  </Button>
                )}
              </ReviewPanel>

              <ReviewPanel
                icon={<Stethoscope className="size-4" />}
                title="Médecin"
                confidence={response.doctor_draft?.confidence}
                warnings={response.doctor_draft?.warnings}
              >
                {response.doctor_matches?.length ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">
                      Médecins possibles
                    </p>
                    {response.doctor_matches.map((doctor) => (
                      <button
                        key={doctor.id}
                        type="button"
                        onClick={() => onSelectDoctor(doctor)}
                        className="w-full rounded-md border px-3 py-2 text-left text-sm hover:bg-muted/50"
                      >
                        <span className="block font-medium">
                          {[
                            doctor.title_name,
                            doctor.first_name,
                            doctor.last_name,
                          ]
                            .filter(Boolean)
                            .join(" ")}
                        </span>
                        {doctor.provenance && (
                          <span className="text-xs text-muted-foreground">
                            {doctor.provenance}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Aucun médecin existant trouvé.
                  </p>
                )}
                {response.doctor_draft && canCreateDoctor && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => onDraftDoctor(response.doctor_draft!)}
                  >
                    Préremplir un médecin
                  </Button>
                )}
              </ReviewPanel>

              <ReviewPanel
                icon={<FlaskConical className="size-4" />}
                title="Examens"
                warnings={[
                  ...(response.warnings ?? []),
                  ...(response.unmatched_phrases?.map(
                    (phrase) => `Non reconnu : ${phrase}`,
                  ) ?? []),
                ]}
              >
                {suggestions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Aucun examen catalogue proposé.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {suggestions.map((suggestion) => (
                      <div
                        key={suggestion.catalog.id}
                        className={cn(
                          "grid grid-cols-[auto_minmax(0,1fr)] gap-2 rounded-md border px-3 py-2 text-sm",
                          selectedSuggestions.has(suggestion.catalog.id) &&
                            "bg-primary/5",
                        )}
                      >
                        <Checkbox
                          checked={selectedSuggestions.has(
                            suggestion.catalog.id,
                          )}
                          onCheckedChange={(checked) =>
                            setSelectedSuggestions((current) => {
                              const next = new Set(current)
                              if (checked) next.add(suggestion.catalog.id)
                              else next.delete(suggestion.catalog.id)
                              return next
                            })
                          }
                        />
                        <span className="min-w-0">
                          <span className="flex min-w-0 items-center gap-2">
                            <span className="truncate font-medium">
                              {suggestion.catalog.name}
                            </span>
                            {selected.has(suggestion.catalog.id) && (
                              <Check className="size-3.5 shrink-0 text-emerald-600" />
                            )}
                          </span>
                          <span className="block truncate text-xs text-muted-foreground">
                            {suggestion.catalog.code} ·{" "}
                            {formatMoney(suggestion.catalog.price ?? 0)}
                          </span>
                          {suggestion.reason && (
                            <span className="mt-1 block text-xs text-muted-foreground">
                              {suggestion.reason}
                            </span>
                          )}
                          {(suggestion.warnings ?? []).map((warning) => (
                            <span
                              key={warning}
                              className="mt-1 block text-xs text-amber-700 dark:text-amber-300"
                            >
                              {warning}
                            </span>
                          ))}
                        </span>
                      </div>
                    ))}
                    <LoadingButton
                      type="button"
                      size="sm"
                      loading={isApplying}
                      disabled={selectedSuggestions.size === 0}
                      onClick={applySelectedCatalogs}
                    >
                      Ajouter sélection
                    </LoadingButton>
                  </div>
                )}
              </ReviewPanel>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function ReviewPanel({
  icon,
  title,
  confidence,
  warnings = [],
  children,
}: {
  icon: ReactNode
  title: string
  confidence?: number | null
  warnings?: string[]
  children: ReactNode
}) {
  return (
    <div className="space-y-3 rounded-md border bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          {icon}
          <h4 className="truncate text-sm font-semibold">{title}</h4>
        </div>
        {typeof confidence === "number" && (
          <Badge variant={confidence >= 0.65 ? "secondary" : "outline"}>
            {Math.round(confidence * 100)} %
          </Badge>
        )}
      </div>
      {warnings.length > 0 && (
        <Alert className="py-2">
          <AlertTriangle className="size-4" />
          <AlertDescription className="space-y-1 text-xs">
            {warnings.map((warning) => (
              <div key={warning}>{warning}</div>
            ))}
          </AlertDescription>
        </Alert>
      )}
      {children}
    </div>
  )
}
