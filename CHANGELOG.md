# Changelog

## 1.0.0 - 2026-04-06

### Added
- Integrated all active backend, client, tests, CI/CD, and frontend branches into a unified release baseline.
- Added frontend key storage helpers in [frontend/src/lib/keyStore.ts](frontend/src/lib/keyStore.ts).
- Added deterministic message id helper in [frontend/src/lib/messageId.ts](frontend/src/lib/messageId.ts).

### Changed
- Updated frontend package version to 1.0.0 in [frontend/package.json](frontend/package.json).
- Replaced template frontend README with project-specific setup and run instructions in [frontend/README.md](frontend/README.md).
- Fixed import-time database behavior to avoid process exit during test collection in [server/db/database.py](server/db/database.py).
- Aligned and stabilized test fixtures and crypto/service tests for current APIs.
- Fixed malformed quick-start heading in [README.md](README.md).

### Validation
- Python tests: 143 passed.
- Frontend lint: no errors (warnings remain).
- Frontend build: successful production build.
- Docker compose config: valid.

### Known Warnings
- Frontend build warns about Node.js version when below Vite recommended minimum.
- Some pytest warnings remain for test markers and return style.
