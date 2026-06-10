import { MoreHorizontal, Pencil, Trash2 } from "lucide-react"
import { useState } from "react"

import type { InsurancePricingDetailPublic } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { usePermission } from "@/hooks/usePermission"
import { DeleteInsurancePricingDialog } from "./DeleteInsurancePricingDialog"
import { InsurancePricingDialog } from "./InsurancePricingDialog"

interface InsurancePricingActionsMenuProps {
  pricing: InsurancePricingDetailPublic
  onDeleted: () => void
}

export function InsurancePricingActionsMenu({
  pricing,
  onDeleted,
}: InsurancePricingActionsMenuProps) {
  const canManage = usePermission("finance", "manage")
  const [open, setOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [providerOption, setProviderOption] =
    useState<SearchSelectOption | null>(null)
  const [catalogOption, setCatalogOption] = useState<SearchSelectOption | null>(
    null,
  )
  const name = `${pricing.insurance_provider_name} · ${pricing.catalog_code}`

  if (!canManage) return null

  return (
    <>
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Actions tarif">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onSelect={(event) => event.preventDefault()}
            onClick={() => {
              setEditOpen(true)
              setOpen(false)
            }}
          >
            <Pencil />
            Modifier
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            variant="destructive"
            onSelect={(event) => event.preventDefault()}
            onClick={() => {
              setDeleteOpen(true)
              setOpen(false)
            }}
          >
            <Trash2 />
            Supprimer
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <InsurancePricingDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        pricing={pricing}
        providerOption={providerOption}
        catalogOption={catalogOption}
        onProviderOptionChange={setProviderOption}
        onCatalogOptionChange={setCatalogOption}
        loadProviderOptions={async () => []}
        loadCatalogOptions={async () => []}
      />
      <DeleteInsurancePricingDialog
        id={pricing.id}
        name={name}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onDeleted={onDeleted}
      />
    </>
  )
}
