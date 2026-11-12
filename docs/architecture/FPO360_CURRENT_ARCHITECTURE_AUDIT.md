# FPO360 Current Architecture and Business Capability Audit

**Audit basis:** source files in the current checkout, migration scripts, and test source. This is a read-only audit; no migrations, application changes, test runs, or runtime database inspection were performed. A named test is evidence of intended/covered behavior, not proof that it passed in this checkout.

## Executive summary

- Frontend: React 18, TypeScript, Vite, React Router 6. Pages are under `frontend/src/pages`; routes live in `frontend/src/App.tsx`.
- Frontend HTTP calls use one Axios client in `frontend/src/services/api.ts`, with JSON defaults, a local-storage bearer token, and redirect on 401. Domain wrappers live in `frontend/src/services/*Service.ts`.
- Authentication uses `/auth/login` and `/auth/me`; `AuthContext` restores the JWT from `localStorage` and user profile. `ProtectedRoute`, `RoleGuard`, and sidebar filtering gate the UI.
- Backend: FastAPI, Pydantic schemas, SQLAlchemy ORM, PostgreSQL-oriented Alembic migrations. Routers are mounted centrally in `backend/app/main.py`.
- Backend layers exist, but are not uniform: many domains use API → service → repository; payments use route-level SQLAlchemy logic; finance is split into setup/year/account/journal/report services and repositories.
- Migration files form a single visible chain `0001` through `0013`; current source head is `0013` (`0013_add_licenses.py`), not independently verified against any database.
- Core records are mostly `organization_id` scoped. Super Admin has cross-organization read paths in selected services; enforcement is per endpoint/service and inconsistent in some master/settings flows.
- Roles are name-based (`Super Admin`, `FPO Admin`, `Manager`, `Accountant`, `Viewer`); `RolePermission` exists but endpoint authorization uses `require_roles`, not permission records.
- Farmers, villages, shareholder registry, crop master, farmer crop records, procurement, farmer payments, crop inventory, simple sales/customers, finance journals, licenses, and operational reports have implemented code paths.
- Procurement atomically creates an inventory IN row; sales atomically create an OUT row after a stock check. Neither transaction creates finance journals.
- Crop master is doing double duty as crop/commodity and saleable stock item. No separate product, raw material, packaging material, supplier, BOM, production, warehouse, batch, or expiry model is present in the inspected model/migration inventory.
- Settings has backend organization settings endpoints/model but the frontend Settings route is a `ComingSoon` placeholder; organization settings API is not wired to a settings page.
- Reports has React UI, backend endpoints/services/repository and `backend/tests/test_reports.py`; full local browser/API/database E2E verification is not established by the repository evidence.
- Git branch: `feature/finance-phase1`; working tree was clean at audit start (`git status --porcelain=v1 --untracked-files=all` returned no entries). The audit report is the only file this task adds.

## 1. Current architecture

### Frontend, routing, API and authentication

`frontend/package.json` identifies React 18, TypeScript, Vite and React Router 6. `frontend/src/main.tsx` mounts `App`; `App.tsx` declares public `/login`, protected nested application routes, and a catch-all redirect. `MainLayout` supplies the common shell. Routes map to page components; Settings, Roles and Permissions render `ComingSoon` in `App.tsx`.

`frontend/src/services/api.ts` exports a shared Axios client with base URL `/api`. Its request interceptor reads `fpo360_token` from browser local storage and adds `Authorization: Bearer …`; its response interceptor clears that token and navigates to `/login` on HTTP 401. Domain service modules wrap API calls, for example `procurementService.ts`, `inventoryService.ts`, `salesService.ts`, `financeService.ts`, and `reportsService.ts`. Some older wrappers use `any`, while finance/report/license wrappers define more specific types.

`AuthContext.tsx` restores a token through `authService.getMe()`, holds user/token/loading state, and implements login/logout. `ProtectedRoute.tsx` gates authenticated pages; `RoleGuard.tsx` gates pages by role name. `RoleBasedSidebar.tsx` independently filters links by role. These frontend checks improve navigation but are not a security boundary; backend dependencies must enforce access.

### Backend, domain layering and persistence

`backend/app/main.py` constructs FastAPI and mounts auth, organizations/settings, roles/users, dashboard, villages/masters, farmers/shareholders/crops, procurement/payments, inventory, customers/sales, finance, licenses and reports routers. API files live in `backend/app/api`, except `backend/app/routers/payment.py`.

