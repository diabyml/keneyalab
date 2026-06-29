import { expect, test } from "@playwright/test"

test.describe("Réactifs", () => {
  test("affiche le module de stock et ses actions principales", async ({
    page,
  }) => {
    await page.goto("/reagents")

    await expect(page.getByRole("heading", { name: "Réactifs" })).toBeVisible()
    await expect(page.getByText("Stock laboratoire")).toBeVisible()
    await expect(page.getByText("Bientôt expirés")).toBeVisible()
    await expect(page.getByText("Stock bas")).toBeVisible()
    await expect(
      page.getByRole("button", { name: "Ajouter un réactif" }),
    ).toBeVisible()
    await expect(page.getByRole("button", { name: "Réglages" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Filtres" })).toBeVisible()
  })
})
