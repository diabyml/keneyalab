import { expect, test } from "@playwright/test"

test.describe("Tableau de bord", () => {
  test("affiche les sections opérationnelles principales", async ({ page }) => {
    await page.goto("/")

    await expect(
      page.getByRole("heading", { name: "Tableau de bord" }),
    ).toBeVisible()
    await expect(page.getByText("Flux de travail")).toBeVisible()
    await expect(page.getByText("Actions rapides")).toBeVisible()
    await expect(page.getByText("Activité")).toBeVisible()
  })
})
