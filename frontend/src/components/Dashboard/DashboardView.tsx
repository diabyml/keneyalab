import { useQuery } from "@tanstack/react-query"
import {
  AlertTriangle,
  ArrowRight,
  Banknote,
  ClipboardList,
  FlaskConical,
  Microscope,
  Plus,
  ReceiptText,
  RefreshCw,
} from "lucide-react"
import type { ReactNode } from "react"
import { useMemo, useState } from "react"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  XAxis,
  YAxis,
} from "recharts"

import {
  type DashboardMetricPublic,
  type DashboardPublic,
  DashboardService,
  type DashboardStatusPointPublic,
} from "@/client"
import { PageHeader } from "@/components/Common/PageHeader"
import { StatusBadge } from "@/components/Common/StatusBadge"
import { formatDateTime } from "@/components/Orders/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { formatPrice } from "@/lib/format"
import { cn } from "@/lib/utils"

type Period = "today" | "week" | "month"

const metricIcons = {
  orders: ClipboardList,
  specimens: FlaskConical,
  results: Microscope,
  critical: AlertTriangle,
  finance: ReceiptText,
} as const

const statusColors = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--destructive)",
]

const trendConfig = {
  orders: { label: "Demandes", color: "var(--chart-1)" },
  specimens: { label: "Prélèvements", color: "var(--chart-2)" },
  results: { label: "Résultats", color: "var(--chart-4)" },
} satisfies ChartConfig

const statusConfig = {
  count: { label: "Demandes", color: "var(--chart-1)" },
} satisfies ChartConfig

function periodRange(period: Period) {
  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)

  if (period === "week") {
    start.setDate(start.getDate() - 6)
  } else if (period === "month") {
    start.setDate(1)
  }

  const end = new Date(now)
  end.setHours(23, 59, 59, 999)
  return { createdFrom: start.toISOString(), createdTo: end.toISOString() }
}

function metricValue(metric: DashboardMetricPublic) {
  if (metric.unit === "money") return formatPrice(metric.value)
  return new Intl.NumberFormat("fr-FR").format(Number(metric.value ?? 0))
}

function metricByKey(
  metrics: DashboardMetricPublic[] | undefined,
  key: string,
) {
  return metrics?.find((metric) => metric.key === key)
}

export function DashboardView() {
  const { user } = useAuth()
  const [period, setPeriod] = useState<Period>("today")
  const range = useMemo(() => periodRange(period), [period])
  const query = useQuery({
    queryKey: ["dashboard", range],
    queryFn: () =>
      DashboardService.readDashboard({
        createdFrom: range.createdFrom,
        createdTo: range.createdTo,
      }),
    refetchInterval: 60_000,
  })

  if (query.isLoading) {
    return <DashboardSkeleton />
  }

  if (query.isError || !query.data) {
    return (
      <DashboardShell
        userName={user?.full_name || user?.email || ""}
        period={period}
        setPeriod={setPeriod}
        onRefresh={() => query.refetch()}
      >
        <Card>
          <CardContent className="py-8 text-center">
            <div className="text-sm font-medium">
              Impossible de charger le tableau de bord.
            </div>
            <Button className="mt-4" onClick={() => query.refetch()}>
              <RefreshCw className="size-4" />
              Réessayer
            </Button>
          </CardContent>
        </Card>
      </DashboardShell>
    )
  }

  return (
    <DashboardShell
      userName={user?.full_name || user?.email || ""}
      period={period}
      setPeriod={setPeriod}
      onRefresh={() => query.refetch()}
      generatedAt={query.data.generated_at}
      isFetching={query.isFetching}
    >
      <DashboardContent data={query.data} />
    </DashboardShell>
  )
}

function DashboardShell({
  userName,
  period,
  setPeriod,
  onRefresh,
  generatedAt,
  isFetching = false,
  children,
}: {
  userName: string
  period: Period
  setPeriod: (period: Period) => void
  onRefresh: () => void
  generatedAt?: string
  isFetching?: boolean
  children: ReactNode
}) {
  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Centre de contrôle"
        title="Tableau de bord"
        description={`Bonjour ${userName}. Vue opérationnelle du laboratoire.`}
        metadata={
          generatedAt
            ? `Actualisé le ${formatDateTime(generatedAt)}`
            : undefined
        }
        actions={
          <>
            <div className="inline-flex rounded-md border bg-background p-0.5">
              {[
                ["today", "Aujourd'hui"],
                ["week", "7 jours"],
                ["month", "Mois"],
              ].map(([value, label]) => (
                <Button
                  key={value}
                  type="button"
                  size="sm"
                  variant={period === value ? "secondary" : "ghost"}
                  className="h-8 px-3"
                  onClick={() => setPeriod(value as Period)}
                >
                  {label}
                </Button>
              ))}
            </div>
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={isFetching}
              onClick={onRefresh}
            >
              <RefreshCw
                className={cn("size-4", isFetching && "animate-spin")}
              />
              Actualiser
            </Button>
          </>
        }
      />
      {children}
    </div>
  )
}

