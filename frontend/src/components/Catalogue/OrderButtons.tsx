import { ArrowDown, ArrowUp } from "lucide-react"

import { Button } from "@/components/ui/button"

export function OrderButtons({
  index,
  length,
  onMove,
}: {
  index: number
  length: number
  onMove: (direction: -1 | 1) => void
}) {
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon"
        className="size-8"
        onClick={() => onMove(-1)}
        disabled={index === 0}
      >
        <ArrowUp className="size-4" />
        <span className="sr-only">Monter</span>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="size-8"
        onClick={() => onMove(1)}
        disabled={index + 1 >= length}
      >
        <ArrowDown className="size-4" />
        <span className="sr-only">Descendre</span>
      </Button>
    </div>
  )
}
