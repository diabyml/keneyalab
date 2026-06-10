import { expect, test } from "@playwright/test"

test.describe("Création de demande", () => {
  test("affiche le workspace de création et le sélecteur catalogue", async ({
    page,
  }) => {
    await page.goto("/orders/new")

    await expect(
      page.getByRole("heading", { name: "Nouvelle demande" }),
    ).toBeVisible()
    await expect(page.getByText("Patient et prescription")).toBeVisible()
    await expect(
      page.getByPlaceholder(
        "Rechercher code ou nom, Entrée pour tout ajouter…",
      ),
    ).toBeVisible()
    await expect(page.getByText("Résumé de la demande")).toBeVisible()
  })
})