Common CRUD domains follow API → service → repository → SQLAlchemy model, with Pydantic schemas in `backend/app/schemas`. Examples include `FarmerService`/`FarmerRepository`, `ProcurementService`/`ProcurementRepository`, `SaleService`/`SaleRepository`, and `ReportsService`/`ReportsRepository`. Payments are an exception: `routers/payment.py` contains relation validation, queries, create/update/status behavior and commit operations directly in route handlers. Finance's `FinanceService` is a compatibility facade over specialized services.

`backend/app/database/database.py` creates the SQLAlchemy engine from `DATABASE_URL` and session dependency `get_db`; this report does not disclose environment values. `backend/migrations/env.py`, `backend/alembic.ini`, and `backend/migrations/versions` establish Alembic. Migration revision chain in files: `0001` initial schema → `0002` villages → `0003` locations → `0004` farmers → `0005` shareholders → `0006` crop tables → `0007` procurement → `0008` payments → `0009` inventory ledger → `0010` customers/sales → `0011` financial years/accounts → `0012` journals → `0013` licenses. `0013` is the source head. No live database revision was queried.

### Organization scoping, roles and permissions

`User` has required `organization_id` and `role_id`; operational models generally carry `organization_id`. `get_current_user` in `backend/app/auth/dependencies.py` validates JWT, reloads the user and rejects inactive users. `require_roles(*allowed_roles)` checks the role's name. The seeded role set is represented by `backend/app/database/seed.py` and `backend/scripts/seed_roles.py` (not a granular permission engine).

Organization restrictions are frequently explicit in service/repository filters (e.g., procurement list, payment validation, inventory balances, sales and finance). Super Admin bypasses scope in selected list/get paths. Important caveats: crop masters are globally shared (`CropMaster` has no `organization_id`) and its endpoints authorize role names but do not scope by org; the organization settings GET accepts an arbitrary organization ID and uses only `get_current_user`, and its service does not compare that ID with the caller's organization. Settings PUT role-checks but also does not perform organization ownership validation in the shown service. `User` has a global unique email; farmer/shareholder/village codes also use global uniqueness in their model definitions. These choices constrain tenant-local naming and should be reviewed before broader multi-FPO onboarding.

`RolePermission` and permission schema/API concepts exist in source, but frontend `/roles` and `/permissions` are placeholders and endpoint guards use role names, not permission assignments. Therefore dynamic, configurable permission behavior is not established.

### Module interactions

- Organization → users, villages, farmers, shareholders, farmer crops, procurements, customers, sales, inventory, settings, finance years/accounts/journals, licenses.
- Farmer → optional village, optional one-to-one shareholder, farmer crop rows, procurement and payment party.
- Shared CropMaster → farmer crop, procurement, inventory ledger and sales. This is the common item key but only models a crop-like commodity.
- Procurement → farmer and crop; create also writes an inventory IN ledger row.
- Payment → farmer and procurement; no finance journal side effect.
- Sale → customer and crop; create also writes inventory OUT ledger row.
- Inventory ledger → organization and crop; source reference is polymorphic text/id, not a foreign key to its source.
- Finance journal lines → organization-owned account and organization-owned journal, with optional farmer/customer party identifiers. Source type permits only `MANUAL`/`OPENING`, and `source_id` is constrained to NULL; operational documents are not automatically linked.
- Reports aggregate operational records and finance journals; reports do not constitute a separate transactional source of truth.

### Testing evidence

Backend tests are `unittest` files under `backend/tests`: `test_finance_phase1.py`, `test_finance_postgres_lifecycle.py`, `test_licenses.py`, and `test_reports.py`. Finance foundation tests include schema/migration-source assertions; PostgreSQL journal lifecycle tests explicitly skip without a configured test DB. Reports/license tests construct in-memory SQLite databases and exercise service/API-level behaviors. No frontend test script or frontend test files appear in `frontend/package.json`/file inventory. No tests were run for this audit. Test presence does not establish a passing state.

## 2. Module inventory

Status meanings: **implemented** = meaningful backend workflow and UI path; **partially implemented** = functional subset with important workflow gaps; **UI-only** = screen/placeholder without usable module API; **not implemented** = no substantive capability found. Testing column describes source evidence only.

