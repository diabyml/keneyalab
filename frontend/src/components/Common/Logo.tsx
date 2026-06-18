import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 40 40"
      className={cn("shrink-0", className)}
      fill="none"
      aria-hidden="true"
    >
      <rect width="40" height="40" rx="12" fill="#0F766E" />
      <path
        d="M13 10.5V29.5M13 20H18.5M18.5 20L26 11.5M18.5 20L27.5 29"
        stroke="white"
        strokeWidth="3.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="27" cy="10.5" r="3.5" fill="#67E8F9" />
      <circle cx="28.5" cy="29.5" r="3.5" fill="#2DD4BF" />
      <circle cx="13" cy="20" r="2.25" fill="white" />
    </svg>
  )
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const content = (
    <span
      className={cn(
        "inline-flex items-center gap-[0.55em] text-base",
        className,
      )}
    >
      <BrandMark className="size-[1.85em]" />

      {variant !== "icon" && (
        <span
          className={cn(
            "whitespace-nowrap font-extrabold tracking-[-0.045em]",
            variant === "responsive" && "group-data-[collapsible=icon]:hidden",
          )}
        >
          Keneya<span className="text-teal-600 dark:text-teal-400">Lab</span>
        </span>
      )}
    </span>
  )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
