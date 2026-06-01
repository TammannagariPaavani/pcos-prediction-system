# Backend Guide

## What This Backend Does

The backend is a FastAPI service for:

- user registration, login, refresh, and logout
- JWT cookie-based authentication
- role-based access control for `patient`, `doctor`, and `admin`
- PCOS prediction scoring
- prediction history retrieval
- patient draft save and resume
- doctor assignment workflow
- clinician notes on patient history
- PDF report generation
- admin statistics and model deployment
- audit logging

Main entry file:

- [`app/main.py`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/main.py)

## Backend Folder Walkthrough

- [`app/api/routes`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/api/routes)
  Route handlers for auth, prediction, patients, reports, and admin APIs.
- [`app/core`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/core)
  App settings, auth/security helpers, dependencies, and Celery config.
- [`app/db`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/db)
  Database connection helpers and Alembic migrations.
- [`app/models`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/models)
  SQLAlchemy ORM models for users, patients, assignments, drafts, notes, lab results, predictions, and audit logs.
- [`app/schemas`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/schemas)
  Pydantic request and response schemas.
- [`app/services`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/services)
  Prediction logic, clinic workflow services, reporting, and notifications.
- [`app/ml`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/app/ml)
  Shared training, preprocessing, prediction, and SHAP logic.
- [`storage/models`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/storage/models)
  Saved trained model artifacts.
- [`storage/reports`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/storage/reports)
  Generated PDF reports.
- [`tests`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/tests)
  Backend smoke and preprocessing tests.

## Requirements Before You Start

Install these on your machine:

1. Python `3.11` or `3.12`
2. PostgreSQL
3. Redis
4. RabbitMQ
5. MinIO

Optional but useful:

- pgAdmin or DBeaver for PostgreSQL
- RabbitMQ Management UI
- MinIO Console

## Backend Dependencies

All backend Python packages are listed in:

- [`requirements.txt`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/requirements.txt)

Important packages used:

- `fastapi`, `uvicorn`
- `sqlalchemy`, `alembic`, `psycopg2-binary`
- `pydantic`, `pydantic-settings`
- `passlib[bcrypt]`, `python-jose`, `python-multipart`
- `redis`, `celery`
- `scikit-learn`, `xgboost`, `shap`, `mlflow`, `joblib`
- `reportlab`
- `boto3`, `botocore`
- `pytest`, `httpx`, `flake8`

## Step-by-Step Backend Setup

### 1. Open the project root

```powershell
cd "C:\Users\91982\Desktop\MCA\pcos prediction system\pcos-prediction"
```

### 2. Create a Python virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

### 4. Install backend packages

```powershell
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

The backend reads from the root environment file:

- [`../.env`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/.env)

If needed, copy from:

- [`../.env.example`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/.env.example)

Important variables:

- `DATABASE_URL`
- `REDIS_URL`
- `RABBITMQ_URL`
- `JWT_SECRET_KEY`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MLFLOW_TRACKING_URI`
- `MODEL_PATH`

### 6. Create the PostgreSQL database

Example:

```sql
CREATE DATABASE pcos_db;
```

### 7. Run database migrations

From the `backend` folder:

```powershell
alembic upgrade head
```

### 8. Train the ML model artifact

Go back to the project root:

```powershell
cd ..
python ml_pipeline\train.py
```

This creates the model artifact at:

- [`backend/storage/models/pcos_ensemble_v1.joblib`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/backend/storage/models/pcos_ensemble_v1.joblib)

### 9. Start the FastAPI server

```powershell
cd backend
uvicorn app.main:app --reload
```

Backend will run on:

- [http://localhost:8000](http://localhost:8000)

API docs:

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 10. Optional: start a Celery worker

If you want the queue worker running too:

```powershell
cd backend
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

## Backend Run Order

Use this order when starting everything manually:

1. PostgreSQL
2. Redis
3. RabbitMQ
4. MinIO
5. `python ml_pipeline\train.py` if the model artifact does not exist yet
6. `uvicorn app.main:app --reload`
7. optional Celery worker

## How Request Flow Works

### Auth flow

1. Frontend sends register/login request.
2. Backend validates data and hashes password with `bcrypt`.
3. Backend creates JWT access and refresh tokens.
4. Tokens are stored in `httpOnly` cookies.

### Prediction flow

1. Frontend sends the `/predict` request with the validated PCOS input payload.
2. Backend checks the logged-in role.
3. Backend updates patient and lab result records.
4. Backend loads the trained model artifact.
5. Backend engineers extra features and scales inputs.
6. Backend computes risk score and SHAP feature impacts.
7. Backend saves the prediction result.
8. Backend returns risk score, label, recommendation, model version, and top factors.

### Clinic workflow flow

1. Patients can save an intake draft to `/patients/me/draft`.
2. Admins assign patients to doctors through `/patients/{patient_id}/assignment`.
3. Doctors see only assigned patients in their dashboard list.
4. Doctors and admins can add clinician notes through `/patients/{patient_id}/notes`.
5. Patient history now returns predictions plus care-team notes.

### Report flow

1. Frontend requests `/reports/{prediction_id}`.
2. Backend creates a PDF with ReportLab.
3. PDF is stored locally and also attempted in MinIO.
4. Backend returns a downloadable URL.

## Useful Backend Commands

Run tests:

```powershell
cd "C:\Users\91982\Desktop\MCA\pcos prediction system\pcos-prediction\backend"
python -m pytest tests -q
```

Run lint:

```powershell
cd "C:\Users\91982\Desktop\MCA\pcos prediction system\pcos-prediction"
flake8 backend\app backend\tests --max-line-length=120
```

Retrain model:

```powershell
python ml_pipeline\train.py
```

Evaluate model:

```powershell
python ml_pipeline\evaluate.py
```

## Common Backend Problems

### `alembic` cannot connect

Check:

- PostgreSQL is running
- `DATABASE_URL` is correct
- the database exists

### login works but predictions fail

Check:

- model artifact exists in `backend/storage/models`
- `MODEL_PATH` points to the correct file

### report generation fails

Check:

- `backend/storage/reports` is writable
- MinIO config is valid if you want object storage uploads

### import errors

Make sure:

- virtual environment is activated
- packages from `requirements.txt` are installed
- you start `uvicorn` from the `backend` folder, not the workspace root

## Recommended Development Workflow

1. Start PostgreSQL, Redis, RabbitMQ, and MinIO.
2. Activate `.venv`.
3. Run migrations.
4. Train the model if needed.
5. Start the FastAPI server.
6. Start the frontend from the `frontend` folder.
7. Use `/docs` to test APIs while building UI features.
