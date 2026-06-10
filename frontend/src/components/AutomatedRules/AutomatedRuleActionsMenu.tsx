import { Eye, MoreHorizontal, Pencil, RotateCcw, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { usePermission } from "@/hooks/usePermission"

interface AutomatedRuleActionsMenuProps<T> {
  rule: T & { is_deleted: boolean }
  onEdit: (rule: T) => void
  onPreview: (rule: T) => void
  onDelete: (rule: T) => void
  onRestore: (rule: T) => void
}

export function AutomatedRuleActionsMenu<T>({
  rule,
  onEdit,
  onPreview,
  onDelete,
  onRestore,
}: AutomatedRuleActionsMenuProps<T>) {
  const canManage = usePermission("rules", "manage")
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
        <DropdownMenuItem onClick={() => onPreview(rule)}>
          <Eye />
          Tester
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onEdit(rule)}>
          <Pencil />
          Modifier
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {rule.is_deleted ? (
          <DropdownMenuItem onClick={() => onRestore(rule)}>
            <RotateCcw />
            Restaurer
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem
            className="text-destructive"
            onClick={() => onDelete(rule)}
          >
            <Trash2 />
            Supprimer
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
