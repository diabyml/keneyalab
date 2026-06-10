import { Link } from "@tanstack/react-router"
import { Ellipsis, ExternalLink, Eye } from "lucide-react"

import type { InvoiceListItemPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function InvoiceActionsMenu({
  invoice,
}: {
  invoice: InvoiceListItemPublic
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Actions">
          <Ellipsis className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link to="/invoices/$invoiceId" params={{ invoiceId: invoice.id }}>
            <Eye className="size-4" />
            Voir la facture
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/orders/$orderId" params={{ orderId: invoice.order_id }}>
            <ExternalLink className="size-4" />
            Voir la demande
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
