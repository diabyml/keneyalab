import {
  createFileRoute,
  Link,
  Outlet,
  useRouterState,
} from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"

import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/_layout/configurations")({
  component: RouteComponent,
})

function RouteComponent() {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const isIndex =
    pathname === "/configurations" || pathname === "/configurations/"

  return (
    <div className="flex flex-col gap-4">
      {!isIndex && (
        <Button variant="ghost" size="sm" asChild className="w-fit px-0">
          <Link to="/configurations">
            <ArrowLeft className="size-4" />
            Configurations
          </Link>
        </Button>
      )}
      <Outlet />
    </div>
  )
}
