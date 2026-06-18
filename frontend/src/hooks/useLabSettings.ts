import { useQuery } from "@tanstack/react-query"

import { LabSettingsService } from "@/client"

export const LAB_SETTINGS_QUERY_KEY = ["lab-settings"] as const

export function useLabSettings() {
  return useQuery({
    queryKey: LAB_SETTINGS_QUERY_KEY,
    queryFn: () => LabSettingsService.readLabSettings(),
    staleTime: 5 * 60 * 1000,
  })
}
