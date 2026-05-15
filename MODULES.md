# Backend Module Documentation

## auth
- Handles JWT login and `me` endpoint.
- Depends on `user` repository and security helpers.

## user
- Manages internal users and roles (admin, student manager, card issuer, finance, canteen staff, parent).
- Provides admin-only creation and listing APIs.
- Exposes admin-only system settings APIs for the system administrator account.

## student
- Creates/reads student records.
- Generates QR code data for student cards.
- Auto-creates linked parent user and a wallet at registration time.

## wallet
- Exposes wallet balance APIs.
- Handles wallet recharge operations and records recharge transactions.

## transaction
- Stores immutable ledger-style records for recharge and purchase events.
- Supports transaction history retrieval per student.

## product
- CRUD-style product operations for POS inventory and pricing.
- Enforces SKU uniqueness and stock boundaries.

## invoice
- Creates POS invoices from product lines.
- Performs atomic wallet deduction with insufficient-balance protection.
- Decrements stock and records purchase transactions.

## notification
- Creates and lists school notifications.
- Supports global notifications and student-targeted notifications.
