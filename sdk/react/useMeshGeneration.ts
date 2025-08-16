// Minimal React hook that wraps the SDK client; uses a tiny type surface to avoid pulling real React types.
import { createMesh, pollUntil } from "../mesh";
import type { Problem } from "../mesh";

type SetStateAction<S> = S | ((prev: S) => S);
type Dispatch<A> = (value: A) => void;

// Tiny subset of React useState/useEffect signatures
declare function useState<S>(initial: S): [S, Dispatch<SetStateAction<S>>];
declare function useEffect(effect: () => void | (() => void), deps?: any[]): void;
declare function useRef<T>(initial: T): { current: T };

export type MeshState =
  | { phase: "idle" }
  | { phase: "submitting" }
  | { phase: "waiting"; statusUrl: string; retryAfterMs: number; laddered?: boolean }
  | { phase: "done"; result: unknown }
  | { phase: "error"; problem: Problem };

export function useMeshGeneration(baseUrl?: string) {
  const [state, setState] = useState<MeshState>({ phase: "idle" });
  const ctrlRef = useRef<AbortController | null>(null);

  useEffect(() => () => {
    ctrlRef.current?.abort();
  }, []);

  async function start(prompt: string) {
    ctrlRef.current?.abort();
    const ctrl = new AbortController();
    ctrlRef.current = ctrl;
    setState({ phase: "submitting" });

    const res = await createMesh(`${baseUrl ?? ""}/api/v1/mesh/generate`, { prompt }, { signal: ctrl.signal });

    if (res.kind === "problem") {
      setState({ phase: "error", problem: res.problem });
      return;
    }

    if (res.kind === "accepted") {
      const retryAfterMs = Math.max(250, Math.floor(res.retryAfter * 1000));
      setState({ phase: "waiting", statusUrl: res.statusUrl, retryAfterMs, laddered: res.laddered });
      const out = await pollUntil(res.statusUrl, { signal: ctrl.signal });
      setState({ phase: "done", result: out.final ?? out });
      return;
    }

    // Fallback: treat anything else as completion
    setState({ phase: "done", result: undefined });
  }

  function cancel() {
    ctrlRef.current?.abort();
  }

  return { state, start, cancel };
}
 
