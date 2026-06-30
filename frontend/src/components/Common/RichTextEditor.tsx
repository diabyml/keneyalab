import { mergeAttributes, Node } from "@tiptap/core"
import LinkExtension from "@tiptap/extension-link"
import Placeholder from "@tiptap/extension-placeholder"
import { Table } from "@tiptap/extension-table"
import { TableCell } from "@tiptap/extension-table-cell"
import { TableHeader } from "@tiptap/extension-table-header"
import { TableRow } from "@tiptap/extension-table-row"
import TextAlign from "@tiptap/extension-text-align"
import UnderlineExtension from "@tiptap/extension-underline"
import { EditorContent, useEditor } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Bold,
  Braces,
  Eraser,
  Heading2,
  Heading3,
  Italic,
  Link,
  List,
  ListOrdered,
  Pilcrow,
  Quote,
  Redo2,
  Table2,
  Underline,
  Undo2,
} from "lucide-react"
import type { ReactNode } from "react"
import { useEffect, useMemo, useRef } from "react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

export type RichTextVariable = {
  label: string
  description?: string
  kind: string
  id?: string | null
  field: string
  value?: boolean | number | string | null
}

export type RichTextVariableGroup = {
  label: string
  items: RichTextVariable[]
}

interface RichTextEditorProps {
  value: string | null | undefined
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  minHeightClassName?: string
  variables?: RichTextVariableGroup[]
  disabled?: boolean
}

