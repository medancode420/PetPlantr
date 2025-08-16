// Minimal React type shim to allow CI type-checks without pulling @types/react.
// Do not publish this file in a package; real apps should depend on @types/react.

declare module "react" {
  export type SetStateAction<S> = S | ((prev: S) => S);
  export type Dispatch<A> = (value: A) => void;

  export function useState<S>(initial: S): [S, Dispatch<SetStateAction<S>>];
  export function useEffect(effect: () => void | (() => void), deps?: any[]): void;
  export function useRef<T>(initial: T): { current: T };
}
declare module 'react' {
  // Minimal surface used by the hook; extend if needed.
  export function useEffect(effect: (...args: any[]) => any, deps?: any[]): void;
  export function useMemo<T>(factory: () => T, deps?: any[]): T;
  export function useState<S>(initial: S | (() => S)): [S, (s: S) => void];
  export type Dispatch<A> = (value: A) => void;
  const React: any;
  export default React;
}
