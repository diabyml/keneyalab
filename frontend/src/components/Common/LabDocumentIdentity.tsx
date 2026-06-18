import { useLabSettings } from "@/hooks/useLabSettings"
import { cn } from "@/lib/utils"

type HeaderProps = {
  title?: string
  compact?: boolean
  className?: string
}

export function LabDocumentHeader({
  title,
  compact = false,
  className,
}: HeaderProps) {
  const { data } = useLabSettings()
  const name = data?.display_name || "KENEYA LAB"
  const contact = [
    data?.primary_phone,
    data?.email,
    data?.city,
    data?.country,
  ].filter(Boolean)

  return (
    <header
      className={cn(
        "flex items-center justify-center gap-3 text-center",
        !compact && "border-b pb-5",
        className,
      )}
    >
      {data?.logo_url && (
        <img
          src={data.logo_url}
          alt={`Logo ${name}`}
          className={cn(
            "shrink-0 object-contain",
            compact ? "size-10" : "size-16",
          )}
        />
      )}
      <div>
        <h1 className={cn("font-bold", compact ? "text-base" : "text-xl")}>
          {name}
        </h1>
        {data?.slogan && <p>{data.slogan}</p>}
        {!compact && contact.length > 0 && (
          <p className="text-sm text-muted-foreground">{contact.join(" · ")}</p>
        )}
        {title && (
          <p className={cn("font-medium", !compact && "mt-2 text-lg")}>
            {title}
          </p>
        )}
      </div>
    </header>
  )
}

export function LabDocumentFooter({
  compact = false,
  className,
}: {
  compact?: boolean
  className?: string
}) {
  const { data } = useLabSettings()
  const fallback = compact ? "Merci pour votre confiance." : null
  const footer = data?.document_footer || fallback
  const contact = [
    data?.address,
    data?.city,
    data?.primary_phone,
    data?.email,
    data?.website,
  ].filter(Boolean)

  if (!footer && contact.length === 0) return null

  return (
    <footer
      className={cn(
        "text-center text-muted-foreground",
        compact ? "mt-3 text-[9px]" : "mt-6 border-t pt-4 text-xs",
        className,
      )}
    >
      {footer && <p className="whitespace-pre-line">{footer}</p>}
      {!compact && contact.length > 0 && <p>{contact.join(" · ")}</p>}
    </footer>
  )
}

export function LabDocumentName({ className }: { className?: string }) {
  const { data } = useLabSettings()
  return <span className={className}>{data?.display_name || "KENEYA LAB"}</span>
}
