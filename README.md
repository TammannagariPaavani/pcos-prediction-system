# 🩺 PCOS Prediction System

A Full-Stack Machine Learning-based web application for predicting the risk of Polycystic Ovary Syndrome (PCOS). The system includes secure authentication, role-based dashboards, and explainable AI to assist patients and healthcare professionals.

## ✨ Features

- 🔐 JWT Authentication
- 👩 Patient Dashboard
- 👨‍⚕️ Doctor Dashboard
- 👨‍💼 Admin Dashboard
- 🤖 Machine Learning Prediction
- 📊 SHAP Explainability
- 📄 PDF Report Generation
- 📈 Prediction History
- 📱 Responsive Design

## 🛠️ Tech Stack

**Frontend**
- Next.js
- React
- Tailwind CSS
- Axios

**Backend**
- FastAPI
- SQLAlchemy
- Alembic
- JWT Authentication

**Machine Learning**
- Scikit-learn
- XGBoost
- Random Forest
- Logistic Regression
- SHAP

**Database**
- PostgreSQL

## 📂 Project Structure

```text
pcos-prediction/
├── frontend/
├── backend/
├── ml_pipeline/
├── README.md
├── .env.example
└── .gitignore
```

## 🚀 Getting Started

```bash
git clone https://github.com/TammannagariPaavani/pcos-prediction-system.git
cd pcos-prediction-system
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 👩‍💻 Author

**Tammannagari Paavani**



---

⭐ If you found this project useful, please consider giving it a star.
