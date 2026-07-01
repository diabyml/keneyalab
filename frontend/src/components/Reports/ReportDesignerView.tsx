import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Archive,
  BookOpen,
  Check,
  Code2,
  FileText,
  LayoutTemplate,
  Plus,
  Save,
  Send,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import type {
  ReportComponentPublic,
  ReportComponentType,
  ReportRendererPublic,
} from "@/client"
import { CategoriesService, OrdersService, ReportsService } from "@/client"
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/Common/SearchSelect"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
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
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { ReportDocument } from "./ReportDocument"
import {
  asReportSnapshot,
  asTemplateSnapshot,
  type ReportTemplateSnapshot,
} from "./reportTypes"

const COMPONENT_LABELS: Record<ReportComponentType, string> = {
  header: "En-têtes",
  patient_doctor_details: "Patient & médecin",
  footer: "Pieds de page",
}

const TEMPLATE_VARIABLE_GROUPS = [
  {
    label: "Demande",
    variables: [
      "order.id",
      "order.accession_number",
      "order.status",
      "order.revision_number",
    ],
  },
  {
    label: "Patient",
    variables: [
      "patient.id",
      "patient.identifier",
      "patient.name",
      "patient.date_of_birth",
      "patient.age",
      "patient.gender",
      "patient.gender_label",
      "patient.context",
      "patient.phone",
      "patient.address",
    ],
  },
  {
    label: "Prescripteur",
    variables: [
      "doctor.title",
      "doctor.name",
      "doctor.provenance",
      "doctor.phone",
    ],
  },
  {
    label: "Laboratoire",
    variables: [
      "lab.display_name",
      "lab.legal_name",
      "lab.slogan",
      "lab.address",
      "lab.city",
      "lab.postal_code",
      "lab.country",
      "lab.primary_phone",
      "lab.secondary_phone",
      "lab.email",
      "lab.website",
      "lab.registration_number",
      "lab.laboratory_license",
      "lab.tax_id",
      "lab.director_name",
      "lab.director_title",
      "lab.document_footer",
      "lab.logo_url",
    ],
  },
  {
    label: "Totaux",
    variables: ["totals.results", "totals.verified"],
  },
]

const RENDERER_FIELDS = [
  {
    label: "category",
    fields: ["id", "name", "tests"],
  },
  {
    label: "category.tests[]",
    fields: [
      "order_item_id",
      "catalog_id",
      "catalog_code",
      "catalog_name",
      "category_id",
      "category_name",
      "is_reflex_added",
      "resulted_count",
      "verified_count",
      "analytes",
    ],
  },
  {
    label: "test.analytes[]",
    fields: [
      "result_id",
      "analyte_id",
      "analyte_code",
      "analyte_name",
      "data_type",
      "unit_name",
      "options_data",
      "reference_text",
      "is_calculated",
      "specimen_id",
      "specimen_type_name",
      "result_value",
      "image_url",
      "status",
      "is_abnormal",
      "is_critical",
      "delta_flag",
      "resulted_by_name",
      "resulted_at",
      "verified_by_name",
      "verified_at",
      "comments",
    ],
  },
  {
    label: "analyte.comments[]",
    fields: ["id", "comment", "user_name", "created_at", "updated_at"],
  },
]

