import { expect, test } from "@playwright/test";

test("answers persist on-device and are restored on reload, with zero transmission", async ({
  page,
}) => {
  const requests: string[] = [];

  // First navigate to establish the origin
  await page.goto("/");

  // Now set up request interception for cross-origin detection
  const origin = new URL(page.url()).origin;
  page.on("request", (r) => {
    if (new URL(r.url()).origin !== origin) {
      requests.push(`${r.method()} ${r.url()}`);
    }
  });

  // Verify hydration completed
  await expect(page.locator("html")).toHaveAttribute("data-hydrated", "true");

  // Answer the first statement with +3
  await page
    .getByRole("group", { name: "stmt-services-publics" })
    .getByRole("button", { name: "+3" })
    .click();

  // Verify the answer is recorded
  await expect(page.getByTestId("state-stmt-services-publics")).toContainText("Répondu (3)");
  await expect(page.getByTestId("progress")).toContainText("1 / 4");

  // Reload: the answer should be restored from IndexedDB
  await page.reload();
  await expect(page.getByTestId("state-stmt-services-publics")).toContainText("Répondu (3)");

  // Verify no cross-origin request was made (local-only operation)
  expect(requests).toEqual([]);
});
