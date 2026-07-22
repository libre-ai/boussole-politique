import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { QuestionnaireApp } from "./questionnaire-app";

describe("QuestionnaireApp — SSR baseline", () => {
  test("renders the empty questionnaire with no store (server render)", () => {
    const html = renderToStaticMarkup(<QuestionnaireApp />);
    expect(html).toContain("0 / 4 répondu(s).");
    expect(html).not.toContain("corrupt-notice");
    expect(html).not.toContain("style=");
  });
});
