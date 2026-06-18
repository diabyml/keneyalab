import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ArrowUpRight, CircleAlert } from "lucide-react"

import { AuditLogsService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  AUDIT_ACTION_LABELS,
  AUDIT_CATEGORY_LABELS,
  auditEntityLabel,
} from "./labels"
import { asRecord, entityLink, formatAuditDate } from "./utils"

function ValueBlock({ value }: { value: unknown }) {
  if (value === undefined)
    return <span className="text-muted-foreground">Non renseigné</span>
  if (value === null) return <span className="text-muted-foreground">Vide</span>
  const rendered =
    typeof value === "string" ? value : JSON.stringify(value, null, 2)
  return (
    <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted/50 p-2 font-mono text-xs">
      {rendered}
    </pre>
  )
}

function ContextValue({
  label,
  value,
}: {
  label: string
  value?: string | null
}) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 break-all font-mono text-xs">{value || "—"}</dd>
    </div>
  )
}

export function AuditDetailSheet({
  auditId,
  onOpenChange,
}: {
  auditId: string | null
  onOpenChange: (open: boolean) => void
}) {
  const query = useQuery({
    queryKey: ["audit-log", auditId],
    queryFn: () => AuditLogsService.readAuditLog({ auditId: auditId! }),
    enabled: Boolean(auditId),
  })
  const event = query.data
  const oldValues = asRecord(event?.old_values)
  const newValues = asRecord(event?.new_values)
  const fields = [
    ...new Set([...Object.keys(oldValues), ...Object.keys(newValues)]),
  ]
  const link = event ? entityLink(event) : null

  return (
    <Sheet open={Boolean(auditId)} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-2xl">
        <SheetHeader className="border-b">
          <div className="flex flex-wrap items-center gap-2 pr-10">
            {event && (
              <>
                <Badge>{AUDIT_ACTION_LABELS[event.action]}</Badge>
                <Badge variant="outline">
                  {AUDIT_CATEGORY_LABELS[event.category]}
                </Badge>
              </>
            )}
          </div>
          <SheetTitle className="text-base">Détail de l'événement</SheetTitle>
          <SheetDescription>
            {event
              ? `${auditEntityLabel(event.table_name)} · ${formatAuditDate(event.performed_at)}`
              : "Chargement du journal d'audit"}
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="min-h-0 flex-1">
          {query.isLoading && (
            <div className="p-6 text-muted-foreground">Chargement…</div>
          )}
          {query.isError && (
            <div className="flex items-center gap-2 p-6 text-destructive">
              <CircleAlert className="size-4" />
              Impossible de charger cet événement.
            </div>
          )}
          {event && (
            <div className="space-y-6 p-6">
              <section className="rounded-lg border p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-medium">
                      {event.record_label ?? auditEntityLabel(event.table_name)}
                    </h3>
                    <p className="mt-1 font-mono text-xs text-muted-foreground">
                      {event.record_id ??
                        "Événement sans enregistrement associé"}
                    </p>
                  </div>
                  {link && (
                    <Button variant="outline" size="sm" asChild>
                      <Link to={link.to} params={link.params as any}>
                        Ouvrir
                        <ArrowUpRight className="size-3.5" />
                      </Link>
                    </Button>
                  )}
                </div>
              </section>

              <section>
                <h3 className="mb-3 text-sm font-medium">Modifications</h3>
                {fields.length === 0 ? (
                  <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                    Aucune différence de champ pour cet événement.
                  </p>
                ) : (
                  <div className="overflow-hidden rounded-lg border">
                    <div className="grid grid-cols-[minmax(110px,0.7fr)_1fr_1fr] gap-px bg-border text-xs">
                      <div className="bg-muted/60 p-2 font-medium">Champ</div>
                      <div className="bg-muted/60 p-2 font-medium">Avant</div>
                      <div className="bg-muted/60 p-2 font-medium">Après</div>
                      {fields.map((field) => (
                        <div key={field} className="contents">
                          <div className="bg-background p-2 font-mono">
                            {field}
                          </div>
                          <div className="min-w-0 bg-background p-2">
                            <ValueBlock value={oldValues[field]} />
                          </div>
                          <div className="min-w-0 bg-background p-2">
                            <ValueBlock value={newValues[field]} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </section>

              {Object.keys(asRecord(event.metadata)).length > 0 && (
                <section>
                  <h3 className="mb-3 text-sm font-medium">Contexte métier</h3>
                  <ValueBlock value={event.metadata} />
                </section>
              )}

              <section>
                <h3 className="mb-3 text-sm font-medium">Attribution</h3>
                <dl className="grid gap-4 rounded-lg border p-4 sm:grid-cols-2">
                  <ContextValue
                    label="Acteur"
                    value={event.actor_name ?? event.actor_email ?? "Système"}
                  />
                  <ContextValue label="Email" value={event.actor_email} />
                  <ContextValue label="Source" value={event.source} />
                  <ContextValue label="Adresse IP" value={event.ip_address} />
                  <ContextValue
                    label="Méthode HTTP"
                    value={event.http_method}
                  />
                  <ContextValue label="Chemin" value={event.http_path} />
                  <ContextValue
                    label="ID de requête"
                    value={event.request_id}
                  />
                  <ContextValue
                    label="ID de corrélation"
                    value={event.correlation_id}
                  />
                  <ContextValue
                    label="Agent utilisateur"
                    value={event.user_agent}
                  />
                  <ContextValue label="ID événement" value={event.id} />
                </dl>
              </section>
            </div>
          )}
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
