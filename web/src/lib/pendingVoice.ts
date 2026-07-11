const DATABASE = "holdspeak-voice-recovery";
const STORE = "captures";
const VERSION = 1;
const MAX_BYTES = 16_000_000;

interface PendingVoiceRecord {
  version: 1;
  scope: string;
  audio: ArrayBuffer;
  updatedAt: string;
}

// Tests and privacy-restricted browsers may not expose IndexedDB. The fallback
// retains the capture for this page lifetime; production browsers use the
// durable device-local store below.
const memory = new Map<string, PendingVoiceRecord>();

function openDatabase(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === "undefined") return Promise.resolve(null);
  return new Promise((resolve) => {
    let request: IDBOpenDBRequest;
    try {
      request = indexedDB.open(DATABASE, VERSION);
    } catch {
      resolve(null);
      return;
    }
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE)) {
        request.result.createObjectStore(STORE, { keyPath: "scope" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => resolve(null);
    request.onblocked = () => resolve(null);
  });
}

export async function savePendingVoice(
  scope: string,
  audio: ArrayBuffer,
): Promise<void> {
  const cleanScope = scope.trim();
  if (!cleanScope || !audio.byteLength || audio.byteLength > MAX_BYTES) return;
  const record: PendingVoiceRecord = {
    version: VERSION,
    scope: cleanScope,
    audio: audio.slice(0),
    updatedAt: new Date().toISOString(),
  };
  const database = await openDatabase();
  if (!database) {
    memory.set(cleanScope, record);
    return;
  }
  await new Promise<void>((resolve) => {
    const transaction = database.transaction(STORE, "readwrite");
    transaction.objectStore(STORE).put(record);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => {
      memory.set(cleanScope, record);
      resolve();
    };
    transaction.onabort = () => {
      memory.set(cleanScope, record);
      resolve();
    };
  });
  database.close();
}

export async function loadPendingVoice(
  scope: string,
): Promise<ArrayBuffer | null> {
  const cleanScope = scope.trim();
  if (!cleanScope) return null;
  const database = await openDatabase();
  if (!database) return memory.get(cleanScope)?.audio.slice(0) ?? null;
  const record = await new Promise<PendingVoiceRecord | null>((resolve) => {
    const transaction = database.transaction(STORE, "readonly");
    const request = transaction.objectStore(STORE).get(cleanScope);
    request.onsuccess = () => resolve(request.result ?? null);
    request.onerror = () => resolve(null);
  });
  database.close();
  if (
    record?.version !== VERSION ||
    !(record.audio instanceof ArrayBuffer) ||
    !record.audio.byteLength ||
    record.audio.byteLength > MAX_BYTES
  ) {
    return memory.get(cleanScope)?.audio.slice(0) ?? null;
  }
  return record.audio.slice(0);
}

export async function clearPendingVoice(scope: string): Promise<void> {
  const cleanScope = scope.trim();
  memory.delete(cleanScope);
  const database = await openDatabase();
  if (!database) return;
  await new Promise<void>((resolve) => {
    const transaction = database.transaction(STORE, "readwrite");
    transaction.objectStore(STORE).delete(cleanScope);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => resolve();
    transaction.onabort = () => resolve();
  });
  database.close();
}
