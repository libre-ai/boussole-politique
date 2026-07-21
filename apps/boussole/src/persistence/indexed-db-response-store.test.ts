import { describe, expect, test } from "bun:test";
import { IDBFactory } from "fake-indexeddb";
import { type ResponseSet, recordResponse, startQuestionnaire } from "../domain/response-set";
import { createIndexedDbResponseStore } from "./indexed-db-response-store";

const DB = "boussole-test";
const STORE = "response-set";

function responseSet(answer = 3): ResponseSet {
  const started = startQuestionnaire(
    {
      datasetId: "urn:libre-ai:dataset:d1",
      datasetDigest: "a".repeat(64),
      methodId: "urn:libre-ai:method:m1",
      methodDigest: "b".repeat(64),
    },
    ["stmt-one", "stmt-two"],
  );
  if (!started.ok) throw new Error("fixture start refused");
  const answered = recordResponse(started.value, "stmt-one", answer);
  if (!answered.ok) throw new Error("fixture record refused");
  return answered.value;
}

// Seed a raw record directly, bypassing the domain, to simulate on-disk corruption.
function seedRaw(factory: IDBFactory, raw: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = factory.open(DB, 1);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE)) {
        database.createObjectStore(STORE, { keyPath: "key" });
      }
    };
    request.onsuccess = () => {
      const database = request.result;
      const transaction = database.transaction(STORE, "readwrite");
      transaction.objectStore(STORE).put({ key: "current", raw });
      transaction.oncomplete = () => {
        database.close();
        resolve();
      };
      transaction.onerror = () => {
        database.close();
        reject(transaction.error ?? new Error("seed failed"));
      };
    };
    request.onerror = () => reject(request.error ?? new Error("seed open failed"));
  });
}

describe("IndexedDB response store — round-trip on fake-indexeddb", () => {
  test("saves and loads the response set", async () => {
    const store = createIndexedDbResponseStore(new IDBFactory(), DB);
    const original = responseSet();
    await store.save(original);
    const result = await store.load();
    expect(result.status).toBe("loaded");
    if (result.status !== "loaded") return;
    expect(result.set).toEqual(original);
  });

  test("a fresh store is empty", async () => {
    const store = createIndexedDbResponseStore(new IDBFactory(), DB);
    expect(await store.load()).toEqual({ status: "empty" });
  });

  test("re-save overwrites the single set", async () => {
    const store = createIndexedDbResponseStore(new IDBFactory(), DB);
    await store.save(responseSet(3));
    await store.save(responseSet(-2));
    const result = await store.load();
    expect(result.status).toBe("loaded");
    if (result.status !== "loaded") return;
    const answer = result.set.responses.find((r) => r.statementId === "stmt-one");
    expect(answer).toEqual({ statementId: "stmt-one", kind: "answer", value: -2 });
  });

  test("clear empties the store", async () => {
    const store = createIndexedDbResponseStore(new IDBFactory(), DB);
    await store.save(responseSet());
    await store.clear();
    expect(await store.load()).toEqual({ status: "empty" });
  });

  test("a corrupt stored record surfaces as corrupt, not a rehydrated set", async () => {
    const factory = new IDBFactory();
    await seedRaw(factory, "{ not valid json");
    const store = createIndexedDbResponseStore(factory, DB);
    expect(await store.load()).toEqual({
      status: "corrupt",
      refusal: "boussole.local_state_corrupt",
    });
  });

  test("save rejects when the factory cannot open", async () => {
    const broken = {
      open: () => {
        throw new Error("no indexeddb");
      },
    } as unknown as IDBFactory;
    const store = createIndexedDbResponseStore(broken, DB);
    await expect(store.save(responseSet())).rejects.toThrow();
  });
});