function DashboardContent({ data }: { data: DashboardPublic }) {
  const hasAnySection =
    data.orders ||
    data.specimens ||
    data.results ||
    data.critical ||
    data.finance

  if (!hasAnySection) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          Aucun module opérationnel n'est disponible pour votre profil.
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-5">
      <MetricGrid data={data} />
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.8fr)]">
        <WorkflowPanel data={data} />
        <QuickActions data={data} />
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        {data.orders && (
          <StatusChart rows={data.orders.status_breakdown ?? []} />
        )}
        <TrendChart data={data} />
      </div>
    </div>
  )
}

function MetricGrid({ data }: { data: DashboardPublic }) {
  const cards = [
    data.orders && {
      key: "orders",
      title: "Demandes",
      metric: metricByKey(data.orders.metrics, "total"),
      detail: metricByKey(data.orders.metrics, "cancelled"),
    },
    data.specimens && {
      key: "specimens",
      title: "Prélèvements",
      metric: metricByKey(data.specimens.metrics, "waiting"),
      detail: metricByKey(data.specimens.metrics, "rejected"),
    },
    data.results && {
      key: "results",
      title: "Résultats",
      metric: metricByKey(data.results.metrics, "entry_queue"),
      detail: metricByKey(data.results.metrics, "critical"),
    },
    data.critical && {
      key: "critical",
      title: "Valeurs critiques",
      metric: metricByKey(data.critical.metrics, "unacknowledged"),
      detail: undefined,
    },
    data.finance && {
      key: "finance",
      title: "Finance",
      metric: metricByKey(data.finance.metrics, "net_billed"),
      detail: metricByKey(data.finance.metrics, "outstanding"),
    },
  ].filter(Boolean) as Array<{
    key: keyof typeof metricIcons
    title: string
    metric?: DashboardMetricPublic
    detail?: DashboardMetricPublic
  }>

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => {
        const Icon = metricIcons[card.key]
        return (
          <Card
            key={card.key}
            className={cn(
              "specimen-rail transition-[transform,box-shadow,border-color] duration-150 ease-out hover:-translate-y-0.5 hover:border-primary/25",
              card.key === "critical" && "[--rail-color:var(--destructive)]",
              card.key === "finance" && "[--rail-color:var(--warning)]",
            )}
          >
            <CardHeader className="pb-0">
              <CardTitle className="flex items-center gap-2.5 text-muted-foreground">
                <span className="flex size-7 items-center justify-center rounded-md bg-primary/9 text-primary">
                  <Icon className="size-3.5" />
                </span>
                {card.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="font-heading text-2xl font-semibold tabular-nums tracking-tight">
                {card.metric ? metricValue(card.metric) : "0"}
              </div>
              {card.detail && (
                <div className="mt-1 text-xs text-muted-foreground">
                  {card.detail.label}: {metricValue(card.detail)}
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

function WorkflowPanel({ data }: { data: DashboardPublic }) {
  return (
    <Card className="border-primary/10">
      <CardHeader>
        <CardTitle>Flux de travail</CardTitle>
        <CardDescription>
          Files et éléments à traiter en priorité.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2">
        {data.specimens?.oldest_waiting && (
          <QueueItem
            title="Plus ancien prélèvement"
            href="/specimens"
            primary={data.specimens.oldest_waiting.accession_number}
            secondary={data.specimens.oldest_waiting.patient_name}
            badge={`${data.specimens.oldest_waiting.pending_count} en attente`}
          />
        )}
        {data.results && (
          <QueueItem
            title="Résultats à saisir"
            href="/results"
            primary={`${metricByKey(data.results.metrics, "entry_queue")?.value ?? 0} demande(s)`}
            secondary="File de saisie des résultats"
            badge="Saisie"
          />
        )}
        {data.results && (
          <QueueItem
            title="Résultats à vérifier"
            href="/results"
            primary={`${metricByKey(data.results.metrics, "verification_queue")?.value ?? 0} demande(s)`}
            secondary="Contrôle et validation"
            badge="Vérification"
          />
        )}
        {data.critical?.latest?.map((item) => (
          <QueueItem
            key={item.id}
            title="Valeur critique"
            href="/results"
            primary={`${item.accession_number} · ${item.analyte_name}`}
            secondary={`${item.patient_name} · ${item.result_value ?? "-"}`}
            badge="À acquitter"
            destructive
          />
        ))}
        {!data.specimens?.oldest_waiting &&
          !data.results &&
          !data.critical?.latest?.length && (
            <div className="col-span-full rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
              Aucun élément prioritaire pour la période sélectionnée.
            </div>
          )}
      </CardContent>
    </Card>
  )
}

function QueueItem({
  title,
  href,
  primary,
  secondary,
  badge,
  destructive = false,
}: {
  title: string
  href: string
  primary: string
  secondary: string
  badge: string
  destructive?: boolean
}) {
  return (
    <a
      href={href}
      className={cn(
        "specimen-rail group rounded-lg border bg-surface/55 p-3 pl-4 transition-[background-color,transform,border-color] duration-150 ease-out hover:-translate-y-0.5 hover:border-primary/25 hover:bg-accent/35",
        destructive && "[--rail-color:var(--destructive)]",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-muted-foreground">
          {title}
        </span>
        <StatusBadge tone={destructive ? "critical" : "pending"}>
          {badge}
        </StatusBadge>
      </div>
      <div className="mt-2 font-medium">{primary}</div>
      <div className="mt-1 text-xs text-muted-foreground">{secondary}</div>
    </a>
  )
}

function QuickActions({ data }: { data: DashboardPublic }) {
  const actions = data.quick_actions ?? []
  return (
    <Card className="bg-[linear-gradient(145deg,var(--card),var(--surface))]">
      <CardHeader>
        <CardTitle>Actions rapides</CardTitle>
        <CardDescription>Accès directs selon vos permissions.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {actions.map((action) => (
          <Button
            key={action.key}
            variant="outline"
            className="h-auto w-full justify-start gap-3 border-border/80 p-3 text-left hover:border-primary/30"
            asChild
          >
            <a href={action.href}>
              {action.key === "new_order" ? (
                <Plus className="size-4" />
              ) : (
                <ArrowRight className="size-4" />
              )}
              <span className="min-w-0 flex-1">
                <span className="block font-medium">{action.label}</span>
                <span className="block truncate text-xs font-normal text-muted-foreground">
                  {action.description}
                </span>
              </span>
            </a>
          </Button>
        ))}
        {!actions.length && (
          <div className="rounded-md border border-dashed p-5 text-center text-sm text-muted-foreground">
            Aucune action rapide disponible.
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function StatusChart({ rows }: { rows: DashboardStatusPointPublic[] }) {
  const data = rows.map((row, index) => ({
    ...row,
    fill: statusColors[index % statusColors.length],
  }))
  return (
    <Card>
      <CardHeader>
        <CardTitle>Statut des demandes</CardTitle>
        <CardDescription>
          Répartition sur la période sélectionnée.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={statusConfig} className="h-64 w-full">
          <BarChart data={data} margin={{ left: 0, right: 8 }}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              interval={0}
              tickFormatter={(value) =>
                String(value).replace("Résultats ", "Rés. ")
              }
            />
            <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
            <ChartTooltip content={<ChartTooltipContent hideLabel />} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((entry) => (
                <Cell key={entry.key} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

function TrendChart({ data }: { data: DashboardPublic }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Activité</CardTitle>
        <CardDescription>Demandes, prélèvements et résultats.</CardDescription>
        {data.finance && (
          <CardAction className="text-right">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Banknote className="size-3.5" />
              {metricValue(
                metricByKey(data.finance.metrics, "collected") ?? {
                  key: "collected",
                  label: "Encaissé",
                  value: 0,
                  unit: "money",
                },
              )}
            </div>
          </CardAction>
        )}
      </CardHeader>
      <CardContent>
        <ChartContainer config={trendConfig} className="h-64 w-full">
          <AreaChart data={data.trends ?? []} margin={{ left: 0, right: 8 }}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Area
              type="monotone"
              dataKey="orders"
              stroke="var(--color-orders)"
              fill="var(--color-orders)"
              fillOpacity={0.18}
            />
            <Area
              type="monotone"
              dataKey="specimens"
              stroke="var(--color-specimens)"
              fill="var(--color-specimens)"
              fillOpacity={0.14}
            />
            <Area
              type="monotone"
              dataKey="results"
              stroke="var(--color-results)"
              fill="var(--color-results)"
              fillOpacity={0.1}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-52" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-56" />
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
      </div>
    </div>
  )
}
