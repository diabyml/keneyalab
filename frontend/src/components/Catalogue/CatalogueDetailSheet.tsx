import { useQuery } from "@tanstack/react-query"

import { CatalogService } from "@/client"
import type { SearchSelectOption } from "@/components/Common/SearchSelect"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { formatPrice } from "@/lib/format"
import { CatalogTypeBadge } from "./CatalogTypeBadge"
import { CatalogueDetailContent } from "./CatalogueDetailContent"

interface CatalogueDetailSheetProps {
  selectedId: string | null
  onOpenChange: (open: boolean) => void
  onDelete: (id: string) => void
  onRestore: (id: string) => void
  loadCategoryOptions: (query: string) => Promise<SearchSelectOption[]>
}

export function CatalogueDetailSheet({
  selectedId,
  onOpenChange,
  onDelete,
  onRestore,
  loadCategoryOptions,
}: CatalogueDetailSheetProps) {
  const detailQuery = useQuery({
    queryKey: ["catalog", "detail", selectedId],
    queryFn: () => CatalogService.readCatalogEntry({ id: selectedId! }),
    enabled: selectedId !== null,
  })

  return (
    <Sheet open={selectedId !== null} onOpenChange={onOpenChange}>
      <SheetContent className="w-[calc(100vw-1rem)] overflow-hidden p-0 sm:max-w-2xl lg:max-w-3xl">
        <SheetHeader className="border-b pr-12">
          <SheetTitle className="flex items-center gap-2">
            {detailQuery.data ? (
              <>
                <CatalogTypeBadge type={detailQuery.data.type} />
                <span className="truncate">{detailQuery.data.name}</span>
              </>
            ) : (
              "Détail catalogue"
            )}
          </SheetTitle>
          <SheetDescription>
            {detailQuery.data
              ? `${detailQuery.data.code} · ${formatPrice(detailQuery.data.price)}`
              : "Chargement des informations catalogue…"}
          </SheetDescription>
        </SheetHeader>

        <div className="min-h-0 flex-1 overflow-y-auto p-4 pb-70">
          {detailQuery.isLoading && (
            <div className="space-y-3">
              {Array.from({ length: 8 }).map((_, index) => (
                <Skeleton key={index} className="h-10 w-full" />
              ))}
            </div>
          )}

          {!detailQuery.isLoading && !detailQuery.data && (
            <div className="text-sm text-muted-foreground">
              Impossible de charger le détail.
            </div>
          )}

          {detailQuery.data && (
            <CatalogueDetailContent
              detail={detailQuery.data}
              onDelete={onDelete}
              onRestore={onRestore}
              loadCategoryOptions={loadCategoryOptions}
            />
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
