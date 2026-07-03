import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  Bell,
  Check,
  CheckCheck,
  FlaskConical,
  Loader2,
  Microscope,
} from "lucide-react"

import {
  CriticalNotificationsService,
  type NotificationPublic,
  NotificationsService,
  type NotificationType,
  ReagentsService,
} from "@/client"
import { formatDateTime } from "@/components/Orders/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useCustomToast from "@/hooks/useCustomToast"
import { usePermission } from "@/hooks/usePermission"
import { cn } from "@/lib/utils"

const notificationTypeLabels: Record<NotificationType, string> = {
  result_ready: "Résultat prêt",
  order_update: "Demande modifiée",
  report_released: "Rapport publié",
  general: "Information",
}

export function NotificationBell() {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  const canViewCritical = usePermission("critical_notifications", "view")
  const canViewReagents = usePermission("reagents", "view")

  const unreadCountQuery = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => NotificationsService.readMyUnreadCount(),
    refetchInterval: 30_000,
  })

  const notificationsQuery = useQuery({
    queryKey: ["notifications", "mine"],
    queryFn: () =>
      NotificationsService.readMyNotifications({
        limit: 10,
        skip: 0,
      }),
    refetchInterval: 30_000,
  })

  const criticalCountQuery = useQuery({
    queryKey: ["critical-notifications", "unacknowledged-count"],
    queryFn: () => CriticalNotificationsService.readUnacknowledgedCount(),
    enabled: canViewCritical,
    refetchInterval: 30_000,
  })

  const reagentAlertsQuery = useQuery({
    queryKey: ["reagents", "alert-summary"],
    queryFn: () => ReagentsService.readReagentAlertSummary(),
    enabled: canViewReagents,
    refetchInterval: 30_000,
  })

  const invalidateNotifications = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    ])

  const markReadMutation = useMutation({
    mutationFn: (notificationId: string) =>
      NotificationsService.markMyNotificationRead({
        notificationId,
      }),
    onSuccess: invalidateNotifications,
    onError: () =>
      showErrorToast("Impossible de marquer la notification comme lue."),
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => NotificationsService.markAllMyNotificationsRead(),
    onSuccess: invalidateNotifications,
    onError: () =>
      showErrorToast("Impossible de marquer les notifications comme lues."),
  })

  const unreadCount = unreadCountQuery.data?.count ?? 0
  const notifications = notificationsQuery.data?.data ?? []
  const criticalCount = criticalCountQuery.data?.count ?? 0
  const reagentAlertCount = reagentAlertsQuery.data?.total_count ?? 0
  const hasQuickLinks =
    (canViewCritical && criticalCount > 0) ||
    (canViewReagents && reagentAlertCount > 0)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="relative rounded-full"
          aria-label="Notifications"
        >
          <Bell className="size-4" />
          {unreadCount > 0 ? (
            <span className="-top-1 -right-1 absolute flex min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[0.6rem] font-bold text-destructive-foreground leading-4">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-96 max-w-[calc(100vw-2rem)] p-0"
      >
        <div className="flex items-center justify-between gap-3 px-3 py-2.5">
          <div>
            <DropdownMenuLabel className="p-0 font-semibold text-foreground">
              Notifications
            </DropdownMenuLabel>
            <p className="text-[0.7rem] text-muted-foreground">
              {unreadCount > 0
                ? `${unreadCount} non lue${unreadCount > 1 ? "s" : ""}`
                : "Tout est à jour"}
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7"
            disabled={unreadCount === 0 || markAllReadMutation.isPending}
            onClick={() => markAllReadMutation.mutate()}
          >
            {markAllReadMutation.isPending ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <CheckCheck className="size-3" />
            )}
            Tout lire
          </Button>
        </div>

        {hasQuickLinks ? (
          <>
            <DropdownMenuSeparator />
            <div className="space-y-1 px-2 py-2">
              {canViewCritical && criticalCount > 0 ? (
                <DropdownMenuItem asChild>
                  <Link
                    to="/results"
                    className="flex items-center justify-between gap-3"
                  >
                    <span className="flex items-center gap-2">
                      <Microscope className="size-3.5 text-destructive" />
                      Résultats critiques
                    </span>
                    <Badge variant="destructive">{criticalCount}</Badge>
                  </Link>
                </DropdownMenuItem>
              ) : null}
              {canViewReagents && reagentAlertCount > 0 ? (
                <DropdownMenuItem asChild>
                  <Link
                    to="/reagents"
                    className="flex items-center justify-between gap-3"
                  >
                    <span className="flex items-center gap-2">
                      <FlaskConical className="size-3.5 text-warning" />
                      Alertes réactifs
                    </span>
                    <Badge variant="outline">{reagentAlertCount}</Badge>
                  </Link>
                </DropdownMenuItem>
              ) : null}
            </div>
          </>
        ) : null}

        <DropdownMenuSeparator />
        <div className="max-h-96 overflow-y-auto px-2 py-2">
          {notificationsQuery.isLoading ? (
            <div className="flex items-center justify-center gap-2 py-8 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" />
              Chargement des notifications...
            </div>
          ) : notifications.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              Aucune notification.
            </div>
          ) : (
            <div className="space-y-1.5">
              {notifications.map((notification) => (
                <NotificationRow
                  key={notification.id}
                  notification={notification}
                  isMarkingRead={
                    markReadMutation.isPending &&
                    markReadMutation.variables === notification.id
                  }
                  onMarkRead={() => markReadMutation.mutate(notification.id)}
                />
              ))}
            </div>
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function NotificationRow({
  notification,
  isMarkingRead,
  onMarkRead,
}: {
  notification: NotificationPublic
  isMarkingRead: boolean
  onMarkRead: () => void
}) {
  const unread = notification.status === "pending"

  return (
    <div
      className={cn(
        "rounded-md border px-2.5 py-2 text-xs",
        unread
          ? "border-primary/20 bg-primary/6"
          : "border-border bg-background",
      )}
    >
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge variant={unread ? "default" : "outline"}>
              {notificationTypeLabels[notification.type]}
            </Badge>
            <span className="text-[0.65rem] text-muted-foreground">
              {formatDateTime(notification.created_at)}
            </span>
          </div>
          <p className="mt-1 text-foreground leading-relaxed">
            {notification.message}
          </p>
        </div>
        {unread ? (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Marquer comme lue"
            disabled={isMarkingRead}
            onClick={onMarkRead}
          >
            {isMarkingRead ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <Check className="size-3" />
            )}
          </Button>
        ) : null}
      </div>
    </div>
  )
}
