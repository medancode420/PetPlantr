# PetPlantr Mesh SDK (TypeScript)
# PetPlantr SDK (WIP)

Minimal TypeScript helpers for the PetPlantr API.

- Idempotency-Key support
- 202 Accepted laddering with Retry-After and Link header parsing
- RFC7807 Problem+JSON propagation
- Lightweight React hook with abort-on-unmount

Usage (TS/ESM):

```ts
import { createMesh, pollUntil } from './sdk';

const res = await createMesh('/api/v1/mesh/generate', { prompt: 'Corgi planter' });
if (res.kind === 'accepted') {
  const final = await pollUntil(res.statusUrl);
  console.log(final);
}
```

Type-check only (no build):

```sh
npx --yes typescript@5.5.4 --noEmit -p sdk/tsconfig.json
```

Notes:
- Designed for bundlers (moduleResolution: Bundler). For Node-only, consider moduleResolution: nodenext.
- React types are shimmed for CI only; real apps should use @types/react.
Tiny, dependency-free client for `/api/v1/mesh/generate`, plus a React hook.

## Install

No build step required. Copy `sdk/mesh.ts` (and optionally `sdk/react/useMeshGeneration.ts`) into your project.

- Browser: Works out of the box (uses `fetch` and `crypto.getRandomValues`).
- Node: Use Node 18+ for global `fetch`. For older Node, add a fetch polyfill.

## Quick start

```ts
import { createMesh, pollUntil } from './sdk/mesh';

const res = await createMesh('A stylized corgi planter', {
  headers: { Authorization: 'Bearer pk_live_...' }, // if your API requires it
  baseUrl: 'https://api.example.com',               // for SSR/Node
});

if (res.kind === 'accepted') {
  const status = await pollUntil(res.statusUrl, { maxAttempts: 60 });
  console.log('Final status:', status);
} else if (res.kind === 'created') {
  console.log('Created:', res.data);
} else if (res.kind === 'collision') {
  console.warn('Collision:', res.problem);
} else if (res.kind === 'invalid') {
  console.warn('Invalid:', res.problem);
} else {
  console.error('Error:', res.problem);
}
```

## React

```tsx
import { useMeshGeneration } from './sdk/react/useMeshGeneration';

function MeshButton() {
  const { state, result, problem, start, cancel } = useMeshGeneration();

  return (
    <div>
      <button disabled={state !== 'idle'} onClick={() => start('A friendly labrador planter')}>
        Generate planter
      </button>
      {state === 'polling' && <button onClick={cancel}>Cancel</button>}
      <pre>{state}</pre>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
      {problem && <pre style={{ color: 'crimson' }}>{JSON.stringify(problem, null, 2)}</pre>}
    </div>
  );
}
```

## Contract notes

- 202 laddering: The server returns integer Retry-After ∈ [1..120] and the body includes poll_after_s with the same value. A proxy‑aware absolute status_url is included in the body; Location and Link headers match it.
- Idempotency: Provide Idempotency-Key to dedupe requests. Collisions return 409 Problem+JSON.
- Errors: 400/409/422 use application/problem+json, with errors[] for 422.
- CORS: Location, Link, Retry-After, Cache-Control, RateLimit-* are exposed.