| Module | Frontend | API / service / persistence | Workflows, access and limitations | Evidence and status |
|---|---|---|---|---|
| Dashboard | `pages/Dashboard.tsx`, `dashboards/*Dashboard.tsx`, `DashboardRouter.tsx`, `DashboardCards.tsx` | `/dashboard*`; `DashboardService`; aggregates repositories; no dedicated dashboard table | Role-specific summary views. Some counts/summaries are operational aggregates. API has role dependencies; org IDs passed in selected role-specific service paths. | `backend/app/api/dashboard.py`, `services/dashboard_service.py`, `schemas/dashboard.py`; no dedicated dashboard tests found. **Partially implemented** |
| Users and roles | `pages/Users.tsx`, `UserForm`, `UserRoleSelector`, `UserStatusToggle`; Roles/Permissions are `ComingSoon` | `/users` CRUD/status/role/reset; `/roles` API and models `User`, `Role`, `RolePermission` | User list/create/update/status/reset/assign role. FPO admin list is org-filtered; service checks scope. Role assignment is fixed role-name guard; no UI for role/permission administration. | `api/users.py`, `services/user_service.py`, `repositories/user_repository.py`, `models/user.py`, `role.py`, `role_permission.py`. Tests not found. **Partially implemented** |
| Farmers | `pages/Farmers.tsx`, `FarmerForm`, actions menu | `/farmers`; `FarmerService`/repository; `farmers` table | CRUD, active toggle, village/shareholder references, identity/contact/land fields. Org-scoped; Super Admin has broader access. Sensitive personal identifiers are stored. | `api/farmers.py`, `models/farmer.py`; no focused tests found. **Implemented** for registry scope |
| Villages | `pages/Villages.tsx`, `VillageForm`, actions menu | `/villages`; service/repository; `villages` | CRUD/status, location text fields, org relation; service scopes ordinary users. No normalized village/block/district foreign key in `Village`. | `api/villages.py`, `models/village.py`; no focused tests found. **Implemented** for registry scope |
| Shareholders | `pages/Shareholders.tsx`, form/actions | `/shareholders`; service/repository; `shareholders` | Farmer-linked share count/value/capital/certificate and active status. Unique one-to-one farmer constraint. No capital receipt/accounting workflow. | `api/shareholders.py`, `services/shareholder_service.py`, `models/shareholder.py`; no focused tests found. **Partially implemented** |
| Crop Masters | `pages/CropMasters.tsx`, form/actions | `/crop-masters`; service/repository; `crop_masters` | Shared create/list/update/active toggle, code/name/category/unit. It is globally shared and reused as stock/sale item; not a separate tenant item catalogue. | `api/crop_masters.py`, `models/crop_master.py`; no focused tests found. **Partially implemented** |
| Farmer Crops | `pages/FarmerCrops.tsx`, `FarmerCropForm` | `/farmer-crops`; service/repository; `farmer_crops` | Farmer-crop-season/year, acreage, sow/harvest dates, expected/actual yield, status. Relates to crop and farmer. Role gated; service validates associations. Not actual yield procurement reconciliation. | `api/farmer_crops.py`, `services/farmer_crop_service.py`, `models/farmer_crop.py`; no focused tests found. **Implemented** for crop planning/record scope |
| Procurement | `pages/Procurements.tsx`, detail/receipt/form/actions | `/procurements`; service/repository; `procurements` | Farmer commodity purchase, quantity/unit/rate/total/grade/remarks; creates linked inventory IN atomically. No supplier purchase-order or receiving state. Edit updates procurement fields without synchronizing linked inventory quantity/crop/activity; deactivation also leaves ledger active. | `services/procurement_service.py`, `models/procurement.py`; no procurement-specific test file found. **Partially implemented** |
| Payments | `pages/Payments.tsx`, detail/receipt/form | `/payments`; route-level DB implementation; `payments` | One active payment per procurement; amount positive and <= procurement total; farmer/procurement must match current org. Edit and active toggle supported. No partial-payment accumulation check, customer receipt, journal, or status-to-accounting posting. Route uses only `get_current_user`, no explicit role dependency. | `backend/app/routers/payment.py`, `models/payment.py`; no focused payment tests found. **Partially implemented** |
| Inventory | `pages/Inventory.tsx`, `InventoryLedger.tsx` | `/inventory/balances`, `/{crop_id}/ledger`, `/adjust`; `InventoryService`/repository; `inventory_ledger` | Active IN/OUT sum by org+crop, manual adjustment, OUT stock check; procurement/sale movement integration. Quantity-only, fixed KG assumptions. No valuation, warehouse records, batches, expiry, reservations or transfer. | `models/inventory.py`, `services/inventory_service.py`; reports tests seed movements but dedicated mutation behavior tests not found. **Partially implemented** |
| Sales | `pages/Sales.tsx`, `SaleForm`, customer form | `/customers`, `/sales`; customer/sale services/repositories; `customers`, `sales` | Customer registry and single-crop-per-sale transaction; stock check and OUT movement; `Pending`/`Paid` enum only. No invoice document lifecycle, line items, tax, receipts, returns or customer balance ledger. | `api/sales.py`, `services/sale_service.py`, `models/sale.py`; no focused sales lifecycle tests found. **Partially implemented** |
| Finance | Finance dashboard, years, accounts, journals, GL, trial balance pages | `/finance/setup`, `/years`, `/accounts`, `/journals`, `/reports/*`; specialized services/repos; financial years, accounts, journal entries/lines | Org-specific chart/year; double-entry journals, date/lock/account/party validation, posting and voiding. No automatic operational postings; manual/opening source only. | `services/journal_service.py`, `models/journal.py`, migrations `0011`–`0012`; finance tests exist (including DB-dependent trigger tests) but not run. **Partially implemented** (ledger foundation, not integrated ERP accounting) |
| Licenses | `pages/Licenses.tsx`, `LicenseForm` | `/licenses`; `LicenseService`/repository; `licenses` | Organization registry, dates, status, activate/deactivate, expiry display and validation. Role access in API; organization-scoped in service. No document upload/storage beyond reference field. | `api/licenses.py`, `models/license.py`, `test_licenses.py`; test file contains service-level cases. **Implemented** for registry scope |
| Reports | `pages/Reports.tsx` | `/reports/{farmers,procurement,payments,inventory,sales}`, finance summary, licenses; service/repository; reads domain tables | Filters, summaries, pagination and CSV export. Scoped through report service org. Pagination/export and filter behavior have backend test source. Client uses `Promise.allSettled` for filter options. No E2E evidence; export route and UI integration not confirmed at runtime. | `api/reports.py`, `services/reports_service.py`, `repositories/reports_repository.py`, `test_reports.py`. **Partially implemented** |
| Settings | `App.tsx` renders `ComingSoon`; no settings frontend service/page | `/organizations/{id}/settings` GET/PUT; `OrganizationSettingsService`; `organization_settings` | Backend profile fields (logo URL, address, phone, email, website); auth/scoping concern: GET is any authenticated user; service does not check caller org; PUT role-checks but service also lacks org ownership check. | `api/organization_settings.py`, `models/organization_settings.py`; no focused tests found. **UI-only** as a user-facing module (backend subset exists) |

