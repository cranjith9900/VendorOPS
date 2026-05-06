# VendorOPS

FastAPI SAP adapter with business partner, bank account, SAP reference-table validation, PostgreSQL support, Swagger docs, automated endpoint tests, and a Postman collection.

## Run Locally

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run with SQLite:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Run with PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql://postgres@localhost:55432/sap_adapter_test"
python seed_postgresql.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Tests

Run all SQLite-backed endpoint tests:

```powershell
python -m pytest
```

Run PostgreSQL endpoint tests:

```powershell
$env:POSTGRES_TEST_DATABASE_URL="postgresql://postgres@localhost:55432/sap_adapter_test"
python -m pytest tests/test_postgresql_endpoints.py
```

Run live smoke tests against a running server:

```powershell
$env:BASE_URL="http://127.0.0.1:8000"
python smoke_test_endpoints.py
```

## Postman

Import `postman_collection.json` into Postman and run the collection against `http://127.0.0.1:8000`.
