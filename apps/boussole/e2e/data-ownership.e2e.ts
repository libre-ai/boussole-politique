import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";

const STATEMENT = "stmt-services-publics";

async function answerFirst(page: import("@playwright/test").Page): Promise<void> {
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");
  await page.getByRole("group", { name: STATEMENT }).getByRole("button", { name: "+3" }).click();
  await expect(page.getByTestId("progress")).toContainText("1 / 4");
}

test("exports the response set to a local file with zero transmission", async ({ page }) => {
  const crossOrigin: string[] = [];
  await page.goto("/");
  const origin = new URL(page.url()).origin;
  page.on("request", (r) => {
    const url = r.url();
    // A blob:/data: download is not a network request; only real cross-origin
    // traffic would break the no-transmission invariant.
    if (url.startsWith("blob:") || url.startsWith("data:")) return;
    if (new URL(url).origin !== origin) crossOrigin.push(`${r.method()} ${url}`);
  });

  await answerFirst(page);

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Télécharger mes réponses" }).click(),
  ]);

  expect(download.suggestedFilename()).toBe("boussole-reponses.json");
  const path = await download.path();
  const doc = JSON.parse(await readFile(path, "utf8"));
  expect(doc.schemaVersion).toBe("libre-ai.boussole-response-set.v2");
  expect(doc.responses).toContainEqual({ statementId: STATEMENT, kind: "answer", value: 3 });

  // The export produced a file entirely on-device: no cross-origin request.
  expect(crossOrigin).toEqual([]);
});

test("deletes all responses after in-page confirmation and stays empty on reload", async ({
  page,
}) => {
  await page.goto("/");
  await answerFirst(page);

  await page.getByRole("button", { name: "Supprimer mes réponses" }).click();
  await page.getByRole("button", { name: "Confirmer la suppression" }).click();
  await expect(page.getByTestId("delete-done")).toBeVisible();

  // The emptied set is persisted: a reload restores an empty questionnaire, binding
  // kept (still 4 statements), old answer gone.
  await page.reload();
  await expect(page.getByTestId("progress")).toContainText("0 / 4");
  await expect(page.getByTestId(`state-${STATEMENT}`)).toContainText("Sans réponse");
});

test("cancelling the delete confirmation keeps the responses", async ({ page }) => {
  await page.goto("/");
  await answerFirst(page);

  await page.getByRole("button", { name: "Supprimer mes réponses" }).click();
  await page.getByRole("button", { name: "Annuler" }).click();

  await expect(page.getByTestId("progress")).toContainText("1 / 4");
  await expect(page.getByTestId(`state-${STATEMENT}`)).toContainText("Répondu (3)");
});
