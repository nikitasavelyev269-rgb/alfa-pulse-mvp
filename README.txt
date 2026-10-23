# ALFA PULSE — staff_comment update

This package updates the backend source files so employee comments are stored
separately from client comments (`notes`).

## Files
- `app/models.py`
- `app/schemas.py`
- `app/main.py`
- `migrations/add_staff_comment.sql`

## Important: existing PostgreSQL database
Uploading the Python files does NOT add the column to an existing PostgreSQL table.
Run `migrations/add_staff_comment.sql` once against the existing database before
testing the updated API. Do not drop/recreate the table.

## API test
PATCH `/api/applications/2/status` with:
```json
{
  "status": "need_documents",
  "staff_comment": "Для продолжения рассмотрения предоставьте выписку по расчётному счёту."
}
```
Then GET `/api/applications?limit=50&offset=0` and confirm the row includes `staff_comment`.

`staff_comment` should contain only a comment intended to be shown to the client.