## 3. Product, purchasing, inventory and sales architecture

### What records represent

- **Product/item/material master:** no distinct Product, Item, Material or SKU model/schema/API/page found in the repository inventory. `CropMaster` (`crop_masters`) holds `crop_code`, `crop_name`, category, unit and active flag. It has no organization ID, product type, brand, tax, pack size or inventory policy. It is shared globally.
- **Commodity/crop:** `CropMaster` is referenced by `FarmerCrop`, `Procurement`, `InventoryLedger` and `Sale`. It is therefore the sole shared stock identity in those workflows.
- **Purchase/procurement:** `Procurement` has farmer, crop, org, date, quantity, unit, rate, total, grade and notes. Optional `warehouse_id`, `lot_number`, `vehicle_number`, `receipt_no` are string columns only; service create/update does not populate them, and there is no warehouse/lot table or traceability workflow.
- **Supplier/vendor:** no supplier/vendor model or supplier purchase flow. Farmers are the only procurement counterparty.
- **Inventory:** `InventoryLedger` records positive quantity plus IN/OUT, org, crop, reference type/id, remarks and active flag. Balances are computed from active rows. There is no stored stock balance, unit cost, valuation method, warehouse/location, batch/expiry, or material category.
- **Sales/customer/invoice:** `Customer` and `Sale` exist. One Sale is exactly one crop, one customer and one quantity/rate/total; it is not an invoice with line children. There is no tax/invoice numbering beyond `sale_no`, receivable ledger, due date, or receipt allocation.
- **Returns and adjustments:** manual inventory IN/OUT adjustment exists. No sale-return or purchase-return model/workflow. Status toggling is used for procurement/sale/payment and can affect reports/accounting consistency.
- **Payments/receivables/payables:** `Payment` is linked to one farmer and procurement. It is an operational farmer payment, not a generic cash transaction. Sale has only `payment_status`; no customer receipt entity. No balance allocation across multiple bills.
- **Finance:** organization chart of accounts, financial years and posted journals exist. `JournalEntry.source_type` is constrained to MANUAL/OPENING and `source_id` is constrained NULL in model/migration. `JournalService` creates balanced journals and voids eligible manual/opening entries. Procurement, payment, sale and stock code do not invoke it.
- **Units:** Procurement and Sale store physical quantity in KG after converting entered KG/QUINTAL/TON. Rates and totals use user-entered quantity/unit. `CropMaster.unit` is descriptive and not connected to conversion rules. Inventory adjustment schema is KG quantity. No generic UOM table or conversion engine exists.

### Answers to required questions

