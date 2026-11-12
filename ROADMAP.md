FPO360 product roadmap
Product direction
FPO360 is a common ERP core with configurable business operations. Extend and reuse the existing organization, identity, catalogue, inventory, procurement, sales, finance, and reporting modules rather than duplicating them for each business model.
MVP foundation
The existing MVP includes Dashboard, Users, Farmers, Villages, Shareholders, Item Catalogue/Crop Masters, Farmer Crops, Procurement, Payments, Inventory, Sales, Finance Phase 1, Licenses V1, Reports V1, and Settings.

Historical verification caveats and the separate legacy procurement reconciliation issue are recorded in PROJECT_STATUS.md. Do not infer that every possible browser workflow or business-data scenario has been tested merely because automated tests passed.
Production & Packing V1 — accepted
Production & Packing V1 is implemented using the existing crop_masters catalogue, shared InventoryPostingService, and Sales flow. Migration 0017 has been applied to the configured application database and the observed Alembic revision is 0017 (head). The owner completed the controlled browser workflow and reported that it behaved as expected. Manual demo acceptance is complete.

V1 scope remains deliberately narrow:
- Consume eligible raw inputs and packaging materials.
- Record finished-goods output.
- Record wastage separately; wastage is not an inventory movement in V1.
- Use the shared inventory posting pathway and existing catalogue.
- Make produced finished goods available to the existing Sales flow.
Do not expand this into full manufacturing, production planning, batch genealogy, quality control, by-products, warehouse management, expiry/valuation, or AI/ML without a separately approved task.
Next: Finance Phase 1 audit and stabilisation
Finance Phase 1 already exists. The next phase begins with a read-only audit of the current implementation, schema, migrations, API/services, frontend, and tests.

Audit the following areas against current code and evidence:
1. Financial year lifecycle and locking.
2. Chart of Accounts defaults and protected system accounts.
3. Journal creation, posting, voiding, and database trigger behaviour.
4. General Ledger calculations and fiscal-year boundaries.
5. Trial Balance accuracy and debit/credit balancing.
6. Role-based access and organization isolation.
7. Finance frontend workflows and regression coverage.
Previously reported concerns are not automatically accepted as current defects. Reproduce and document findings first. After review, agree on a prioritised remediation scope before product-code changes.
Separate data-reconciliation issue
Nine legacy procurement records without linked inventory movements remain an independent data-reconciliation issue. Do not recreate or repair historical stock movements automatically. Require physical stock evidence and explicit operator authorization. This issue must not block unrelated module development or the Finance code audit.