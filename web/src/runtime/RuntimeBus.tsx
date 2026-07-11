import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { websocketUrl } from "../lib/auth";

export type RuntimeFrame<T = unknown> = { type: string; data: T };
export type RuntimeState =
  "connecting" | "connected" | "reconnecting" | "offline";
type Listener = (frame: RuntimeFrame) => void;

interface RuntimeBusValue {
  state: RuntimeState;
  lastFrame: RuntimeFrame | null;
  subscribe(type: string, listener: Listener): () => void;
}

const RuntimeBusContext = createContext<RuntimeBusValue | null>(null);

export function RuntimeBusProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<RuntimeState>("connecting");
  const [lastFrame, setLastFrame] = useState<RuntimeFrame | null>(null);
  const listeners = useRef(new Map<string, Set<Listener>>());

  const subscribe = useCallback((type: string, listener: Listener) => {
    const set = listeners.current.get(type) ?? new Set<Listener>();
    set.add(listener);
    listeners.current.set(type, set);
    return () => {
      set.delete(listener);
      if (!set.size) listeners.current.delete(type);
    };
  }, []);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let timer = 0;
    let ping = 0;
    let attempt = 0;
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      setState(attempt ? "reconnecting" : "connecting");
      socket = new WebSocket(websocketUrl());
      socket.addEventListener("open", () => {
        attempt = 0;
        setState("connected");
        ping = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) socket.send("ping");
        }, 15_000);
      });
      socket.addEventListener("message", (event) => {
        if (typeof event.data !== "string") return;
        try {
          const frame = JSON.parse(event.data) as RuntimeFrame;
          if (!frame || typeof frame.type !== "string") return;
          setLastFrame(frame);
          for (const listener of listeners.current.get(frame.type) ?? [])
            listener(frame);
          for (const listener of listeners.current.get("*") ?? [])
            listener(frame);
        } catch {
          // Ignore malformed or non-protocol frames; the connection remains healthy.
        }
      });
      socket.addEventListener("close", () => {
        window.clearInterval(ping);
        if (disposed) return;
        attempt = Math.min(attempt + 1, 8);
        setState(navigator.onLine ? "reconnecting" : "offline");
        timer = window.setTimeout(
          connect,
          Math.min(12_000, 500 * 2 ** (attempt - 1)),
        );
      });
      socket.addEventListener("error", () => socket?.close());
    };

    connect();
    return () => {
      disposed = true;
      window.clearTimeout(timer);
      window.clearInterval(ping);
      socket?.close();
    };
  }, []);

  const value = useMemo(
    () => ({ state, lastFrame, subscribe }),
    [state, lastFrame, subscribe],
  );
  return (
    <RuntimeBusContext.Provider value={value}>
      {children}
    </RuntimeBusContext.Provider>
  );
}

export function useRuntimeBus(): RuntimeBusValue {
  const value = useContext(RuntimeBusContext);
  if (!value)
    throw new Error("useRuntimeBus must be used inside RuntimeBusProvider");
  return value;
}

export function useRuntimeFrame<T = unknown>(type: string): T | null {
  const { subscribe } = useRuntimeBus();
  const [data, setData] = useState<T | null>(null);
  useEffect(
    () => subscribe(type, (frame) => setData(frame.data as T)),
    [subscribe, type],
  );
  return data;
}
