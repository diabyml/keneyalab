import UnderlineExtension from "@tiptap/extension-underline"
import { EditorContent, useEditor } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import {
  Bold,
  Eraser,
  Italic,
  List,
  ListOrdered,
  Pilcrow,
  Underline,
} from "lucide-react"
import { useEffect } from "react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface RichTextEditorProps {
  value: string | null | undefined
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function RichTextEditor({
  value,
  onChange,
  placeholder = "Saisir le contenu...",
  className,
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ underline: false }),
      UnderlineExtension,
    ],
    content: value ?? "",
    editorProps: {
      attributes: {
        class:
          "min-h-32 rounded-b-md px-3 py-2 text-sm outline-none [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-1 [&_ul]:list-disc [&_ul]:pl-5",
      },
    },
    immediatelyRender: false,
    onUpdate: ({ editor: currentEditor }) => {
      onChange(currentEditor.getHTML())
    },
  })

  useEffect(() => {
    if (!editor) return

    const nextValue = value ?? ""
    if (editor.getHTML() !== nextValue) {
      editor.commands.setContent(nextValue, { emitUpdate: false })
    }
  }, [editor, value])

  const runCommand = (command: () => void) => {
    command()
    editor?.commands.focus()
  }

  return (
    <div className={cn("rounded-md border bg-background", className)}>
      <div className="flex flex-wrap items-center gap-1 border-b p-1">
        <Button
          type="button"
          variant={editor?.isActive("bold") ? "secondary" : "ghost"}
          size="icon"
          title="Gras"
          disabled={!editor}
          onClick={() =>
            runCommand(() => editor?.chain().focus().toggleBold().run())
          }
        >
          <Bold className="size-4" />
        </Button>
        <Button
          type="button"
          variant={editor?.isActive("italic") ? "secondary" : "ghost"}
          size="icon"
          title="Italique"
          disabled={!editor}
          onClick={() =>
            runCommand(() => editor?.chain().focus().toggleItalic().run())
          }
        >
          <Italic className="size-4" />
        </Button>
        <Button
          type="button"
          variant={editor?.isActive("underline") ? "secondary" : "ghost"}
          size="icon"
          title="Souligné"
          disabled={!editor}
          onClick={() =>
            runCommand(() => editor?.chain().focus().toggleUnderline().run())
          }
        >
          <Underline className="size-4" />
        </Button>
        <Button
          type="button"
          variant={editor?.isActive("bulletList") ? "secondary" : "ghost"}
          size="icon"
          title="Liste à puces"
          disabled={!editor}
          onClick={() =>
            runCommand(() => editor?.chain().focus().toggleBulletList().run())
          }
        >
          <List className="size-4" />
        </Button>
        <Button
          type="button"
          variant={editor?.isActive("orderedList") ? "secondary" : "ghost"}
          size="icon"
          title="Liste numérotée"
          disabled={!editor}
          onClick={() =>
            runCommand(() => editor?.chain().focus().toggleOrderedList().run())
          }
        >
          <ListOrdered className="size-4" />
        </Button>
        <Button
          type="button"
          variant={editor?.isActive("paragraph") ? "secondary" : "ghost"}
          size="icon"
          title="Paragraphe"
          disabled={!editor}
          onClick={() =>
            runCommand(() => editor?.chain().focus().setParagraph().run())
          }
        >
          <Pilcrow className="size-4" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          title="Effacer le formatage"
          disabled={!editor}
          onClick={() =>
            runCommand(() =>
              editor?.chain().focus().unsetAllMarks().clearNodes().run(),
            )
          }
        >
          <Eraser className="size-4" />
        </Button>
      </div>
      {editor?.isEmpty && placeholder ? (
        <div className="border-b px-3 py-2 text-sm text-muted-foreground">
          {placeholder}
        </div>
      ) : null}
      <EditorContent
        editor={editor}
        className="rounded-b-md focus-within:ring-[3px] focus-within:ring-ring/50"
      />
    </div>
  )
}
