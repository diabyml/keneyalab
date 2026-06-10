import { Link } from "@tanstack/react-router"
import { Microscope } from "lucide-react"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const content = (
    <span
      className={cn(
        "inline-flex items-center gap-2 text-base font-semibold",
        className,
      )}
    >
      {/* Icon */}
      {variant === "responsive" ? (
        <>
          <Microscope
            className="size-5 shrink-0 text-primary group-data-[collapsible=icon]:block hidden"
            strokeWidth={2}
            aria-hidden="true"
          />
          <Microscope
            className="size-5 shrink-0 text-primary group-data-[collapsible=icon]:hidden"
            strokeWidth={2}
            aria-hidden="true"
          />
        </>
      ) : (
        <Microscope
          className={cn(
            "shrink-0 text-primary",
            variant === "icon" ? "size-5" : "size-5",
          )}
          strokeWidth={2}
          aria-hidden="true"
        />
      )}

      {/* Text — hidden when icon-only or when sidebar is collapsed */}
      {variant !== "icon" && (
        <span
          className={cn(
            "font-bold tracking-tight whitespace-nowrap",
            variant === "responsive" && "group-data-[collapsible=icon]:hidden",
          )}
        >
          KeneyaLab
        </span>
      )}
    </span>
  )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
