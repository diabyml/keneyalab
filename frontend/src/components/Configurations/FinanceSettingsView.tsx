import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import type { DiscountAllocationPolicy } from "@/client"
import { FinanceSettingsService } from "@/client"
import {
  decimalToPercentString,
  percentToDecimalString,
} from "@/components/Doctors/utils"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { handleError } from "@/utils"

const SETTINGS_QUERY_KEY = ["finance-settings"] as const

const POLICY_OPTIONS: Array<{
  value: DiscountAllocationPolicy
  label: string
  description: string
}> = [
  {
    value: "non_insured_first",
    label: "Examens non assurés en priorité",
    description:
      "La remise réduit d'abord les examens non couverts, puis les examens assurés si nécessaire.",
  },
  {
    value: "insured_first",
    label: "Examens assurés en priorité",
    description:
      "La remise réduit d'abord les examens couverts, puis les examens non assurés si nécessaire.",
  },
  {
    value: "proportional",
    label: "Répartition proportionnelle",
    description:
      "La remise est répartie selon la part des examens assurés et non assurés dans le total.",
  },
]

export function FinanceSettingsView() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [policy, setPolicy] = useState<DiscountAllocationPolicy | null>(null)
  const [directRate, setDirectRate] = useState("")
  const [insuranceRate, setInsuranceRate] = useState("")
  const settingsQuery = useQuery({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: () => FinanceSettingsService.readFinanceSettings(),
  })

  const savedPolicy =
    settingsQuery.data?.discount_allocation_policy ?? "non_insured_first"
  const savedDirectRate = decimalToPercentString(
    settingsQuery.data?.default_commission_rate,
  )
  const savedInsuranceRate = decimalToPercentString(
    settingsQuery.data?.default_insurance_commission_rate,
  )

  useEffect(() => {
    if (settingsQuery.data) {
      setPolicy(savedPolicy)
      setDirectRate(savedDirectRate)
      setInsuranceRate(savedInsuranceRate)
    }
  }, [savedPolicy, savedDirectRate, savedInsuranceRate, settingsQuery.data])

  const hasChanges =
    policy !== savedPolicy ||
    directRate !== savedDirectRate ||
    insuranceRate !== savedInsuranceRate

  const updateMutation = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = {}
      if (policy !== savedPolicy) {
        body.discount_allocation_policy = policy
      }
      if (directRate !== savedDirectRate) {
        body.default_commission_rate = directRate
          ? percentToDecimalString(directRate)
          : null
      }
      if (insuranceRate !== savedInsuranceRate) {
        body.default_insurance_commission_rate = insuranceRate
          ? percentToDecimalString(insuranceRate)
          : null
      }
      return FinanceSettingsService.updateFinanceSettings({
        requestBody: body as any,
      })
    },
    onSuccess: (settings) => {
      queryClient.setQueryData(SETTINGS_QUERY_KEY, settings)
      showSuccessToast("Paramètres financiers enregistrés")
    },
    onError: handleError.bind(showErrorToast),
  })

  if (settingsQuery.isLoading || policy === null) {
    return (
      <Card className="max-w-3xl">
        <CardHeader>
          <Skeleton className="h-5 w-56" />
          <Skeleton className="h-4 w-full max-w-xl" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }, (_, index) => (
            <Skeleton key={index} className="h-24 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="max-w-3xl">
      <CardHeader>
        <CardTitle className="text-base">
          Répartition des remises pour les commissions
        </CardTitle>
        <CardDescription>
          Ce choix détermine comment une remise globale est répartie entre les
          montants assurés et non assurés avant le calcul des commissions
          médicales.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <RadioGroup
          value={policy}
          onValueChange={(value) =>
            setPolicy(value as DiscountAllocationPolicy)
          }
        >
          {POLICY_OPTIONS.map((option) => (
            <Label
              key={option.value}
              htmlFor={`discount-policy-${option.value}`}
              className={cn(
                "flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors",
                policy === option.value
                  ? "border-primary bg-primary/5"
                  : "hover:bg-muted/40",
              )}
            >
              <RadioGroupItem
                id={`discount-policy-${option.value}`}
                value={option.value}
                className="mt-0.5"
              />
              <span className="space-y-1">
                <span className="block font-medium">{option.label}</span>
                <span className="block text-sm font-normal leading-relaxed text-muted-foreground">
                  {option.description}
                </span>
              </span>
            </Label>
          ))}
        </RadioGroup>

        <div className="space-y-4 border-t pt-6">
          <h3 className="text-sm font-medium">Taux de commission par défaut</h3>
          <p className="text-sm text-muted-foreground">
            Ces taux sont utilisés lorsqu&apos;un médecin n&apos;a pas de
            configuration de commission active. Laissez vide pour ne pas
            appliquer de commission par défaut.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="default-direct-rate">
                Commission directe (%)
              </Label>
              <Input
                id="default-direct-rate"
                type="number"
                min={0}
                max={100}
                step={0.01}
                placeholder="—"
                value={directRate}
                onChange={(e) => setDirectRate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="default-insurance-rate">
                Commission assurance (%)
              </Label>
              <Input
                id="default-insurance-rate"
                type="number"
                min={0}
                max={100}
                step={0.01}
                placeholder="—"
                value={insuranceRate}
                onChange={(e) => setInsuranceRate(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end border-t pt-4">
          <LoadingButton
            loading={updateMutation.isPending}
            disabled={!hasChanges}
            onClick={() => updateMutation.mutate()}
          >
            Enregistrer
          </LoadingButton>
        </div>
      </CardContent>
    </Card>
  )
}
