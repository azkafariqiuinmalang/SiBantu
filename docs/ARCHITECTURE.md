# Architecture Proposal

## Principles
Monolith modular first, relational DB, pure deterministic decision engine, service-layer authorization/validation, database migrations, unit/integration/E2E tests. Avoid microservice overhead for UAS.

## Default **suggestion only if repo is empty**
- TypeScript app (e.g. Next.js) for web UI and server routes; PostgreSQL relational database; ORM with migrations and constraints; schema validator; test runner.
- Existing repo stack wins if practical and compatible. Record final stack choice in `DECISIONS.md` before implementation.
- Alternative: Laravel + PostgreSQL/MySQL is acceptable; mathematical engine remains independent and tested.

## Modules
```text
web/
  authentication & role-aware navigation
  cases / districts / assignment / reports / verification
  ahp-assessment / individual-results / group-results
server/
  authz / cases / field-report / verification / rounds
  decision-engine/{ahp,topsis,borda} (pure, versioned)
  result-persistence / audit
storage/
  migrations / seed / fixtures
```

## Logical flow
Client form → validated HTTP action → authorized application service → domain constraints → transactionally persist → audit. Decision round reads immutable snapshot → pure engine → persisted trace → role-aware rendering.

## Configuration
ENV secrets, database URL, session/cookie signing, secure cookie and CSRF if cookie auth, safe logging, migration command; add `.env.example` but never commit live secrets.

## Deployment concept
Do not choose Vercel/Railway prematurely. If Next.js + PostgreSQL: frontend/server can be deployed to suitable compatible host and DB as managed service. Deployment only after full local validation. Document exact hosting decision and costs later.
