import { useMutation, useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, Power } from "lucide-react"

import type { ValidationRuleDetailPublic } from "@/client"
import { ValidationRulesService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { handleError } from "@/utils"

interface ValidationRuleActionsMenuProps {
  rule: ValidationRuleDetailPublic
  onEdit: (rule: ValidationRuleDetailPublic) => void
}

export function ValidationRuleActionsMenu({
  rule,
  onEdit,
}: ValidationRuleActionsMenuProps) {
  const canManage = usePermission("rules", "manage")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const toggleMutation = useMutation({
    mutationFn: () =>
      ValidationRulesService.updateValidationRule({
        id: rule.id,
        requestBody: { is_active: !(rule.is_active ?? true) },
      }),
    onSuccess: () => showSuccessToast("Statut de la règle mis à jour"),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["validation-rules"] }),
  })

  if (!canManage) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="size-8">
          <MoreHorizontal className="size-4" />
          <span className="sr-only">Actions</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onSelect={(event) => event.preventDefault()}
          onClick={() => onEdit(rule)}
        >
          <Pencil />
          Modifier
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          disabled={toggleMutation.isPending}
          onSelect={(event) => event.preventDefault()}
          onClick={() => toggleMutation.mutate()}
        >
          <Power />
          {rule.is_active ? "Désactiver" : "Activer"}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
