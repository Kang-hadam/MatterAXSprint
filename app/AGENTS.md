# AGENTS.md

Conventions for agents working in a repository created from `service-template`.
Read this before writing code. The rules here are the ones that have actually
been broken, not a general style guide.

## What this project is

| Part | Stack |
|------|-------|
| `apps/front`, `apps/admin` | **Next.js App Router**, run by [vinext](https://vinext.dev/) on Vite |
| Styling | `@devup-ui/react` + `@devup-ui/reset-css` |
| API client | `@devup-api/fetch`, `@devup-api/react-query` (generated from `openapi.json`) |
| `apis/api` | Rust / Axum (vespera), schemas in `vespertide.json` |
| Package manager | **bun** workspaces (`apps/*`) |
| Lint | `oxlint` + `eslint-plugin-devup` |

## 1. This is a Next App Router project. `vite.config.ts` does not say otherwise.

**`vinext` is a drop-in replacement for the `next` CLI that runs Next.js on
Vite.** So a perfectly normal App Router app here has a `vite.config.ts`, no
`next.config.ts`, and uses `@devup-ui/vite-plugin`. None of that makes it a
Vite SPA.

The evidence is in `apps/front/package.json`:

```jsonc
"scripts": { "dev": "vinext dev", "build": "vinext build", "start": "vinext start" },
"dependencies": { "vinext": "...", "react": "^19" }
```

and in `apps/front/src/app/layout.tsx`, which imports `from 'next'`.

**Therefore:**

- Routing is **file routing** under `src/app/`. One directory per route.
- There is **no `main.tsx` and no `index.html`**. If you are creating one, you
  have misread the project.
- Do not switch screens with local state. This is the single most common way
  this template gets misimplemented:

```tsx
// WRONG - hand-rolled SPA routing
const [screen, setScreen] = useState<Screen>('home')
return screen === 'home' ? <Home /> : <Settings />
```

```tsx
// CORRECT - one route per screen, the framework owns navigation
// src/app/page.tsx, src/app/settings/page.tsx
import Link from 'next/link'
```

## 2. Never author a CSS file

There is no `.css` or `.scss` file in this template and none should be added.
devup-ui extracts styling at build time; a hand-written stylesheet is invisible
to it and competes silently with the generated classes.

| Need | Use |
|------|-----|
| Reset | `resetCss()` — already called in `apps/front/src/app/layout.tsx` |
| Document-level rules (`body`, `*`, `@font-face`) | `globalCss({ ... })` |
| Component styling | Style props on `Box`/`Flex`/`Text`, or `css({ ... })` |
| A runtime value | A style prop — devup-ui emits a CSS variable |

The only acceptable CSS import is a stylesheet **shipped by an installed
package you do not author**, such as an offline webfont package.

Do not invent class names for styling either. `className` is for a `css()`
result, not for a hand-written selector.

## 3. File placement

```
apps/front/src/
├── app/          # ONLY layout.tsx and page.tsx. Nothing else.
├── components/
│   ├── common/   # shared across pages
│   ├── layout/   # Header, Footer, ...
│   └── pages/    # page-specific: pages/<route>/Component.tsx
├── contexts/  hooks/  stores/  utils/
└── api.ts
```

- One component per file. `export default` **only** in `page.tsx`.
- Page components get a descriptive name ending in `Page` (`HomePage`, not
  `Page`) — see the existing `apps/front/src/app/page.tsx`.
- Server Components are the default. Add `'use client'` only when the file
  itself needs `useState`/`useEffect`/`useRouter`, defines an event handler
  internally, or uses `framer-motion`.
- Single-colour SVG icons go to `public/icons/*.svg` and are used with
  `<Image src="/icons/x.svg" />`, not written as React components.

## 4. Theme tokens

`apps/admin` has a `devup.json`; `apps/front` does not yet. When you add one,
the `$token` names in code must come from that file. `$token` only resolves in
a **JSX prop** — in an external object use `var(--token)`.

## 5. Verify before you claim it works

```bash
bun run lint          # oxlint
bun tsc --noEmit      # inside the app you changed
bun test              # bun test
cargo clippy -- -D warnings && cargo fmt --check   # if you touched apis/
```

`bun run build` builds both apps.

Run the dev server from inside the app (`cd apps/front && bun dev`), not with
`bun -F front dev`, which leaves zombie processes.

## 6. Load the skills

The full conventions live in agent skills, not in this file. If your workspace
has none, `devup-mcp` carries them and installs them with no network:

```
devup_skills { "action": "status" }
devup_skills { "action": "install" }
```

| Skill | Covers |
|-------|--------|
| `devfive-frontend` | Structure, Server Components, the rules above in detail |
| `devup-ui` | Style props, responsive arrays, `$token`, what extracts statically |
| `vespera` / `vespertide` | The Rust API and its DB schemas |

This file is the minimum that has to be true even when no skill is loaded.
