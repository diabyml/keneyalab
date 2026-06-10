import type { HTMLAttributes } from "react"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

export function NumberField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Input
        type="number"
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
      />
    </div>
  )
}

export function DecimalField(props: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="grid gap-2">
      <Label>{props.label}</Label>
      <Input
        type="number"
        step="0.01"
        value={props.value}
        onChange={(event) => props.onChange(event.currentTarget.value)}
      />
    </div>
  )
}

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  inputMode,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  inputMode?: HTMLAttributes<HTMLInputElement>["inputMode"]
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Input
        value={value}
        placeholder={placeholder}
        inputMode={inputMode}
        onChange={(event) => onChange(event.currentTarget.value)}
      />
    </div>
  )
}

export function OptionTextarea({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Textarea
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        rows={5}
        placeholder={
          options.length ? options.join("\n") : "Une valeur par ligne"
        }
      />
    </div>
  )
}
