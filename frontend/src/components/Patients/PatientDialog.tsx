import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { PatientPublic } from "@/client"
import { PatientsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
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

const patientSchema = z.object({
  identifier: z.string().trim().min(1, "L'identifiant est requis"),
  first_name: z.string().trim().min(1, "Le prénom est requis"),
  last_name: z.string().trim().min(1, "Le nom est requis"),
  date_of_birth: z.string().min(1, "La date de naissance est requise"),
  gender: z.enum(["male", "female"], {
    error: "Le sexe est requis",
  }),
  phone: z.string().trim().optional(),
  address: z.string().trim().optional(),
})

type PatientFormData = z.infer<typeof patientSchema>

interface PatientDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  patient: PatientPublic | null
  initialIdentifier?: string
  onSaved?: (patient: PatientPublic) => void
}

export function PatientDialog({
  open,
  onOpenChange,
  patient,
  initialIdentifier = "",
  onSaved,
}: PatientDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEdit = patient !== null
  const form = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    mode: "onBlur",
    defaultValues: {
      identifier: initialIdentifier,
      first_name: "",
      last_name: "",
      date_of_birth: "",
      gender: "male",
      phone: "",
      address: "",
    },
  })

  useEffect(() => {
    if (!open) return
    form.reset({
      identifier: patient?.identifier ?? initialIdentifier,
      first_name: patient?.first_name ?? "",
      last_name: patient?.last_name ?? "",
      date_of_birth: patient?.date_of_birth ?? "",
      gender: patient?.gender ?? "male",
      phone: patient?.phone ?? "",
      address: patient?.address ?? "",
    })
  }, [form, initialIdentifier, open, patient])

  const mutation = useMutation({
    mutationFn: (data: PatientFormData) => {
      const requestBody = {
        ...data,
        phone: data.phone || null,
        address: data.address || null,
      }
      if (isEdit) {
        return PatientsService.updatePatient({
          id: patient.id,
          requestBody,
        })
      }
      return PatientsService.createPatient({ requestBody })
    },
    onSuccess: (savedPatient) => {
      showSuccessToast(isEdit ? "Patient mis à jour" : "Patient créé")
      queryClient.invalidateQueries({ queryKey: ["patients"] })
      queryClient.invalidateQueries({ queryKey: ["patient", savedPatient.id] })
      onSaved?.(savedPatient)
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier le patient" : "Nouveau patient"}
          </DialogTitle>
          <DialogDescription>
            Renseignez les informations d'identification du patient.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            className="space-y-4"
            onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="identifier"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Identifiant *</FormLabel>
                    <FormControl>
                      <Input placeholder="ex. PAT-000123" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="date_of_birth"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date de naissance *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Prénom *</FormLabel>
                    <FormControl>
                      <Input placeholder="Prénom" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nom *</FormLabel>
                    <FormControl>
                      <Input placeholder="Nom" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="gender"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sexe *</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="male">Homme</SelectItem>
                        <SelectItem value="female">Femme</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Téléphone</FormLabel>
                    <FormControl>
                      <Input placeholder="+223 ..." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Adresse</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Adresse complète" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Annuler
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                {isEdit ? "Enregistrer" : "Créer"}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
