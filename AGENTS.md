Agent instructions
Before work, read PROJECT_STATUS.md, TASKS.md, DECISIONS.md, and ROADMAP.md. Treat docs/architecture/FPO360_CURRENT_ARCHITECTURE_AUDIT.md as historical context; it predates the current Item Catalogue and Inventory work.
Working rules
- Work on the current branch and preserve all staged, unstaged, and untracked user changes.
- Never reset, clean, stash, revert, overwrite unrelated work, commit, or push without explicit authorization.
- Inspect git status and the exact diff before editing. Claim one task in TASKS.md before product-code changes.
- Reuse existing modules and models. FPO360 is a common ERP core with configurable business operations; do not create parallel functionality.
- Production & Packing V1 is accepted for its current scope. Do not reopen routine testing or expand it into full Manufacturing unless a concrete defect or separately approved task requires it.
- The next planned task is a read-only audit of the existing Finance Phase 1 implementation. Revalidate older audit findings against current code; do not assume they remain defects.
- Do not modify business records or create/replay historical stock movements merely to make tests pass. Historical reconciliation requires evidence and explicit authorization.
- Do not apply migrations to a database unless the task explicitly authorizes it and the target is positively identified. Migration 0017 has already been applied to the configured application database; verify the current Alembic revision rather than rerunning or stamping it.
- Report actual test counts, skips, database type, and unverified workflows. A skipped test is not a pass; SQLite does not prove PostgreSQL concurrency.
- Keep changes scoped to a concrete defect. Do not repeat broad audits without a specific reason.
Command execution and permission efficiency
- Routine execution: Batch related read-only inspection commands into a single shell execution. Avoid repeatedly requesting approval for individual routine checks. Reuse collected information instead of re-inspecting. Prefer targeted searches over recursive scans. Use project configuration directly without repeated environment discovery.
- Testing & builds: Group test runs (e.g. backend and frontend test/build passes). Avoid rerunning passing suites unless code edits require it. Use the repository's .venv environment without installing packages or modifying environment configuration without authorization.
- Permission handling: When approval is needed, group commands and describe the purpose clearly. Never bypass, disable, manipulate, or circumvent CLI permission controls.
- Explicit authorization required: Never assume permission for database creation/infrastructure changes, migrations against application databases, destructive Git/file actions (reset/clean/stash/discard/overwrite), commits/pushes, production business data modifications, or external network calls with material side effects.
- Execution pattern: 1) Grouped inspection, 2) Focused implementation/review pass, 3) Grouped verification pass, 4) Concise final report. Do not sacrifice correctness, security, or verification rigor to reduce prompts.
Handoff protocol
1. Read the shared project files before starting.
2. Claim one task in TASKS.md before modifying product code.
3. Inspect current Git status and diffs before editing.
4. After work, update PROJECT_STATUS.md and TASKS.md.
5. Record files changed, verification, blockers, and whether changes remain uncommitted.
6. Continue from the recorded state; do not repeat completed investigations without new evidence.