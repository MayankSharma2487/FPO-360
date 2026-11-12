FPO360 project status
Latest: Production & Packing V1 accepted; Finance Phase 1 is next
Updated on: 2026-11-03
Branch: feature/finance-phase1 (last reported branch; confirm current branch before repository work)
Status: Production & Packing V1 has passed the owner's controlled browser workflow and is accepted for the current V1 scope. The next task is a read-only audit of the existing Finance Phase 1 implementation.
Production & Packing V1 — implementation and acceptance
- Production records and input rows reuse the existing crop_masters item catalogue; no parallel product master was introduced.
- Production consumes eligible raw inputs and packaging materials and adds finished goods through the shared InventoryPostingService.
- Wastage is stored as a separate measurement in V1; it is not an inventory movement and does not increase finished-goods output.
- Request idempotency, input validation, role/tenant checks, history/detail APIs, frontend workflow, and Sales availability of finished goods are implemented.
- PostgreSQL concurrency deadlock during competing production consumption was fixed by using with_for_update(key_share=True) (FOR NO KEY UPDATE) for the relevant catalogue row locking.
- Migration 0017 was applied to the configured application database after preflight and backup. The observed Alembic revision was 0017 (head). A pre-migration backup was created at D:\fpo360_backups\fpo360_before_0017_20261030_183158.backup; it was readable with pg_restore --list. This was a backup listing check, not a restore test.
- The owner completed the controlled browser workflow and reported that the Production & Packing flow behaved as expected. Manual demo acceptance is complete.
- The owner also confirmed that the agricultural commodity catalogue items can be selected as raw inputs; the service normalizes these to the existing RAW_MATERIAL production-input type to satisfy migration 0017's database constraint. The source catalogue item type is not changed.
- Recorded automated verification from the implementation/review cycle:
  - Disposable PostgreSQL target: 127 run, 127 passed, 0 failed, 0 skipped, including PostgreSQL integration/concurrency and migration tests.
  - With PostgreSQL test URLs unset: 104 run, 100 passed, 0 failed, 4 PostgreSQL test classes skipped. Skipped tests are not passes.
  - Frontend Node tests: 3 passed, 0 failed, 0 skipped.
  - npm run build: passed, with a Vite large-chunk warning.
  - git diff --check: passed in the recorded review run.
  - The focused production unit suite was later run after agricultural commodity support: 10 tests passed. Frontend build also passed after that change.
- These are previously recorded results. They were not rerun as part of this documentation-only update.
Next task: Finance Phase 1 — read-only audit
The existing Finance Phase 1 module is already part of FPO360. The next step is to inspect its current implementation and tests, not to create a replacement finance module.

Previously reported areas requiring revalidation include:
- Financial year lifecycle and locking.
- Chart of Accounts defaults and system-account protections.
- Journal creation, posting, voiding, and database trigger behaviour.
- General Ledger balances and fiscal-year handling.
- Trial Balance correctness and balancing.
- Finance role-based access and tenant isolation.
- Finance frontend workflows and regression coverage.
Treat these as audit questions, not confirmed current defects. Reproduce and verify each finding against the current worktree before recommending changes. The initial audit must be read-only.
Separate legacy procurement reconciliation issue
Earlier local read-only checks identified 11 active procurement records: 2 had matching current IN movements, while records 1–9 had no linked ledger rows or reversals. The nine records' previously recorded canonical quantities were:
- Wheat/item 1: 600 KG (IDs 1–3)
- Moong/item 2: 1,100 KG (IDs 5, 8–9)
- Paddy/item 3: 102 KG (IDs 4, 6)
- Red Gram/item 4: 1,200 KG (ID 7)
Whether this stock remains physically available is unknown. Do not recreate historical movements, edit procurement records, or otherwise reconcile automatically. This remains a separate operator decision and does not block the Finance code audit.
Project boundaries and working state
- FPO360 remains a common ERP core with configurable business operations; extend existing modules rather than duplicating them.
- Preserve all existing staged, unstaged, and untracked work. No commit or push was authorized as part of the Production & Packing work.
- Confirm the current branch, Git status, and exact diffs before further repository changes.
- No Finance code changes, new migrations, database creation, or business-data changes are authorized by the next read-only audit task.