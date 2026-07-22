import { StatusMessage } from "@libre-ai/ui";
import { useQuestionnaire } from "../client/use-questionnaire";
import type { LocalResponseStore } from "../persistence/local-response-store";
import { QUESTIONNAIRE_STATEMENTS } from "./fixture";
import { Questionnaire } from "./questionnaire";

// The controller's handlers are passed unconditionally (they fold through the
// domain and persist via the optional store), so the server render (no store) and
// the client's first render (store present) produce IDENTICAL markup — event
// handlers are not serialized into HTML, and no other output depends on the store.
// This keeps hydration a byte-for-byte match; interactivity is inert without
// JavaScript because the controls live in `lai-enhanced-only`.
export function QuestionnaireApp({ store }: { readonly store?: LocalResponseStore }) {
  const controller = useQuestionnaire(store);
  return (
    <>
      {controller.status === "corrupt" ? (
        <StatusMessage className="lai-status" data-testid="corrupt-notice">
          Vos réponses locales sont illisibles. Recommencez le questionnaire.
        </StatusMessage>
      ) : null}
      <Questionnaire
        statements={QUESTIONNAIRE_STATEMENTS}
        responses={controller.set.responses}
        onAnswer={controller.answer}
        onSkip={controller.skip}
      />
    </>
  );
}
