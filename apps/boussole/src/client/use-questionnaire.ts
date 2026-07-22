import { useEffect, useState } from "react";
import {
  deleteResponses,
  type ExportedResponseSet,
  exportResponseSet,
  type ResponseSet,
  recordResponse,
  skipStatement,
  startQuestionnaire,
} from "../domain/response-set";
import type { LocalResponseStore } from "../persistence/local-response-store";
import { QUESTIONNAIRE_BINDING, QUESTIONNAIRE_STATEMENTS } from "../ui/fixture";

function emptySet(): ResponseSet {
  const started = startQuestionnaire(QUESTIONNAIRE_BINDING, QUESTIONNAIRE_STATEMENTS);
  if (!started.ok) throw new Error("boussole.fixture_invalid");
  return started.value;
}

export type QuestionnaireStatus = "loading" | "ready" | "corrupt";

export interface QuestionnaireController {
  readonly set: ResponseSet;
  readonly status: QuestionnaireStatus;
  readonly answer: (statementId: string, value: number) => void;
  readonly skip: (statementId: string) => void;
  // Data-ownership: `exportData` returns the current responses as a non-identifying
  // export document (null when empty, mirroring the domain's empty-refusal); the
  // caller turns it into a LOCAL file download — never a network upload. `deleteAll`
  // erases every response through the domain and persists the emptied set (binding
  // kept); it resolves only once the store has durably saved, so the caller can
  // truthfully announce deletion (unlike the optimistic answer/skip saves, a
  // deletion claim must be durable).
  readonly exportData: () => ExportedResponseSet | null;
  readonly deleteAll: () => Promise<void>;
}

// The interactive controller. Without a store (SSR) it stays at the empty set with
// status "ready" (the SSR baseline). With a store, the initial status is "loading"
// until the mount effect loads the persisted set; it then persists every mutation.
// A corrupt local store is surfaced fail-closed (never rehydrated).
export function useQuestionnaire(store?: LocalResponseStore): QuestionnaireController {
  const [set, setSet] = useState<ResponseSet>(emptySet);
  const [status, setStatus] = useState<QuestionnaireStatus>(store ? "loading" : "ready");

  useEffect(() => {
    if (!store) return;
    let cancelled = false;
    store.load().then((result) => {
      if (cancelled) return;
      if (result.status === "loaded") setSet(result.set);
      setStatus(result.status === "corrupt" ? "corrupt" : "ready");
    });
    return () => {
      cancelled = true;
    };
  }, [store]);

  function commit(next: ResponseSet): void {
    setSet(next);
    void store?.save(next);
  }

  return {
    set,
    status,
    answer(statementId, value) {
      const next = recordResponse(set, statementId, value);
      if (next.ok) commit(next.value);
    },
    skip(statementId) {
      const next = skipStatement(set, statementId);
      if (next.ok) commit(next.value);
    },
    exportData() {
      const result = exportResponseSet(set);
      return result.ok ? result.value : null;
    },
    async deleteAll() {
      // Persist first, mutate UI state after: if the save rejects, the visible
      // state must keep matching the (unchanged) store — never show an emptied
      // questionnaire whose old answers would come back on reload.
      const next = deleteResponses(set);
      await store?.save(next);
      setSet(next);
    },
  };
}
