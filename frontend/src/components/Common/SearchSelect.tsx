import { Loader2, Search } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"

import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox"
import { cn } from "@/lib/utils"

export interface SearchSelectOption {
  value: string
  label: string
  description?: string
  disabled?: boolean
}

interface SearchSelectProps {
  value: string | null
  onValueChange: (value: string | null, option?: SearchSelectOption) => void
  loadOptions: (query: string) => Promise<SearchSelectOption[]>
  selectedOption?: SearchSelectOption | null
  placeholder?: string
  searchPlaceholder?: string
  emptyMessage?: string
  loadingMessage?: string
  disabled?: boolean
  clearable?: boolean
  minSearchLength?: number
  debounceMs?: number
  className?: string
  autoFocus?: boolean
  onEscape?: () => void
}

const DEFAULT_DEBOUNCE_MS = 250

export function SearchSelect({
  value,
  onValueChange,
  loadOptions,
  selectedOption,
  placeholder = "Sélectionner…",
  searchPlaceholder = "Rechercher…",
  emptyMessage = "Aucun résultat",
  loadingMessage = "Recherche…",
  disabled = false,
  clearable = true,
  minSearchLength = 0,
  debounceMs = DEFAULT_DEBOUNCE_MS,
  className,
  autoFocus = false,
  onEscape,
}: SearchSelectProps) {
  const [open, setOpen] = useState(false)
  const [inputValue, setInputValue] = useState("")
  const [options, setOptions] = useState<SearchSelectOption[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const requestId = useRef(0)
  const wrapperRef = useRef<HTMLDivElement | null>(null)
  const [portalContainer, setPortalContainer] = useState<
    HTMLElement | null | undefined
  >(undefined)

  const selectedValue = useMemo(() => {
    if (!value) return null
    const option =
      selectedOption ?? options.find((item) => item.value === value) ?? null
    return option ?? { value, label: value }
  }, [options, selectedOption, value])

  useEffect(() => {
    if (!open) return

    const query = inputValue.trim()
    if (query.length < minSearchLength) {
      setOptions([])
      setIsLoading(false)
      return
    }

    const currentRequest = requestId.current + 1
    requestId.current = currentRequest
    setIsLoading(true)

    const timeout = window.setTimeout(() => {
      loadOptions(query)
        .then((loadedOptions) => {
          if (requestId.current === currentRequest) {
            setOptions(loadedOptions)
          }
        })
        .catch(() => {
          if (requestId.current === currentRequest) {
            setOptions([])
          }
        })
        .finally(() => {
          if (requestId.current === currentRequest) {
            setIsLoading(false)
          }
        })
    }, debounceMs)

    return () => window.clearTimeout(timeout)
  }, [debounceMs, inputValue, loadOptions, minSearchLength, open])

  useEffect(() => {
    const wrapper = wrapperRef.current
    if (!wrapper) return
    let el: HTMLElement | null = wrapper.parentElement
    while (el) {
      const slot = el.getAttribute("data-slot")
      if (slot === "dialog-content" || slot === "sheet-content") {
        setPortalContainer(el)
        return
      }
      el = el.parentElement
    }
  }, [])

  return (
    <div ref={wrapperRef}>
      <Combobox<SearchSelectOption>
        open={open}
        onOpenChange={setOpen}
        inputValue={open ? inputValue : (selectedValue?.label ?? "")}
        onInputValueChange={(nextInputValue) => setInputValue(nextInputValue)}
        value={selectedValue}
        onValueChange={(option) => {
          onValueChange(option?.value ?? null, option ?? undefined)
          setInputValue("")
          setOpen(false)
        }}
        itemToStringLabel={(option) => option?.label ?? ""}
        itemToStringValue={(option) => option?.value ?? ""}
        isItemEqualToValue={(option, selected) =>
          option.value === selected.value
        }
        filter={null}
      >
        <ComboboxInput
          className={cn("w-full", className)}
          disabled={disabled}
          placeholder={open ? searchPlaceholder : placeholder}
          showClear={clearable && !!value}
          autoFocus={autoFocus}
          onKeyDown={(event) => {
            if (event.key === "Escape") onEscape?.()
          }}
        />
        <ComboboxContent
          container={portalContainer}
          positionMethod={portalContainer ? "fixed" : undefined}
        >
          <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-muted-foreground">
            {isLoading ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Search className="size-3.5" />
            )}
            <span>{isLoading ? loadingMessage : searchPlaceholder}</span>
          </div>
          <ComboboxList>
            {options.map((option) => (
              <ComboboxItem
                key={option.value}
                value={option}
                disabled={option.disabled}
                className="items-start"
              >
                <span className="min-w-0">
                  <span className="block truncate">{option.label}</span>
                  {option.description && (
                    <span className="block truncate text-xs text-muted-foreground">
                      {option.description}
                    </span>
                  )}
                </span>
              </ComboboxItem>
            ))}
            {!isLoading && (
              <ComboboxEmpty>
                {inputValue.trim().length < minSearchLength
                  ? `Saisissez au moins ${minSearchLength} caractère${minSearchLength > 1 ? "s" : ""}`
                  : emptyMessage}
              </ComboboxEmpty>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
    </div>
  )
}
