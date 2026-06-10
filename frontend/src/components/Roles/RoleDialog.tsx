import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { PermissionPublic, RoleDetail } from "@/client"
import { RbacService } from "@/client"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
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
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

import { ActionBadge, groupPermissionsByResource } from "./PermissionBadge"

const formSchema = z.object({
  name: z.string().min(1, "Le nom est requis"),
  description: z.string().default(""),
  is_default: z.boolean().default(false),
})

type FormData = z.infer<typeof formSchema>

interface RoleDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  role: RoleDetail | null
  allPermissions: PermissionPublic[]
  permissionsLoading?: boolean
}

function RoleDialog({
  open,
  onOpenChange,
  role,
  allPermissions,
  permissionsLoading = false,
}: RoleDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [selected, setSelected] = useState<string[]>([])
  const isEdit = role !== null

  const form = useForm({
    resolver: zodResolver(formSchema),
    mode: "onBlur" as const,
    criteriaMode: "all" as const,
    defaultValues: {
      name: "",
      description: "",
      is_default: false,
    },
  })

  // Reset form + selected permissions when dialog opens or role changes
  useEffect(() => {
    if (open) {
      form.reset({
        name: role?.name ?? "",
        description: role?.description ?? "",
        is_default: role?.is_default ?? false,
      })
      setSelected(role?.permissions?.map((p) => p.id) ?? [])
    }
  }, [open, role, form])

  const grouped = groupPermissionsByResource(allPermissions)

  function toggle(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    )
  }

  function toggleGroup(ids: string[], allOn: boolean) {
    if (allOn) {
      setSelected((prev) => prev.filter((i) => !ids.includes(i)))
    } else {
      setSelected((prev) => Array.from(new Set([...prev, ...ids])))
    }
  }

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      if (isEdit) {
        // Update role metadata
        await RbacService.updateRole({
          roleId: role!.id,
          requestBody: {
            name: data.name,
            description: data.description || null,
            is_default: data.is_default,
          },
        })

        // Diff permissions
        const currentIds = new Set(role!.permissions?.map((p) => p.id) ?? [])
        const selectedIds = new Set(selected)

        // Add new permissions
        const toAdd = selected.filter((id) => !currentIds.has(id))
        for (const permId of toAdd) {
          await RbacService.addPermissionToRole({
            roleId: role!.id,
            requestBody: { permission_id: permId },
          })
        }

        // Remove unselected permissions
        const toRemove = (role!.permissions ?? [])
          .map((p) => p.id)
          .filter((id) => !selectedIds.has(id))
        for (const permId of toRemove) {
          await RbacService.removePermissionFromRole({
            roleId: role!.id,
            permissionId: permId,
          })
        }
      } else {
        // Create role
        const created = await RbacService.createRole({
          requestBody: {
            name: data.name,
            description: data.description || null,
            is_default: data.is_default,
          },
        })

        // Assign permissions
        for (const permId of selected) {
          await RbacService.addPermissionToRole({
            roleId: created.id,
            requestBody: { permission_id: permId },
          })
        }
      }
    },
    onSuccess: () => {
      showSuccessToast(
        isEdit ? "Rôle mis à jour avec succès" : "Rôle créé avec succès",
      )
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries()
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] flex-col p-0 sm:max-w-lg">
        {/* Header */}
        <div className="shrink-0 border-b px-6 py-4">
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Modifier le rôle" : "Créer un rôle"}
            </DialogTitle>
            <DialogDescription>
              {isEdit
                ? "Modifiez les informations et les permissions du rôle."
                : "Définissez un nouveau rôle et ses permissions."}
            </DialogDescription>
          </DialogHeader>
        </div>

        {/* Scrollable body */}
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex min-h-0 flex-1 flex-col"
          >
            <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">
              <div className="space-y-4">
                {/* Name */}
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nom du rôle</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="ex. Responsable qualité"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Description */}
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Que peut faire ce rôle ?"
                          rows={2}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Default role toggle */}
                <FormField
                  control={form.control}
                  name="is_default"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <FormLabel className="text-sm">
                          Rôle par défaut
                        </FormLabel>
                        <p className="text-xs text-muted-foreground">
                          Assigné automatiquement aux nouveaux utilisateurs
                        </p>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                {/* Permissions checklist */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium">Permissions</h3>
                    <span className="inline-flex size-5 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
                      {selected.length}
                    </span>
                  </div>

                  {permissionsLoading && allPermissions.length === 0 && (
                    <p className="py-4 text-center text-sm text-muted-foreground">
                      Chargement des permissions…
                    </p>
                  )}

                  {!permissionsLoading && allPermissions.length === 0 && (
                    <p className="py-4 text-center text-sm text-muted-foreground">
                      Aucune permission disponible.
                    </p>
                  )}

                  {grouped.map(([resource, perms]) => {
                    const allOn = perms.every((p) => selected.includes(p.id))
                    return (
                      <Card key={resource} className="rounded-lg border p-3">
                        <div className="mb-2 flex items-center justify-between">
                          <span className="font-mono text-sm font-medium capitalize">
                            {resource}
                          </span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="xs"
                            onClick={() =>
                              toggleGroup(
                                perms.map((p) => p.id),
                                allOn,
                              )
                            }
                          >
                            {allOn ? "Tout effacer" : "Tout sélectionner"}
                          </Button>
                        </div>
                        <div className="space-y-1">
                          {perms.map((perm) => (
                            <label
                              key={perm.id}
                              htmlFor={`permission-${perm.id}`}
                              className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 hover:bg-accent/50"
                            >
                              <Checkbox
                                id={`permission-${perm.id}`}
                                checked={selected.includes(perm.id)}
                                onCheckedChange={() => toggle(perm.id)}
                              />
                              <ActionBadge action={perm.action} />
                              <span className="truncate text-xs text-muted-foreground">
                                {perm.description}
                              </span>
                            </label>
                          ))}
                        </div>
                      </Card>
                    )
                  })}
                </div>
              </div>
            </div>

            <DialogFooter className="shrink-0 border-t px-6 py-4">
              <DialogClose asChild>
                <Button
                  type="button"
                  variant="outline"
                  disabled={mutation.isPending}
                >
                  Annuler
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                {isEdit ? "Enregistrer" : "Créer le rôle"}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default RoleDialog