const VariableNode = Node.create({
  name: "variable",
  group: "inline",
  inline: true,
  atom: true,
  selectable: false,

  addAttributes() {
    return {
      kind: { default: "" },
      id: { default: "" },
      field: { default: "" },
      label: { default: "" },
    }
  },

  parseHTML() {
    return [
      {
        tag: "span[data-variable-kind]",
        getAttrs: (element) => {
          if (!(element instanceof HTMLElement)) return false
          return {
            kind: element.dataset.variableKind ?? "",
            id: element.dataset.variableId ?? "",
            field: element.dataset.variableField ?? "",
            label: element.textContent ?? "",
          }
        },
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "span",
      mergeAttributes({
        class:
          "interpretation-variable rounded border bg-muted px-1 py-0.5 font-medium",
        "data-variable-kind": HTMLAttributes.kind,
        "data-variable-id": HTMLAttributes.id,
        "data-variable-field": HTMLAttributes.field,
        contenteditable: "false",
      }),
      HTMLAttributes.label || "Variable",
    ]
  },
})

function ToolbarButton({
  label,
  active,
  disabled,
  onClick,
  children,
}: {
  label: string
  active?: boolean
  disabled?: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          type="button"
          variant={active ? "secondary" : "ghost"}
          size="icon"
          title={label}
          disabled={disabled}
          onClick={onClick}
        >
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}

export function RichTextEditor({
  value,
  onChange,
  placeholder = "Saisir le contenu...",
  className,
  minHeightClassName = "min-h-32",
  variables = [],
  disabled = false,
}: RichTextEditorProps) {
  const variableDisplayMap = useMemo(() => {
    const displayMap = new Map<string, string>()
    for (const group of variables) {
      for (const variable of group.items) {
        displayMap.set(variableKey(variable), variableDisplayValue(variable))
      }
    }
    return displayMap
  }, [variables])

  const contentWithVariableValues = useMemo(
    () => renderVariableValues(value ?? "", variableDisplayMap),
    [value, variableDisplayMap],
  )
  const lastEmittedHtmlRef = useRef<string | null>(null)

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ underline: false, link: false }),
      UnderlineExtension,
      LinkExtension.configure({
        openOnClick: false,
        autolink: true,
        defaultProtocol: "https",
      }),
      TextAlign.configure({ types: ["heading", "paragraph"] }),
      Placeholder.configure({ placeholder }),
      Table.configure({ resizable: false }),
      TableRow,
      TableHeader,
      TableCell,
      VariableNode,
    ],
    content: contentWithVariableValues,
    editable: !disabled,
    editorProps: {
      attributes: {
        class: cn(
          minHeightClassName,
          "rounded-b-md px-3 py-2 text-sm outline-none",
          "prose prose-sm max-w-none",
          "[&_blockquote]:border-l-2 [&_blockquote]:pl-3 [&_blockquote]:italic",
          "[&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-1 [&_table]:my-2",
          "[&_table]:w-full [&_table]:border-collapse [&_td]:border",
          "[&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:bg-muted/60",
          "[&_th]:px-2 [&_th]:py-1 [&_ul]:list-disc [&_ul]:pl-5",
        ),
      },
    },
    immediatelyRender: false,
    onUpdate: ({ editor: currentEditor }) => {
      const html = currentEditor.getHTML()
      lastEmittedHtmlRef.current = html
      onChange(html)
    },
  })

  useEffect(() => {
    if (!editor) return
    editor.setEditable(!disabled)
  }, [disabled, editor])

  useEffect(() => {
    if (!editor) return

    const nextValue = contentWithVariableValues
    if (editor.isFocused && lastEmittedHtmlRef.current === (value ?? "")) {
      return
    }
    if (editor.getHTML() !== nextValue) {
      editor.commands.setContent(nextValue, { emitUpdate: false })
    }
  }, [contentWithVariableValues, editor, value])

  const runCommand = (command: () => void) => {
    command()
    editor?.commands.focus()
  }

  const setLink = () => {
    if (!editor) return
    const previousUrl = editor.getAttributes("link").href as string | undefined
    const url = window.prompt("Lien", previousUrl ?? "https://")
    if (url === null) return
    if (!url.trim()) {
      runCommand(() => editor.chain().focus().unsetLink().run())
      return
    }
    runCommand(() =>
      editor
        .chain()
        .focus()
        .extendMarkRange("link")
        .setLink({ href: url })
        .run(),
    )
  }

  const insertVariable = (variable: RichTextVariable) => {
    if (!editor) return
    const displayValue = variableDisplayValue(variable)
    runCommand(() =>
      editor
        .chain()
        .focus()
        .insertContent({
          type: "variable",
          attrs: {
            kind: variable.kind,
            id: variable.id ?? "",
            field: variable.field,
            label: displayValue,
          },
        })
        .insertContent(" ")
        .run(),
    )
  }

  const hasVariables = variables.some((group) => group.items.length > 0)
  const disabledToolbar = disabled || !editor

  return (
    <TooltipProvider delayDuration={250} skipDelayDuration={80}>
      <div
        className={cn(
          "overflow-hidden rounded-md border bg-background",
          className,
        )}
      >
        <div className="flex flex-wrap items-center gap-1 border-b bg-muted/20 p-1">
          <ToolbarButton
            label="Annuler"
            disabled={disabledToolbar || !editor?.can().undo()}
            onClick={() =>
              runCommand(() => editor?.chain().focus().undo().run())
            }
          >
            <Undo2 className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Rétablir"
            disabled={disabledToolbar || !editor?.can().redo()}
            onClick={() =>
              runCommand(() => editor?.chain().focus().redo().run())
            }
          >
            <Redo2 className="size-4" />
          </ToolbarButton>
          <span className="mx-1 h-5 w-px bg-border" />
          <ToolbarButton
            label="Gras"
            active={editor?.isActive("bold")}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() => editor?.chain().focus().toggleBold().run())
            }
          >
            <Bold className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Italique"
            active={editor?.isActive("italic")}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() => editor?.chain().focus().toggleItalic().run())
            }
          >
            <Italic className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Souligné"
            active={editor?.isActive("underline")}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() => editor?.chain().focus().toggleUnderline().run())
            }
          >
            <Underline className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Lien"
            active={editor?.isActive("link")}
            disabled={disabledToolbar}
            onClick={setLink}
          >
            <Link className="size-4" />
          </ToolbarButton>
          <span className="mx-1 h-5 w-px bg-border" />
          <ToolbarButton
            label="Titre 2"
            active={editor?.isActive("heading", { level: 2 })}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().toggleHeading({ level: 2 }).run(),
              )
            }
          >
            <Heading2 className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Titre 3"
            active={editor?.isActive("heading", { level: 3 })}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().toggleHeading({ level: 3 }).run(),
              )
            }
          >
            <Heading3 className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Paragraphe"
            active={editor?.isActive("paragraph")}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() => editor?.chain().focus().setParagraph().run())
            }
          >
            <Pilcrow className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Citation"
            active={editor?.isActive("blockquote")}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() => editor?.chain().focus().toggleBlockquote().run())
            }
          >
            <Quote className="size-4" />
          </ToolbarButton>
          <span className="mx-1 h-5 w-px bg-border" />
          <ToolbarButton
            label="Liste à puces"
            active={editor?.isActive("bulletList")}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() => editor?.chain().focus().toggleBulletList().run())
            }
          >
            <List className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Liste numérotée"
            active={editor?.isActive("orderedList")}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().toggleOrderedList().run(),
              )
            }
          >
            <ListOrdered className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Tableau"
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor
                  ?.chain()
                  .focus()
                  .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
                  .run(),
              )
            }
          >
            <Table2 className="size-4" />
          </ToolbarButton>
          <span className="mx-1 h-5 w-px bg-border" />
          <ToolbarButton
            label="Aligner à gauche"
            active={editor?.isActive({ textAlign: "left" })}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().setTextAlign("left").run(),
              )
            }
          >
            <AlignLeft className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Centrer"
            active={editor?.isActive({ textAlign: "center" })}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().setTextAlign("center").run(),
              )
            }
          >
            <AlignCenter className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Aligner à droite"
            active={editor?.isActive({ textAlign: "right" })}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().setTextAlign("right").run(),
              )
            }
          >
            <AlignRight className="size-4" />
          </ToolbarButton>
          <ToolbarButton
            label="Justifier"
            active={editor?.isActive({ textAlign: "justify" })}
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().setTextAlign("justify").run(),
              )
            }
          >
            <AlignJustify className="size-4" />
          </ToolbarButton>
          <span className="mx-1 h-5 w-px bg-border" />
          <DropdownMenu>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    disabled={disabledToolbar || !hasVariables}
                    title="Insérer une variable"
                  >
                    <Braces className="size-4" />
                  </Button>
                </DropdownMenuTrigger>
              </TooltipTrigger>
              <TooltipContent>Insérer une variable</TooltipContent>
            </Tooltip>
            <DropdownMenuContent
              align="start"
              className="max-h-96 w-80 overflow-auto"
            >
              <DropdownMenuLabel>Variables du rapport</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {variables.map((group) => (
                <DropdownMenuSub key={group.label}>
                  <DropdownMenuSubTrigger>{group.label}</DropdownMenuSubTrigger>
                  <DropdownMenuSubContent className="max-h-80 w-80 overflow-auto">
                    {group.items.map((variable) => (
                      <DropdownMenuItem
                        key={`${variable.kind}:${variable.id ?? ""}:${variable.field}`}
                        onClick={() => insertVariable(variable)}
                      >
                        <span className="flex min-w-0 flex-col">
                          <span className="truncate">{variable.label}</span>
                          <span className="truncate text-xs text-muted-foreground">
                            {variableDisplayValue(variable)}
                          </span>
                          {variable.description && (
                            <span className="truncate text-xs text-muted-foreground">
                              {variable.description}
                            </span>
                          )}
                        </span>
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <ToolbarButton
            label="Effacer le formatage"
            disabled={disabledToolbar}
            onClick={() =>
              runCommand(() =>
                editor?.chain().focus().unsetAllMarks().clearNodes().run(),
              )
            }
          >
            <Eraser className="size-4" />
          </ToolbarButton>
        </div>
        <EditorContent
          editor={editor}
          className="rounded-b-md focus-within:ring-[3px] focus-within:ring-ring/50"
        />
      </div>
    </TooltipProvider>
  )
}

function variableKey(
  variable: Pick<RichTextVariable, "field" | "id" | "kind">,
) {
  return `${variable.kind}:${variable.id ?? ""}:${variable.field}`
}

function variableDisplayValue(variable: RichTextVariable) {
  if (variable.value === null || variable.value === undefined) return "—"
  const value = String(variable.value).trim()
  return value || "—"
}

function renderVariableValues(html: string, displayMap: Map<string, string>) {
  if (!html || !displayMap.size || typeof document === "undefined") {
    return html
  }

  const parsed = document.implementation.createHTMLDocument("")
  parsed.body.innerHTML = html
  parsed.body
    .querySelectorAll<HTMLElement>("span[data-variable-kind]")
    .forEach((element) => {
      const key = `${element.dataset.variableKind ?? ""}:${element.dataset.variableId ?? ""}:${element.dataset.variableField ?? ""}`
      const displayValue = displayMap.get(key)
      if (displayValue !== undefined) {
        element.textContent = displayValue
      }
    })

  return parsed.body.innerHTML
}