1. **Buy finished supplier products and resell?** Not as a supplier workflow or distinct SKU. The system can represent a crop-like item, procure it from a farmer, then sell it to a customer and decrement stock. `ProcurementService.create_procurement` requires a farmer and `SaleService.create_sale` requires a customer and crop (`services/procurement_service.py`, `services/sale_service.py`). Third-party supplier and brand identity are absent.
2. **Bulk tea + packaging stock → packaged product?** No. Each movement is keyed to one `crop_id`; there is no packaging material item, consumption/output transaction, conversion/BOM, or distinct product transformation. Existing manual adjustment cannot correctly model linked consumption and production.
3. **Production batch with multiple inputs, finished goods, by-products, wastage?** No production order/batch, BOM, issue, output, by-product or wastage model/service/API exists. `InventoryLedger` only allows a single crop per movement.
4. **Same product purchased, stocked, sold consistently?** Within the current crop-like use case, yes: all three models refer to `crop_id` and the sale stock check reads inventory balance. It is not a general product identity across supplier purchases, packaging and manufactured products; `CropMaster.unit` and persisted KG quantity also differ in meaning.
5. **Does procurement update Inventory? Conditions?** Yes, on successful `create_procurement`: `ProcurementService` flushes the procurement, inserts one active `IN` row with same org/crop/quantity, then commits both or rolls back. It only accepts active same-org farmer and active crop and positive quantity/rate. Update and active toggle do not update/deactivate linked ledger. This makes existing edits/deactivation capable of leaving stock inconsistent.
6. **Does Sales update Inventory and Finance? Conditions?** Sales create checks active available crop stock, converts unit to KG, validates customer/crop/amount/payment status, then creates Sale and OUT ledger in one transaction. Update adjusts an active sale's linked ledger for quantity/unit/crop changes; deactivation toggles ledger off and reactivation checks stock and reactivates/recreates movement. It has no finance journal integration. (`SaleService`).
7. **Quantities, rates, costs and corrections?** Procurement/Sale quantity convert KG=1, QUINTAL=100kg, TON=1000kg. Total equals entered quantity × rate, with rate/total numeric decimal but stored physical quantity Float. Inventory movement quantity is Float and positive magnitude. There is no inventory cost/valuation. Procurement update recalculates total but does not update ledger; it can also recalculate total from stored KG as if user-entered quantity when rate changes without quantity/unit. Sale update has explicit unit-change safety and updates ledger when active, but rate-only update converts stored KG back by unit. No immutable correction/credit-note workflow; status changes can be used to deactivate.
8. **Edit/deactivate/cancel/void behavior?** Procurement edits change business fields without adjusting ledger; status toggle only changes procurement `is_active`, not ledger. Payment edits mutate payment data; status toggle only changes its active flag; neither reverses a journal because none is posted. Sales edits update linked active stock ledger for stock-affecting changes; active toggle mirrors sale active state to ledger and reactivation checks available stock. No cancellation/void event history. Journal void is separate and limited to manual/opening entries, requires reason and unlocked year.
9. **Which operations journal?** Only explicitly created Finance journals (manual/opening) enter finance. Journal validation enforces at least two balanced lines, active org accounts, current org parties and unlocked in-range FY; posted journals can be voided under rules. Procurements, farmer payments, sales and inventory adjustments remain operational-only. The report finance summary reads posted journals, not these operational records.
10. **What is missing for manufacturing/packing/resale?** Generic org-scoped products/SKUs, supplier records and purchase receipts, multi-line documents, warehouse/bin/location, UOM conversions, lots/expiry, stock valuation, purchase/sales returns, stock reservations, BOM/recipe, production orders/batches, multi-input consumption, yield/output, by-products/waste, finished-good receipt, cost roll-up, traceability, customer receipts and supplier/customer subledgers, and automatic finance posting/reversal integration.

## 4. Business-model capability matrix

Legend: **Supported** means the described basic workflow exists; **Partially Supported** means an adjacent workflow exists but not enough for a reliable model; **Not Supported** means no corresponding workflow found. For this table, product setup refers to setting up the appropriate products/inputs for that business model, not merely adding a crop name.

