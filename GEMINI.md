Google Antigravity / Gemini handoff
Use the shared repository context as the source of truth. Before acting, read:
1. AGENTS.md for repository rules and handoff protocol.
2. PROJECT_STATUS.md for verified state and evidence boundaries.
3. TASKS.md for the single active task and next action.
4. DECISIONS.md and ROADMAP.md for settled architecture and scope.
Production & Packing V1 is accepted for its current scope. Migration 0017 has been applied to the configured application database (observed revision 0017 (head)), and the owner completed the controlled browser workflow. Do not repeat routine acceptance testing unless a concrete defect or new requirement appears.

The active next task is a read-only audit of the existing Finance Phase 1 implementation. Revalidate previously reported concerns against the current worktree and code; do not assume old findings are still defects. Do not change product code until the audit findings and a focused remediation scope are agreed.

Inspect the current Git worktree and exact diff, preserve every pending change, claim one task before code edits, and update shared status/task files when finished. Follow AGENTS.md command execution and permission efficiency rules (batching routine commands, avoiding repetitive scans, grouping verification passes). Do not alter business records or post historical inventory movements without explicit authorization. Report exact tests and skips; distinguish SQLite from PostgreSQL validation.