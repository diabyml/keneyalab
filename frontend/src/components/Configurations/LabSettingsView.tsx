import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ImageUp, Trash2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import type { LabSettingsPublic, LabSettingsUpdate } from "@/client"
import { LabSettingsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { LAB_SETTINGS_QUERY_KEY, useLabSettings } from "@/hooks/useLabSettings"
import { handleError } from "@/utils"

type EditableField = Exclude<keyof LabSettingsUpdate, "display_name">

type FormState = Record<keyof LabSettingsUpdate, string>

const SECTIONS: Array<{
  title: string
  description: string
  fields: Array<{
    name: keyof LabSettingsUpdate
    label: string
    type?: "email" | "url" | "textarea"
    placeholder?: string
  }>
}> = [
  {
    title: "Identité",
    description: "Informations visibles dans les en-têtes des documents.",
    fields: [
      { name: "display_name", label: "Nom affiché" },
      { name: "legal_name", label: "Raison sociale" },
      { name: "slogan", label: "Slogan" },
    ],
  },
  {
    title: "Coordonnées",
    description: "Adresse et moyens de contact du laboratoire.",
    fields: [
      { name: "address", label: "Adresse", type: "textarea" },
      { name: "city", label: "Ville" },
      { name: "postal_code", label: "Code postal" },
      { name: "country", label: "Pays" },
      { name: "primary_phone", label: "Téléphone principal" },
      { name: "secondary_phone", label: "Téléphone secondaire" },
      { name: "email", label: "E-mail", type: "email" },
      {
        name: "website",
        label: "Site web",
        type: "url",
        placeholder: "https://...",
      },
    ],
  },
  {
    title: "Informations légales",
    description: "Références administratives et réglementaires.",
    fields: [
      { name: "registration_number", label: "Numéro d’enregistrement" },
      { name: "laboratory_license", label: "Licence du laboratoire" },
      { name: "tax_id", label: "Identifiant fiscal" },
    ],
  },
  {
    title: "Paiement",
    description: "Informations réservées aux documents financiers appropriés.",
    fields: [
      { name: "bank_name", label: "Banque" },
      { name: "bank_account_holder", label: "Titulaire du compte" },
      { name: "bank_account_number", label: "Numéro de compte" },
      {
        name: "payment_instructions",
        label: "Instructions de paiement",
        type: "textarea",
      },
    ],
  },
  {
    title: "Direction et documents",
    description: "Signataire par défaut et pied de page des documents.",
    fields: [
      { name: "director_name", label: "Nom du directeur ou signataire" },
      { name: "director_title", label: "Titre du signataire" },
      {
        name: "document_footer",
        label: "Pied de page",
        type: "textarea",
      },
    ],
  },
]

const EMPTY_FORM = Object.fromEntries(
  SECTIONS.flatMap((section) => section.fields).map((field) => [
    field.name,
    "",
  ]),
) as FormState

function settingsToForm(settings: LabSettingsPublic): FormState {
  const form = { ...EMPTY_FORM }
  for (const name of Object.keys(form) as Array<keyof FormState>) {
    form[name] = settings[name] ?? ""
  }
  return form
}

export function LabSettingsView() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const settingsQuery = useLabSettings()
  const [form, setForm] = useState<FormState>(EMPTY_FORM)

  useEffect(() => {
    if (settingsQuery.data) setForm(settingsToForm(settingsQuery.data))
  }, [settingsQuery.data])

  const savedForm = settingsQuery.data
    ? settingsToForm(settingsQuery.data)
    : EMPTY_FORM
  const hasChanges = JSON.stringify(form) !== JSON.stringify(savedForm)

  const updateMutation = useMutation({
    mutationFn: () => {
      const requestBody: LabSettingsUpdate = {
        display_name: form.display_name.trim(),
      }
      for (const name of Object.keys(form) as EditableField[]) {
        requestBody[name] = form[name].trim() || null
      }
      return LabSettingsService.updateLabSettings({ requestBody })
    },
    onSuccess: (settings) => {
      queryClient.setQueryData(LAB_SETTINGS_QUERY_KEY, settings)
      showSuccessToast("Informations du laboratoire enregistrées")
    },
    onError: handleError.bind(showErrorToast),
  })

  const logoMutation = useMutation({
    mutationFn: (file: File) =>
      LabSettingsService.uploadLabLogo({ formData: { file } }),
    onSuccess: (settings) => {
      queryClient.setQueryData(LAB_SETTINGS_QUERY_KEY, settings)
      showSuccessToast("Logo du laboratoire enregistré")
      if (fileInputRef.current) fileInputRef.current.value = ""
    },
    onError: handleError.bind(showErrorToast),
  })

  const deleteLogoMutation = useMutation({
    mutationFn: () => LabSettingsService.deleteLabLogo(),
    onSuccess: (settings) => {
      queryClient.setQueryData(LAB_SETTINGS_QUERY_KEY, settings)
      showSuccessToast("Logo supprimé")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (settingsQuery.isLoading || !settingsQuery.data) {
    return (
      <div className="max-w-4xl space-y-4">
        {Array.from({ length: 3 }, (_, index) => (
          <Skeleton key={index} className="h-52 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="max-w-4xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Logo</CardTitle>
          <CardDescription>
            Image PNG, JPEG ou WebP, avec une taille maximale de 2 Mo.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-4">
          <div className="flex size-24 items-center justify-center overflow-hidden rounded-lg border bg-muted/30">
            {settingsQuery.data.logo_url ? (
              <img
                src={settingsQuery.data.logo_url}
                alt="Logo du laboratoire"
                className="size-full object-contain p-2"
              />
            ) : (
              <span className="text-xs text-muted-foreground">Aucun logo</span>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Label
              htmlFor="lab-logo"
              className="inline-flex h-9 cursor-pointer items-center gap-2 rounded-md border bg-background px-3 text-sm font-medium hover:bg-accent"
            >
              <ImageUp className="size-4" />
              {settingsQuery.data.logo_url ? "Remplacer" : "Ajouter"}
            </Label>
            <input
              ref={fileInputRef}
              id="lab-logo"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="sr-only"
              disabled={logoMutation.isPending}
              onChange={(event) => {
                const file = event.currentTarget.files?.[0]
                if (file) logoMutation.mutate(file)
              }}
            />
            {settingsQuery.data.logo_url && (
              <Button
                type="button"
                variant="outline"
                disabled={deleteLogoMutation.isPending}
                onClick={() => deleteLogoMutation.mutate()}
              >
                <Trash2 className="size-4" />
                Supprimer
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {SECTIONS.map((section) => (
        <Card key={section.title}>
          <CardHeader>
            <CardTitle className="text-base">{section.title}</CardTitle>
            <CardDescription>{section.description}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {section.fields.map((field) => {
              const isTextarea = field.type === "textarea"
              return (
                <div
                  key={field.name}
                  className={
                    isTextarea ? "space-y-2 sm:col-span-2" : "space-y-2"
                  }
                >
                  <Label htmlFor={`lab-${field.name}`}>{field.label}</Label>
                  {isTextarea ? (
                    <Textarea
                      id={`lab-${field.name}`}
                      value={form[field.name]}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          [field.name]: event.target.value,
                        }))
                      }
                    />
                  ) : (
                    <Input
                      id={`lab-${field.name}`}
                      type={field.type || "text"}
                      required={field.name === "display_name"}
                      placeholder={field.placeholder}
                      value={form[field.name]}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          [field.name]: event.target.value,
                        }))
                      }
                    />
                  )}
                </div>
              )
            })}
          </CardContent>
        </Card>
      ))}

      <div className="sticky bottom-4 flex justify-end rounded-lg border bg-background/95 p-3 shadow-sm backdrop-blur">
        <LoadingButton
          loading={updateMutation.isPending}
          disabled={!hasChanges || !form.display_name.trim()}
          onClick={() => updateMutation.mutate()}
        >
          Enregistrer
        </LoadingButton>
      </div>
    </div>
  )
}
