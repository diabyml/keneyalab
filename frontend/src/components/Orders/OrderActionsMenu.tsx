import { Link } from "@tanstack/react-router"
import { Ellipsis, Eye, Pencil } from "lucide-react"

import type { OrderListItemPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { usePermission } from "@/hooks/usePermission"

export function OrderActionsMenu({ order }: { order: OrderListItemPublic }) {
  const canEdit = usePermission("orders", "edit")

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Actions demande">
          <Ellipsis className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link to="/orders/$orderId" params={{ orderId: order.id }}>
            <Eye className="size-4" />
            Voir la demande
          </Link>
        </DropdownMenuItem>
        {canEdit && (
          <DropdownMenuItem asChild>
            <Link to="/orders/$orderId/edit" params={{ orderId: order.id }}>
              <Pencil className="size-4" />
              Modifier
            </Link>
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
