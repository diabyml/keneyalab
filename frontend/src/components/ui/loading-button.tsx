import type { VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { Slot } from "radix-ui"

import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface LoadingButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
}

function LoadingButton({
  className,
  loading = false,
  children,
  disabled,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: LoadingButtonProps) {
  const Comp = asChild ? Slot.Root : "button"
  const iconOnly = size?.startsWith("icon")

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={loading || disabled}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <Loader2 className="animate-spin" />}
      {!loading || !iconOnly ? children : null}
    </Comp>
  )
}

export { buttonVariants, LoadingButton }
