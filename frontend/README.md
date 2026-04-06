# QChat Frontend

Web client for QChat built with React, TypeScript, and Vite.

## Development

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

## Quality Checks

Run lint checks:

```bash
npm run lint
```

Build for production:

```bash
npm run build
```

Preview production bundle:

```bash
npm run preview
```

## Environment Variables

- `VITE_API_BASE_URL` (default: `/api`)
- `VITE_WS_BASE_URL` (optional; auto-derived from browser location when omitted)

## Notes

- The frontend stores local user keys and cached public keys in IndexedDB.
- Requires Node.js 20.19+ (or 22.12+) for the current Vite version.
