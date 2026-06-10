import { FlaskConical, PanelTop } from "lucide-react"

import type { CatalogType } from "@/client"
import { Badge } from "@/components/ui/badge"
import { catalogTypeLabel } from "./utils"

export function CatalogTypeBadge({ type }: { type: CatalogType }) {
  return (
    <Badge variant={type === "item" ? "secondary" : "outline"}>
      {type === "item" ? (
        <FlaskConical className="mr-1 size-3" />
      ) : (
        <PanelTop className="mr-1 size-3" />
      )}
      {catalogTypeLabel(type)}
    </Badge>
  )
}