| Capability | A. Agricultural procurement/trading | B. Third-party branded resale | C. Private-label packing/repacking | D. Biofertilizer/manufacturing | E. Agricultural processing/value addition | F. Input supply (seeds/fertilizer) |
|---|---|---|---|---|---|---|
| Product setup | Partially Supported | Partially Supported | Not Supported | Not Supported | Not Supported | Partially Supported |
| Purchase of inputs/finished goods | Supported (farmer produce) | Not Supported (no supplier) | Partially Supported (farmers only) | Partially Supported (farmer raw produce only) | Partially Supported (farmer raw produce only) | Not Supported (supplier buying absent) |
| Stock receipt and issue | Supported (crop ledger) | Partially Supported (crop ledger, no supplier/SKU) | Not Supported for separate material/FG | Not Supported for production inputs/outputs | Not Supported for transformed stocks | Partially Supported (commodity ledger only) |
| Production/packing transformation | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported |
| Batch/lot traceability | Partially Supported (procurement lot string unused by workflow) | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported |
| Wastage/by-product tracking | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported |
| Cost calculation | Partially Supported (procurement total/rate only; no stock valuation) | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported |
| Sales | Supported (single crop/customer sale) | Partially Supported (crop sale only) | Not Supported for packaged SKU | Not Supported for manufactured FG | Not Supported for processed FG | Partially Supported (crop sale only) |
| Customer receivables | Partially Supported (`Pending`/`Paid` label only) | Partially Supported | Not Supported | Not Supported | Not Supported | Partially Supported |
| Supplier/farmer payments | Partially Supported (farmer/procurement-linked payment) | Not Supported for supplier | Partially Supported for farmers | Partially Supported for farmers | Partially Supported for farmers | Not Supported for suppliers |
| Accounting integration | Not Supported automatically | Not Supported | Not Supported | Not Supported | Not Supported | Not Supported |
| Operational reports | Supported (procurement, payments, inventory, sales, farmer) | Partially Supported | Not Supported | Not Supported | Not Supported | Partially Supported |

Evidence: `CropMaster` is the single shared item-like entity; procurement references only `Farmer`; sales references `Customer` and `CropMaster`; only procurement/sale write stock ledger; no production/material/supplier models are present. Reports endpoints aggregate the existing records. Finance journal `source_type`/`source_id` constraints prohibit source-linked operational journals.

## 5. Data model and integration map

```text
Organization
 ├─ Users ── Role ── RolePermission (present, but not used by endpoint guards)
 ├─ Villages ── Farmers ── Shareholder (0..1)
 │                  ├─ FarmerCrops ── CropMaster (shared/global)
 │                  ├─ Procurement ── CropMaster
 │                  │       ├─ InventoryLedger [IN on create; polymorphic ref]
 │                  │       └─ Payments ── Farmer
 │                  └─ (no direct customer/vendor account ledger)
 ├─ Customers ── Sales ── CropMaster
 │                    └─ InventoryLedger [OUT on create; polymorphic ref]
 ├─ InventoryLedger ── CropMaster [computed balances, no valuation/location/lot FK]
 ├─ FinancialYears ── Accounts ── JournalLines ── JournalEntries
 │                                      └─ optional party_type/id → Farmer/Customer
 │   (no source FK/operational posting link; source_id constrained NULL)
 ├─ Licenses
 └─ OrganizationSettings

 ReportsService reads operational records, posted journals and licenses.
```

**Missing or indirect links:** inventory source IDs are generic text/integer, not foreign keys; crop master is globally shared rather than owned by an organization; payments are procurement-linked but do not update procurement paid balance; Sale's paid/pending flag has no receipt relation; finance party IDs are typed but not DB foreign keys to farmer/customer; journal source fields intentionally do not link to operational records; settings route does not establish tenant ownership in its service.

**Overlapping concepts:** `CropMaster` means crop/commodity and also sale/inventory item. Procurement has string `warehouse_id` and `lot_number`, while inventory has no warehouse/lot structure. Sale line item concept is one `Sale` row rather than an invoice header with multiple lines. Organization settings are separate from core Organization fields; location tables coexist with village free-text state/district/block values.

## 6. Gaps and recommended decisions

### Ten priority gaps

| # | Gap | Importance |
|---|---|---|
| 1 | Procurement edit/deactivation does not synchronize its inventory ledger row. | **MVP blocker** for trustworthy stock. |
| 2 | No supplier/vendor or purchase workflow for non-farmer goods. | **Blocker** for resale and packaging inputs. |
| 3 | Crop master is the only stock item identity; no org-specific products/SKUs or type/brand/pack-size metadata. | **Blocker** for private label and third-party resale; migration decision needed. |
| 4 | No multi-line invoice/document model; current sale is one crop per transaction. | **Blocker** for practical product sales and packaging SKU catalog. |
| 5 | No transformation/production/packing model (BOM, batch, input issue, finished output, waste/by-product). | **Blocker** for private label/manufacturing; later than trading MVP. |
| 6 | Inventory has no UOM conversion service, valuation/cost layers, warehouse, batch or expiry. | UOM/basic stock integrity is **blocker**; location/valuation/lot capabilities are model-dependent and can follow. |
| 7 | No customer receipt allocation, supplier bill balance or subledger; Paid/Pending is a single flag. | **Blocker** for reliable receivable/payable tracking; basic cash reporting can follow. |
| 8 | Finance does not post from procurement, payment, sale or stock. | **Blocker** if MVP requires financial statements; can follow an operational pilot only if limitation is accepted. |
| 9 | Tenant enforcement is inconsistent: global crop masters, settings arbitrary organization IDs, and several services rely on role/path checks. | **Blocker** before multi-FPO production use; review all cross-tenant reads/writes. |
| 10 | Thin lifecycle tests for procurement, payments, sales, inventory cross-module behavior; no frontend tests/E2E. | **Blocker** to confidently declare local E2E-ready, though not a product data-model blocker. |

