import { createFileRoute } from "@tanstack/react-router"

import ChangePassword from "@/components/UserSettings/ChangePassword"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"

const tabsConfig = [
  { value: "my-profile", title: "Mon profil", component: UserInformation },
  { value: "password", title: "Mot de passe", component: ChangePassword },
]

export const Route = createFileRoute("/_layout/user-account")({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: "Paramètres - KeneyaLab",
      },
    ],
  }),
})

function UserSettings() {
  const { user: currentUser } = useAuth()
  const finalTabs = tabsConfig

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Paramètres utilisateur
        </h1>
        <p className="text-muted-foreground">
          Gérer les paramètres et préférences de votre compte
        </p>
      </div>

      <Tabs defaultValue="my-profile">
        <TabsList>
          {finalTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {finalTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value}>
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
