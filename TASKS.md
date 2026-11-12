Task queue
Active task: Finance Phase 1 — Read-only implementation audit and remediation plan
Owner: Implementation/review agent
Status: Not started. Begin with a read-only review of the current worktree and Finance implementation. Do not modify product code until findings are documented, the task is claimed, and a focused remediation scope is agreed.
Scope
1. Read AGENTS.md, PROJECT_STATUS.md, DECISIONS.md, ROADMAP.md, and GEMINI.md.
2. Inspect current Git status and exact diffs; preserve all staged, unstaged, and untracked work.
3. Review the existing Finance Phase 1 implementation against current code, schema, migrations, API, services, frontend, and tests.
4. Revalidate previously reported concerns rather than assuming older audit findings are still current.
5. Produce a prioritised findings report with file/line evidence, impact, reproduction or test evidence, and proposed fixes.
6. Do not change product code, run migrations, modify business data, or create databases during the initial audit.
Implemented and accepted: Production & Packing V1
- Organization-scoped production records and input rows reuse the existing crop_masters catalogue.
- Raw-material/agricultural-commodity and packaging consumption plus finished-good output are posted through the shared InventoryPostingService.
- Wastage is recorded separately and does not add inventory or count as finished output in V1.
- Request idempotency, validation, role/tenant checks, history/detail APIs, frontend workflow, and finished-good availability in Sales are implemented.
- PostgreSQL concurrency deadlock in competing production consumption was fixed using with_for_update(key_share=True) (FOR NO KEY UPDATE) for catalogue row locking.
- Migration 0017 was applied to the configured application database after preflight and backup. The application database was observed at Alembic revision 0017 (head).
- The owner completed the controlled browser workflow and reported that the Production & Packing flow behaved as expected. Manual demo acceptance is complete.
- Recorded automated evidence from the implementation/review cycle: disposable PostgreSQL suite 127/127 passed; isolated SQLite suite 104 run, 100 passed, 4 PostgreSQL classes skipped; frontend Node tests 3/3 passed; frontend build passed. These are historical run results, not a claim that tests were rerun during this documentation update.
- Production & Packing V1 is accepted for the current project scope. Do not reopen routine testing unless a concrete defect or new requirement appears.
Separate data-reconciliation issue: legacy procurement movements
Status: Open; requires operator evidence and a separate explicit decision. It does not block Finance code review.

Active legacy procurement records 1–9 were previously identified without linked inventory movements. Their item IDs and canonical KG quantities are documented in PROJECT_STATUS.md. Do not edit these records or post retroactive movements without evidence of stock disposition and explicit authorization.
Handoff checklist
- Read all shared project context files before starting.
- Inspect Git status and exact diffs; preserve all existing work.
- Claim one task before product-code changes.
- Keep the initial Finance audit read-only.
- Update TASKS.md and PROJECT_STATUS.md after work with exact findings, files changed, verification, blockers, and uncommitted state.