### Existing features to reuse

- Preserve Farmer, Village, Shareholder and FarmerCrop registry workflows for FPO membership/field context.
- Reuse crop master only as an agricultural commodity master or compatibility layer, not as a general stock model without a deliberate evolution path.
- Reuse procurement/sales transaction numbering, current role framework, organization ID pattern, customer registry, inventory ledger/service, and transactional create patterns.
- Reuse finance organization chart, financial years, journal validation/void lifecycle, and reports infrastructure; add source linkage/posting rules rather than a parallel accounting subsystem.
- Reuse report CSV/pagination conventions and test fixture style.

### Data model constraints and isolation risks

Float quantities and fixed KG inventory, unit stored separately, global crop uniqueness, globally unique farmer/shareholder/village identifiers, polymorphic inventory references, and sale single-item rows complicate UOM precision, tenant-local catalogs, auditable corrections and transformations. Finance is stronger on tenant consistency via composite organization foreign keys; older operational relations often use independent foreign keys and service checks, so cross-org association bugs remain possible. `OrganizationSettingsService` does not enforce caller organization. Super Admin cross-org access should be explicit and narrowly tested rather than inferred from role name.

### Missing high-value tests

- Procurement creation/edit/deactivate/reactivate reconciles exactly one inventory row and correct quantity/crop/org.
- Sales create/update/deactivate/reactivate stock checks including simultaneous/cross-crop changes and inactive stock.
- Payment duplicate/partial amount rules, status edits, procurement edits after payment, and org isolation.
- API authorization matrix for all five roles; cross-org IDs for every detail/update endpoint.
- Crop master global/shared behavior under multiple organizations and organization settings tenant isolation.
- E2E browser/API/database workflows for procurement → stock → sale → report, payment → report, and finance journal → report.
- CSV export, empty reports, maximum pagination, time zones/date edges, and UI filters against endpoint query names.
- Migration upgrade from supported existing revisions on PostgreSQL and model/migration parity.

### Smallest viable path for trading + packing + resale, with manufacturing path

1. **Stabilize current operational invariants first:** define transaction correction semantics; reconcile procurement updates/status with linked movements; add tests for procurement/sale/payment tenant and stock lifecycle. Avoid quiet ledger drift.
2. **Add a tenant-owned item catalog with categories and UOM conversions:** retain crop reference for agricultural commodities; represent raw material, packaging material, purchased finished goods and own-brand finished goods as explicit item types. Decide whether to migrate `CropMaster` into/under this catalog or bridge it through a stable item identifier.
3. **Add supplier and purchase receipt/bill basics plus multi-line sales documents/customer receipts:** keep procurement farmer-specific for farmer produce, but make purchased goods use supplier counterparties. Inventory movements must reference source documents and items with organization integrity.
4. **Add a minimal pack/transform batch:** BOM/recipe lines, input issue, output receipt, batch number, actual yield, packing material consumption and wastage. This supports repacking now and provides a base for production orders/by-products later.
5. **Connect accounting after document lifecycle is sound:** define posting templates and reversals/voids for purchase, payment, sale, receipt and stock/production cost; use existing journal service and enforce source idempotency. Add inventory valuation only with an explicit costing policy.
6. **Finish org isolation and test the browser workflows**, then consider warehouse/expiry, lot traceability, returns, richer manufacturing planning and compliance integrations as required by pilot FPOs.

This is an evolutionary path: preserve farmer procurement and existing reports/finance foundations, while introducing generic commercial inventory/document structures where the current crop-only design ends.

## 7. MVP completion checkpoint

### Complete in source

