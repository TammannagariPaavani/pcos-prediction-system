# Frontend Guide

## What This Frontend Does

The frontend is a Next.js application for:

- login and registration
- patient prediction form, draft saving, and risk dashboard
- doctor patient list, history trend view, and clinician notes
- admin stats, doctor assignment, and model deployment tools

Main app entry:

- [`src/pages/_app.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/_app.js)

## Frontend Folder Walkthrough

- [`src/pages`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages)
  Next.js pages for login, patient, doctor, admin, and index routing.
- [`src/components`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/components)
  Shared UI pieces like the multistep form, risk card, SHAP chart, report viewer, and workspace shell.
- [`src/api`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/api)
  Axios-based API wrappers for auth, prediction, reports, patients, and admin.
- [`src/context`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/context)
  Auth and theme providers.
- [`src/styles`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/styles)
  Global Tailwind and custom CSS.
- [`public`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/public)
  Static assets area.

## Frontend Technologies

- Next.js
- React
- TailwindCSS
- Axios
- Recharts
- Jest
- ESLint

## Frontend Dependencies

Packages are defined in:

- [`package.json`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/package.json)

Main runtime dependencies:

- `next`
- `react`
- `react-dom`
- `axios`
- `recharts`

Main dev dependencies:

- `tailwindcss`
- `postcss`
- `autoprefixer`
- `eslint`
- `eslint-config-next`
- `jest`
- `jest-environment-jsdom`
- `@testing-library/react`
- `@testing-library/jest-dom`

## Step-by-Step Frontend Setup

### 1. Open the frontend folder

```powershell
cd "C:\Users\91982\Desktop\MCA\pcos prediction system\pcos-prediction\frontend"
```

### 2. Install Node.js

Use Node.js `18+`, preferably `20+`.

Check your version:

```powershell
node --version
npm --version
```

### 3. Install frontend packages

```powershell
npm install
```

This creates:

- [`node_modules`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/node_modules)
- [`package-lock.json`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/package-lock.json)

### 4. Configure API base URL

Frontend reads:

- `NEXT_PUBLIC_API_BASE_URL`

That value is already included in the root env file:

- [`../.env`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/.env)

Default value:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 5. Start the frontend development server

```powershell
npm run dev
```

Frontend will run on:

- [http://localhost:3000](http://localhost:3000)

## Frontend Run Order

For the UI to work correctly:

1. Start the backend first on `http://localhost:8000`
2. Then start the frontend on `http://localhost:3000`
3. Open the browser and go to `http://localhost:3000`

## Frontend Page Guide

### `/login`

Purpose:

- register a new patient or doctor
- log in using backend auth

Files involved:

- [`src/pages/login.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/login.js)
- [`src/context/AuthContext.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/context/AuthContext.js)
- [`src/api/auth.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/api/auth.js)

### `/patient`

Purpose:

- collect PCOS screening inputs
- save and restore intake drafts
- submit the prediction request
- show risk gauge and top contributing features
- preview and download report

Files involved:

- [`src/pages/patient/index.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/patient/index.js)
- [`src/components/InputForm.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/components/InputForm.js)
- [`src/components/RiskCard.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/components/RiskCard.js)
- [`src/components/SHAPChart.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/components/SHAPChart.js)
- [`src/components/ReportViewer.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/components/ReportViewer.js)

### `/doctor`

Purpose:

- list patients
- filter by risk level
- inspect patient prediction history
- write clinician follow-up notes
- export CSV

Files involved:

- [`src/pages/doctor/index.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/doctor/index.js)
- [`src/api/patients.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/api/patients.js)

### `/admin`

Purpose:

- see active users and prediction counts
- assign patients to doctors
- review model governance details
- review recent audit logs
- upload and deploy a new `.joblib` model

Files involved:

- [`src/pages/admin/index.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/admin/index.js)
- [`src/api/admin.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/api/admin.js)

## How Frontend Data Flow Works

1. User opens a page.
2. `AuthContext` checks session state with backend cookies.
3. Page-specific API modules call FastAPI endpoints through Axios.
4. UI updates charts, tables, cards, and report viewer from API responses.

## Important Frontend Config Files

- [`next.config.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/next.config.js)
  Next.js configuration and public API base URL.
- [`tailwind.config.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/tailwind.config.js)
  Tailwind theme setup.
- [`postcss.config.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/postcss.config.js)
  PostCSS plugins.
- [`jsconfig.json`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/jsconfig.json)
  Path alias config for `@/`.
- [`jest.config.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/jest.config.js)
  Jest config.
- [`/.eslintrc.json`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/.eslintrc.json)
  ESLint config.

## Frontend Commands

Install packages:

```powershell
npm install
```

Run development server:

```powershell
npm run dev
```

Run lint:

```powershell
npm run lint
```

Run tests:

```powershell
npm test -- --runInBand
```

Build production bundle:

```powershell
npm run build
```

Start production server after build:

```powershell
npm run start
```

## Recommended Full Project Start Sequence

From the project root:

1. Start PostgreSQL, Redis, RabbitMQ, and MinIO.
2. Start backend:

```powershell
cd backend
uvicorn app.main:app --reload
```

3. Start frontend in a new terminal:

```powershell
cd frontend
npm run dev
```

4. Open:

- [http://localhost:3000](http://localhost:3000)

## Common Frontend Problems

### page loads but API calls fail

Check:

- backend is running on port `8000`
- `NEXT_PUBLIC_API_BASE_URL` matches the backend URL

### login page works but session disappears

Check:

- backend cookies are being set
- frontend and backend URLs are consistent
- backend CORS settings allow the frontend URL

### charts do not render

Check:

- API returned `top_features` or patient history data
- browser console for request failures

### build fails

Run:

```powershell
npm run lint
npm test -- --runInBand
```

Then fix any reported issue before re-running `npm run build`.

## Best Way To Explore This Frontend

Read files in this order:

1. [`src/pages/login.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/login.js)
2. [`src/context/AuthContext.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/context/AuthContext.js)
3. [`src/pages/patient/index.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/patient/index.js)
4. [`src/components/InputForm.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/components/InputForm.js)
5. [`src/pages/doctor/index.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/doctor/index.js)
6. [`src/pages/admin/index.js`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/pages/admin/index.js)
7. [`src/api`](C:/Users/91982/Desktop/MCA/pcos%20prediction%20system/pcos-prediction/frontend/src/api)

That order gives you the clearest path from auth to patient workflow to clinician/admin tools.
