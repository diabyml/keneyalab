import { cn } from "@/lib/utils"

interface HtmlContentProps {
  html: string | null | undefined
  className?: string
  emptyClassName?: string
}

export function HtmlContent({
  html,
  className,
  emptyClassName,
}: HtmlContentProps) {
  if (!html) {
    return (
      <span className={cn("text-muted-foreground", emptyClassName)}>—</span>
    )
  }

  const htmlProps = { dangerouslySetInnerHTML: { __html: html } }

  return (
    <div
      className={cn(
        "prose prose-sm max-w-none text-sm [&_ol]:my-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-0 [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5",
        className,
      )}
      {...htmlProps}
    />
  )
}