- Authentication, organization/user administration, role-based navigation and backend role guards.
- Farmer/village/shareholder/crop/farmer-crop registries.
- Farmer procurement and farmer payment pages/APIs.
- Crop-keyed inventory balances, ledger and manual adjustment; sales/customer basics.
- Finance chart/year/journal/GL/trial balance foundation.
- License registry.
- Reports UI and operational/report service endpoints.

“Complete” here means the code path is present, not that it was built, run or accepted in an E2E environment.

### Before local end-to-end testing is ready

- Confirm runtime configuration and database availability without exposing secrets; apply migrations only through the project's normal controlled setup (not done in this audit).
- Check migration head `0013` against the target local DB.
- Resolve and test stock reconciliation on procurement edit/deactivation; ensure operational user roles and server guards agree with intended workflow.
- Exercise critical paths with seeded organization/user and representative records, especially procurement → inventory → sale and payment/report.
- Verify finance setup and report scoping with a real local database. Review known tenant isolation holes.
- Build frontend and launch backend/frontend in a local test environment; there is no frontend test script in the package manifest.

### Known build/test blockers and verification boundaries

- No build or test command was run, per the read-only audit scope. Thus current build/test pass state is **Unknown — requires verification**.
- `test_finance_postgres_lifecycle.py` needs `FINANCE_TEST_DATABASE_URL` and PostgreSQL; whether that environment is available is **Unknown — requires verification**.
- Reports has service/API-level test source (`backend/tests/test_reports.py`) and a frontend page, but Reports has **not been verified end to end** from the current evidence.
- No dedicated procurement, payment, inventory or sales lifecycle tests were found in `backend/tests`; frontend test coverage is not present in the package scripts/file inventory.

### Settings remaining

Frontend `/settings` is only `ComingSoon`. Backend supports basic organization settings fields with GET/PUT, but lacks a usable page, user experience, and caller-org authorization in the shown service. No evidence of logo upload/document storage or broader business configuration settings.

### Safest next steps (not executed)

1. Review/fix tenant authorization for settings and all operational detail/update endpoints; document role matrix.
2. Specify whether procurement deactivation/edit is correction, reversal or replacement, then reconcile inventory under that policy.
3. Add focused service tests for procurement, sales and payment lifecycle/isolation; run them against a disposable local test database.
4. Verify migration `0013` and finance setup on a local disposable database; run backend unit suite and PostgreSQL integration suite where available.
5. Build frontend and exercise Reports and core operational flows in browser against local API/database.
6. Decide item catalog/UOM/supplier schema before extending inventory for resale or packing.

## Executive summary requested

### Architecture in 10–15 bullets

- React 18 + TypeScript + Vite frontend with React Router pages.
- Axios shared API client attaches a JWT stored in local storage.
- FastAPI backend mounts domain routers centrally in `backend/app/main.py`.
- SQLAlchemy models and Pydantic schemas with Alembic migrations.
- Most modules use service/repository layers; payments are route-centric.
- Source migration head is `0013` (licenses); live database state was not checked.
- User records belong to an organization and role; API guards use fixed role names.
- Organization IDs are enforced in many services, inconsistently in some settings/master paths.
- Farmer, village, shareholder and farmer crop registries are implemented.
- CropMaster is shared globally and doubles as crop, inventory item and sales product.
- Procurement and sales create inventory movements; payments are farmer/procurement-linked.
- Inventory balances are summed from active quantity-only ledger rows in KG.
- Finance supports manually posted/voided journals but has no operational transaction posting.
- Licenses and operational reports have backend workflows; Settings UI is a placeholder.
- Tests are backend unittest; no frontend test command is declared; no tests were run here.

### Biggest three product/packing/manufacturing findings

1. Agricultural crop procurement → inventory → crop sale has a real integrated stock path.
2. Generic supplier purchasing/resale and separate packaging/finished-goods identities are absent.
3. No production/packing transformation, batch consumption/output, cost rollup, or wastage/by-product workflow exists; inventory is not valued.

### Smallest viable next development step

First make existing stock lifecycle consistent and tested (especially procurement edit/deactivation); then define an organization-owned item/UOM catalog and supplier purchase receipt as the smallest foundation for both private-label packing and third-party resale.

### Exact evidence gaps requiring manual verification

- Whether current frontend TypeScript/Vite build succeeds and backend imports/startup succeed.
- Whether Alembic revision `0013` is applied to the intended local database.
- Whether PostgreSQL journal trigger integration tests can run in the available local test environment.
- Whether Reports UI, filters and CSV export work end to end against a running API/database.
- Whether procurement/sales/payment pages match current request/response schemas in live use.
- Whether role setup/seed data and intended cross-FPO access rules match the deployed environment.
- Whether organization settings authorization and other tenant boundaries are acceptable for pilot use.