export function ReportDesignerView() {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [tab, setTab] = useState<"components" | "renderers" | "assignments">(
    "components",
  )
  const [componentType, setComponentType] =
    useState<ReportComponentType>("header")
  const [selectedComponentId, setSelectedComponentId] = useState("")
  const [selectedRendererId, setSelectedRendererId] = useState("")
  const [isCreatingComponent, setIsCreatingComponent] = useState(false)
  const [isCreatingRenderer, setIsCreatingRenderer] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [html, setHtml] = useState("")
  const [css, setCss] = useState("")
  const [jsx, setJsx] = useState("")
  const [previewOrderId, setPreviewOrderId] = useState("")
  const [previewOrderOption, setPreviewOrderOption] =
    useState<SearchSelectOption | null>(null)

  const componentsQuery = useQuery({
    queryKey: ["report-components", componentType],
    queryFn: () => ReportsService.readReportComponents({ componentType }),
  })
  const renderersQuery = useQuery({
    queryKey: ["report-renderers"],
    queryFn: () => ReportsService.readReportRenderers(),
  })
  const categoriesQuery = useQuery({
    queryKey: ["categories", "report-design"],
    queryFn: () => CategoriesService.readCategories({ limit: 500 }),
  })
  const sampleQuery = useQuery({
    queryKey: ["report-sample-preview"],
    queryFn: () => ReportsService.readSampleReportPreview(),
  })
  const livePreviewQuery = useQuery({
    queryKey: ["report-designer-preview", previewOrderId],
    queryFn: () =>
      ReportsService.readOrderReportPreview({ orderId: previewOrderId }),
    enabled: Boolean(previewOrderId),
  })

  const selectedComponent = componentsQuery.data?.data.find(
    (component) => component.id === selectedComponentId,
  )
  const selectedRenderer = renderersQuery.data?.data.find(
    (renderer) => renderer.id === selectedRendererId,
  )

  useEffect(() => {
    const first = componentsQuery.data?.data[0]
    if (
      !isCreatingComponent &&
      first &&
      !componentsQuery.data?.data.some(
        (component) => component.id === selectedComponentId,
      )
    ) {
      setSelectedComponentId(first.id)
    }
  }, [componentsQuery.data, isCreatingComponent, selectedComponentId])

  useEffect(() => {
    if (!selectedComponent) return
    const version =
      selectedComponent.draft_version ?? selectedComponent.published_version
    setName(selectedComponent.name)
    setDescription(selectedComponent.description ?? "")
    setHtml(version?.html_source ?? "")
    setCss(version?.css_source ?? "")
  }, [selectedComponent])

  useEffect(() => {
    const first = renderersQuery.data?.data[0]
    if (
      !isCreatingRenderer &&
      first &&
      !renderersQuery.data?.data.some(
        (renderer) => renderer.id === selectedRendererId,
      )
    ) {
      setSelectedRendererId(first.id)
    }
  }, [isCreatingRenderer, renderersQuery.data, selectedRendererId])

  useEffect(() => {
    if (!selectedRenderer) return
    const version =
      selectedRenderer.draft_version ?? selectedRenderer.published_version
    setName(selectedRenderer.name)
    setDescription(selectedRenderer.description ?? "")
    setJsx(version?.jsx_source ?? "")
    setCss(version?.css_source ?? "")
  }, [selectedRenderer])

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["report-components"] })
    queryClient.invalidateQueries({ queryKey: ["report-renderers"] })
    queryClient.invalidateQueries({ queryKey: ["report-sample-preview"] })
  }
  const saveComponent = useMutation({
    mutationFn: () =>
      selectedComponent
        ? ReportsService.updateReportComponent({
            componentId: selectedComponent.id,
            requestBody: {
              name,
              description,
              html_source: html,
              css_source: css,
            },
          })
        : ReportsService.createReportComponent({
            requestBody: {
              name,
              description,
              component_type: componentType,
              html_source: html,
              css_source: css,
            },
          }),
    onSuccess: (component) => {
      setIsCreatingComponent(false)
      setSelectedComponentId(component.id)
      showSuccessToast("Brouillon enregistré")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const publishComponent = useMutation({
    mutationFn: () =>
      ReportsService.publishReportComponent({
        componentId: selectedComponentId,
      }),
    onSuccess: () => {
      showSuccessToast("Composant publié")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const defaultComponent = useMutation({
    mutationFn: () =>
      ReportsService.setDefaultReportComponent({
        componentType,
        requestBody: { template_id: selectedComponentId },
      }),
    onSuccess: () => {
      showSuccessToast("Composant défini par défaut")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const archiveComponent = useMutation({
    mutationFn: () =>
      ReportsService.archiveReportComponent({
        componentId: selectedComponentId,
      }),
    onSuccess: () => {
      setSelectedComponentId("")
      showSuccessToast("Composant archivé")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const saveRenderer = useMutation({
    mutationFn: () =>
      selectedRenderer
        ? ReportsService.updateReportRenderer({
            rendererId: selectedRenderer.id,
            requestBody: {
              name,
              description,
              jsx_source: jsx,
              css_source: css,
            },
          })
        : ReportsService.createReportRenderer({
            requestBody: {
              name,
              description,
              jsx_source: jsx,
              css_source: css,
            },
          }),
    onSuccess: (renderer) => {
      setIsCreatingRenderer(false)
      setSelectedRendererId(renderer.id)
      showSuccessToast("Brouillon enregistré")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const publishRenderer = useMutation({
    mutationFn: () =>
      ReportsService.publishReportRenderer({
        rendererId: selectedRendererId,
      }),
    onSuccess: () => {
      showSuccessToast("Rendu publié")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const defaultRenderer = useMutation({
    mutationFn: () =>
      ReportsService.setDefaultReportRenderer({
        requestBody: { template_id: selectedRendererId },
      }),
    onSuccess: () => {
      showSuccessToast("Rendu défini par défaut")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const archiveRenderer = useMutation({
    mutationFn: () =>
      ReportsService.archiveReportRenderer({
        rendererId: selectedRendererId,
      }),
    onSuccess: () => {
      setSelectedRendererId("")
      showSuccessToast("Rendu archivé")
      invalidate()
    },
    onError: handleError.bind(showErrorToast),
  })
  const assignmentMutation = useMutation({
    mutationFn: ({
      categoryId,
      rendererId,
    }: {
      categoryId: string
      rendererId: string | null
    }) =>
      ReportsService.assignCategoryReportRenderer({
        categoryId,
        requestBody: { report_renderer_id: rendererId },
      }),
    onSuccess: () => {
      showSuccessToast("Affectation mise à jour")
      queryClient.invalidateQueries({
        queryKey: ["categories", "report-design"],
      })
    },
    onError: handleError.bind(showErrorToast),
  })
  const loadOrderOptions = useCallback(
    async (query: string): Promise<SearchSelectOption[]> => {
      const response = await OrdersService.readOrders({
        search: query.trim() || undefined,
        limit: 10,
      })
      return response.data.map((order) => ({
        value: order.id,
        label: `${order.accession_number} · ${order.patient_name}`,
        description: [
          order.patient_identifier,
          order.doctor_name || "Sans prescripteur",
        ].join(" · "),
      }))
    },
    [],
  )

  const preview = livePreviewQuery.data ?? sampleQuery.data
  const previewTemplates = useMemo(() => {
    if (!preview?.template_snapshot) return null
    const templates = structuredClone(
      asTemplateSnapshot(preview.template_snapshot),
    ) as ReportTemplateSnapshot
    if (tab === "components" && (selectedComponent || isCreatingComponent)) {
      const activeComponentType =
        selectedComponent?.component_type ?? componentType
      const slot =
        activeComponentType === "patient_doctor_details"
          ? "details"
          : activeComponentType
      templates[slot] = {
        id: selectedComponent?.id ?? "new-component",
        name,
        version_id: selectedComponent?.draft_version?.id ?? "draft",
        version: selectedComponent?.draft_version?.version ?? 0,
        html_source: html,
        css_source: css,
      }
    }
    if (tab === "renderers" && (selectedRenderer || isCreatingRenderer)) {
      for (const category of asReportSnapshot(preview.snapshot).categories) {
        templates.renderers[category.id ?? "uncategorized"] = {
          id: selectedRenderer?.id ?? "new-renderer",
          name,
          version_id: selectedRenderer?.draft_version?.id ?? "draft",
          version: selectedRenderer?.draft_version?.version ?? 0,
          jsx_source: jsx,
          css_source: css,
        }
      }
    }
    return templates
  }, [
    componentType,
    css,
    html,
    isCreatingComponent,
    isCreatingRenderer,
    jsx,
    name,
    preview,
    selectedComponent,
    selectedRenderer,
    tab,
  ])

  if (componentsQuery.isLoading || renderersQuery.isLoading) {
    return <Skeleton className="h-[720px] w-full" />
  }

  return (
    <div className="-mx-4 -mb-5 -mt-4 flex min-h-[calc(100vh-4rem)] flex-col lg:-mx-5 lg:-mt-5">
      <header className="flex flex-wrap items-center gap-3 border-b bg-background px-4 py-3 lg:px-5">
        <div className="mr-auto">
          <h1 className="text-lg font-semibold">Conception des rapports</h1>
          <p className="text-xs text-muted-foreground">
            Brouillons isolés, publication explicite et aperçu A4
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SearchSelect
            value={previewOrderId || null}
            selectedOption={previewOrderOption}
            onValueChange={(value, option) => {
              setPreviewOrderId(value ?? "")
              setPreviewOrderOption(option ?? null)
            }}
            loadOptions={loadOrderOptions}
            placeholder="N° de demande ou patient"
            searchPlaceholder="Rechercher une demande ou un patient…"
            emptyMessage="Aucune demande trouvée"
            minSearchLength={2}
            className="w-80"
          />
          {previewOrderId && (
            <Button
              variant="ghost"
              onClick={() => {
                setPreviewOrderId("")
                setPreviewOrderOption(null)
              }}
            >
              Données exemple
            </Button>
          )}
        </div>
      </header>

      <Tabs
        value={tab}
        onValueChange={(value) => setTab(value as typeof tab)}
        className="flex min-h-0 flex-1 flex-col"
      >
        <div className="border-b px-4 lg:px-5">
          <TabsList className="bg-transparent">
            <TabsTrigger value="components">
              <LayoutTemplate className="size-4" />
              Structure
            </TabsTrigger>
            <TabsTrigger value="renderers">
              <Code2 className="size-4" />
              Rendus par catégorie
            </TabsTrigger>
            <TabsTrigger value="assignments">
              <FileText className="size-4" />
              Affectations
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="components" className="m-0 min-h-0 flex-1">
          <div className="grid h-full min-h-[720px] grid-cols-[230px_minmax(360px,0.8fr)_minmax(600px,1.2fr)]">
            <aside className="border-r p-3">
              <Select
                value={componentType}
                onValueChange={(value) => {
                  setComponentType(value as ReportComponentType)
                  setIsCreatingComponent(false)
                  setSelectedComponentId("")
                }}
              >
                <SelectTrigger className="mb-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(COMPONENT_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <TemplateList
                items={componentsQuery.data?.data ?? []}
                selectedId={selectedComponentId}
                onSelect={(id) => {
                  setIsCreatingComponent(false)
                  setSelectedComponentId(id)
                }}
                onCreate={() => {
                  setIsCreatingComponent(true)
                  setSelectedComponentId("")
                  setName(
                    `Nouveau ${COMPONENT_LABELS[componentType].toLowerCase()}`,
                  )
                  setDescription("")
                  setHtml("<div>Nouveau composant</div>")
                  setCss("")
                }}
              />
            </aside>
            <EditorPane
              name={name}
              description={description}
              source={html}
              css={css}
              sourceLabel="HTML"
              onNameChange={setName}
              onDescriptionChange={setDescription}
              onSourceChange={setHtml}
              onCssChange={setCss}
              onSave={() => saveComponent.mutate()}
              onPublish={() => publishComponent.mutate()}
              onDefault={() => defaultComponent.mutate()}
              onArchive={() => archiveComponent.mutate()}
              canPublish={Boolean(selectedComponent?.draft_version)}
              canDefault={Boolean(
                selectedComponent?.published_version &&
                  !selectedComponent.draft_version,
              )}
              canArchive={Boolean(
                selectedComponent && !selectedComponent.is_default,
              )}
              isDefault={selectedComponent?.is_default}
              isSaving={saveComponent.isPending}
              isPublishing={publishComponent.isPending}
              variableHelp="template"
            />
            <PreviewPane preview={preview} templates={previewTemplates} />
          </div>
        </TabsContent>

        <TabsContent value="renderers" className="m-0 min-h-0 flex-1">
          <div className="grid h-full min-h-[720px] grid-cols-[230px_minmax(420px,0.9fr)_minmax(600px,1.1fr)]">
            <aside className="border-r p-3">
              <TemplateList
                items={renderersQuery.data?.data ?? []}
                selectedId={selectedRendererId}
                onSelect={(id) => {
                  setIsCreatingRenderer(false)
                  setSelectedRendererId(id)
                }}
                onCreate={() => {
                  setIsCreatingRenderer(true)
                  setSelectedRendererId("")
                  setName("Nouveau rendu")
                  setDescription("")
                  setJsx(
                    "function Renderer({ category, ReportKit }) { return <ReportKit.ClinicalTable category={category} /> }",
                  )
                  setCss("")
                }}
              />
            </aside>
            <EditorPane
              name={name}
              description={description}
              source={jsx}
              css={css}
              sourceLabel="JSX / React"
              onNameChange={setName}
              onDescriptionChange={setDescription}
              onSourceChange={setJsx}
              onCssChange={setCss}
              onSave={() => saveRenderer.mutate()}
              onPublish={() => publishRenderer.mutate()}
              onDefault={() => defaultRenderer.mutate()}
              onArchive={() => archiveRenderer.mutate()}
              canPublish={Boolean(selectedRenderer?.draft_version)}
              canDefault={Boolean(
                selectedRenderer?.published_version &&
                  !selectedRenderer.draft_version,
              )}
              canArchive={Boolean(
                selectedRenderer && !selectedRenderer.is_default,
              )}
              isDefault={selectedRenderer?.is_default}
              isSaving={saveRenderer.isPending}
              isPublishing={publishRenderer.isPending}
              variableHelp="renderer"
            />
            <PreviewPane preview={preview} templates={previewTemplates} />
          </div>
        </TabsContent>

        <TabsContent value="assignments" className="m-0 p-5">
          <div className="mx-auto max-w-4xl overflow-hidden rounded-md border">
            <div className="grid grid-cols-[1fr_300px] border-b bg-muted/30 px-4 py-3 text-sm font-medium">
              <span>Catégorie</span>
              <span>Rendu publié</span>
            </div>
            {(categoriesQuery.data?.data ?? []).map((category) => (
              <div
                key={category.id}
                className="grid grid-cols-[1fr_300px] items-center border-b px-4 py-3 last:border-b-0"
              >
                <span className="font-medium">{category.name}</span>
                <Select
                  value={category.report_renderer_id ?? "default"}
                  onValueChange={(value) =>
                    assignmentMutation.mutate({
                      categoryId: category.id,
                      rendererId: value === "default" ? null : value,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">
                      Rendu global par défaut
                    </SelectItem>
                    {(renderersQuery.data?.data ?? [])
                      .filter(
                        (renderer) =>
                          renderer.published_version && !renderer.is_archived,
                      )
                      .map((renderer) => (
                        <SelectItem key={renderer.id} value={renderer.id}>
                          {renderer.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

function TemplateList({
  items,
  selectedId,
  onSelect,
  onCreate,
}: {
  items: Array<ReportComponentPublic | ReportRendererPublic>
  selectedId: string
  onSelect: (id: string) => void
  onCreate: () => void
}) {
  return (
    <div className="space-y-1">
      <Button variant="outline" className="mb-2 w-full" onClick={onCreate}>
        <Plus className="size-4" />
        Nouveau
      </Button>
      {items.map((item) => (
        <button
          type="button"
          key={item.id}
          onClick={() => onSelect(item.id)}
          className={`w-full rounded-md px-3 py-2 text-left transition-colors ${
            selectedId === item.id ? "bg-accent" : "hover:bg-muted/60"
          }`}
        >
          <div className="flex items-center gap-2 text-sm font-medium">
            <span className="truncate">{item.name}</span>
            {item.is_default && (
              <Check className="ml-auto size-3 text-primary" />
            )}
          </div>
          <div className="mt-1 flex gap-1">
            {item.draft_version && <Badge variant="secondary">Brouillon</Badge>}
            {item.published_version && <Badge variant="outline">Publié</Badge>}
          </div>
        </button>
      ))}
    </div>
  )
}

function EditorPane({
  name,
  description,
  source,
  css,
  sourceLabel,
  onNameChange,
  onDescriptionChange,
  onSourceChange,
  onCssChange,
  onSave,
  onPublish,
  onDefault,
  onArchive,
  canPublish,
  canDefault,
  canArchive,
  isDefault,
  isSaving,
  isPublishing,
  variableHelp,
}: {
  name: string
  description: string
  source: string
  css: string
  sourceLabel: string
  onNameChange: (value: string) => void
  onDescriptionChange: (value: string) => void
  onSourceChange: (value: string) => void
  onCssChange: (value: string) => void
  onSave: () => void
  onPublish: () => void
  onDefault: () => void
  onArchive: () => void
  canPublish: boolean
  canDefault: boolean
  canArchive: boolean
  isDefault?: boolean
  isSaving: boolean
  isPublishing: boolean
  variableHelp: "template" | "renderer"
}) {
  return (
    <section className="min-h-0 overflow-auto border-r p-4">
      <div className="mb-4 flex items-center gap-2">
        <LoadingButton loading={isSaving} onClick={onSave}>
          <Save className="size-4" />
          Enregistrer
        </LoadingButton>
        <LoadingButton
          variant="outline"
          loading={isPublishing}
          disabled={!canPublish}
          onClick={onPublish}
        >
          <Send className="size-4" />
          Publier
        </LoadingButton>
        {!isDefault && (
          <Button variant="ghost" disabled={!canDefault} onClick={onDefault}>
            Définir par défaut
          </Button>
        )}
        <VariablesDialog kind={variableHelp} />
        {canArchive && (
          <Button
            variant="ghost"
            className="text-destructive"
            onClick={onArchive}
          >
            <Archive className="size-4" />
            Archiver
          </Button>
        )}
      </div>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label>Nom</Label>
          <Input value={name} onChange={(e) => onNameChange(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label>Description</Label>
          <Input
            value={description}
            onChange={(e) => onDescriptionChange(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label>{sourceLabel}</Label>
          <Textarea
            value={source}
            onChange={(e) => onSourceChange(e.target.value)}
            className="min-h-72 resize-y font-mono text-xs leading-relaxed"
            spellCheck={false}
          />
        </div>
        <div className="space-y-1.5">
          <Label>CSS</Label>
          <Textarea
            value={css}
            onChange={(e) => onCssChange(e.target.value)}
            className="min-h-52 resize-y font-mono text-xs leading-relaxed"
            spellCheck={false}
          />
        </div>
      </div>
    </section>
  )
}

function VariablesDialog({ kind }: { kind: "template" | "renderer" }) {
  const isTemplate = kind === "template"

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="ml-auto">
          <BookOpen className="size-4" />
          Variables
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-hidden p-0 sm:max-w-3xl">
        <DialogHeader className="border-b px-5 py-4 pr-12">
          <DialogTitle>Variables disponibles</DialogTitle>
          <DialogDescription>
            {isTemplate
              ? "Insérez une variable dans le HTML avec la syntaxe {{variable}}. Les valeurs sont échappées automatiquement."
              : "Le composant Renderer reçoit category et ReportKit. Aucun import ni appel réseau n’est autorisé."}
          </DialogDescription>
        </DialogHeader>

        <div className="max-h-[calc(85vh-88px)] overflow-y-auto px-5 py-4">
          {isTemplate ? (
            <div className="grid gap-5 sm:grid-cols-2">
              {TEMPLATE_VARIABLE_GROUPS.map((group) => (
                <VariableGroup
                  key={group.label}
                  label={group.label}
                  values={group.variables.map((variable) => `{{${variable}}}`)}
                />
              ))}
              <div className="sm:col-span-2">
                <p className="mb-2 font-medium">Exemple</p>
                <CodeExample
                  value={`<strong>{{patient.name}}</strong>\n<span>{{order.accession_number}}</span>\n<img src="{{lab.logo_url}}" alt="Logo" />`}
                />
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              <CodeExample
                value={`function Renderer({ category, ReportKit }) {\n  return <ReportKit.ClinicalTable category={category} />\n}`}
              />
              <div className="grid gap-5 sm:grid-cols-2">
                {RENDERER_FIELDS.map((group) => (
                  <VariableGroup
                    key={group.label}
                    label={group.label}
                    values={group.fields}
                  />
                ))}
              </div>
              <div>
                <p className="mb-2 font-medium">Composants ReportKit</p>
                <CodeExample
                  value={`<ReportKit.ClinicalTable category={category} />`}
                />
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function VariableGroup({ label, values }: { label: string; values: string[] }) {
  return (
    <section>
      <h3 className="mb-2 text-sm font-medium">{label}</h3>
      <div className="flex flex-wrap gap-1.5">
        {values.map((value) => (
          <code
            key={value}
            className="rounded-md border bg-muted/50 px-2 py-1 font-mono text-[11px] text-foreground"
          >
            {value}
          </code>
        ))}
      </div>
    </section>
  )
}

function CodeExample({ value }: { value: string }) {
  return (
    <pre className="overflow-x-auto rounded-lg border bg-slate-950 p-3 text-[11px] leading-relaxed text-slate-100">
      <code>{value}</code>
    </pre>
  )
}

function PreviewPane({
  preview,
  templates,
}: {
  preview: { snapshot?: unknown } | undefined
  templates: ReportTemplateSnapshot | null
}) {
  return (
    <section className="min-w-0 overflow-auto bg-slate-100 p-6 dark:bg-slate-950">
      {preview?.snapshot && templates ? (
        <div className="mx-auto w-[210mm] origin-top scale-[0.78]">
          <ReportDocument
            snapshot={asReportSnapshot(preview.snapshot)}
            templates={templates}
          />
        </div>
      ) : (
        <Skeleton className="mx-auto h-[900px] max-w-3xl" />
      )}
    </section>
  )
}
