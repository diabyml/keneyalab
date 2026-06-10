import { useQuery, type useQueryClient } from "@tanstack/react-query"
import { ApiError, type PermissionPublic, UsersService } from "@/client"

const PERMISSIONS_KEY = ["currentUserPermissions"] as const

/** Pure utility — works anywhere, including route beforeLoad guards. */
export function hasPermission(
  permissions: PermissionPublic[],
  resource: string,
  action: string,
): boolean {
  return permissions.some((p) => p.resource === resource && p.action === action)
}

export function getStoredPermissions(): PermissionPublic[] {
  try {
    const stored = localStorage.getItem("permissions")
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

async function fetchCurrentUserPermissions(): Promise<PermissionPublic[]> {
  const permissions = await UsersService.readUserMePermissions()
  localStorage.setItem("permissions", JSON.stringify(permissions))
  return permissions
}

export async function ensurePermission(
  resource: string,
  action: string,
): Promise<boolean> {
  if (!localStorage.getItem("access_token")) {
    return false
  }
  try {
    const permissions = await fetchCurrentUserPermissions()
    return hasPermission(permissions, resource, action)
  } catch (error) {
    if (error instanceof ApiError && [401, 403].includes(error.status)) {
      if (error.status === 401) {
        localStorage.removeItem("access_token")
        localStorage.removeItem("permissions")
      }
      return false
    }
    throw error
  }
}

/** Put permissions into React Query cache. Called at login + rehydration. */
export function setPermissionsCache(
  queryClient: ReturnType<typeof useQueryClient>,
  permissions: PermissionPublic[],
) {
  queryClient.setQueryData(PERMISSIONS_KEY, permissions)
}

/** React hook — returns the full permissions array from cache. */
export function usePermissions(): PermissionPublic[] {
  const { data: permissions } = useQuery<PermissionPublic[]>({
    queryKey: PERMISSIONS_KEY,
    queryFn: fetchCurrentUserPermissions,
    enabled: localStorage.getItem("access_token") !== null,
    initialData: getStoredPermissions,
  })
  return permissions ?? []
}

/** React hook — checks a specific resource + action against cached permissions. */
export function usePermission(resource: string, action: string): boolean {
  const permissions = usePermissions()
  return hasPermission(permissions, resource, action)
}
