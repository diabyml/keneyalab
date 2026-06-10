import { Skeleton } from "@/components/ui/skeleton"

const summarySections = [
  ["w-16", "w-36", "w-48"],
  ["w-24", "w-44", "w-32"],
  ["w-20", "w-full", "w-full", "w-24"],
]

export function OrderDetailSkeleton() {
  return (
    <div className="screen-order-detail space-y-6" aria-busy="true">
      <span className="sr-only" role="status">
        Chargement de la demande
      </span>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3">
          <Skeleton className="h-8 w-28" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-44" />
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
          <Skeleton className="h-4 w-64 max-w-full" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-28" />
          <Skeleton className="h-9 w-40" />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {summarySections.map((section, sectionIndex) => (
          <section key={section.join("-")} className="space-y-3 border-t pt-4">
            {section.map((width, index) => (
              <Skeleton
                key={`${width}-${index}`}
                className={
                  index === 0
                    ? `h-5 ${width}`
                    : sectionIndex === 2
                      ? `h-4 ${width}`
                      : `h-4 ${width} max-w-full`
                }
              />
            ))}
          </section>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="overflow-hidden rounded-md border">
          <div className="border-b bg-muted/20 px-4 py-3">
            <Skeleton className="h-5 w-28" />
          </div>
          {Array.from({ length: 4 }, (_, index) => (
            <div
              key={index}
              className="flex items-start justify-between gap-4 border-b px-4 py-3 last:border-b-0"
            >
              <div className="space-y-2">
                <Skeleton className="h-4 w-48 max-w-full" />
                <Skeleton className="h-3 w-20" />
              </div>
              <Skeleton className="h-4 w-24" />
            </div>
          ))}
        </section>

        <div className="space-y-6">
          <section className="overflow-hidden rounded-md border">
            <div className="border-b bg-muted/20 px-4 py-3">
              <Skeleton className="h-5 w-32" />
            </div>
            {Array.from({ length: 3 }, (_, index) => (
              <div
                key={index}
                className="space-y-2 border-b px-4 py-3 last:border-b-0"
              >
                <div className="flex items-center gap-2">
                  <Skeleton className="size-3 rounded-full" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-3 w-44 max-w-full" />
              </div>
            ))}
          </section>

          <section className="space-y-3 rounded-md border p-4">
            <Skeleton className="h-5 w-44" />
            <div className="grid grid-cols-2 gap-2">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
            <Skeleton className="h-9 w-full" />
          </section>
        </div>
      </div>
    </div>
  )
}
