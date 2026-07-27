# 🩺 PCOS Prediction System

A Full-Stack Machine Learning web application for predicting the risk of Polycystic Ovary Syndrome (PCOS). The system provides role-based dashboards for Patients, Doctors, and Admins, enabling secure prediction, patient management, and report generation.

---

## 🚀 Features

- 🔐 JWT Authentication & Role-Based Access Control
- 👩 Patient Dashboard
- 👨‍⚕️ Doctor Dashboard
- 👨‍💼 Admin Dashboard
- 🤖 Machine Learning-based PCOS Risk Prediction
- 📊 SHAP Explainability
- 📈 Prediction History
- 📄 PDF Report Generation
- 📱 Responsive UI
- 📑 Swagger API Documentation

---

## 🛠 Tech Stack

### Frontend
- Next.js
- React.js
- Tailwind CSS
- Axios
- Recharts

### Backend
- FastAPI
- SQLAlchemy
- Alembic
- JWT Authentication

### Machine Learning
- Scikit-learn
- XGBoost
- Random Forest
- Logistic Regression
- SHAP
- MLflow

### Database
- PostgreSQL

---

## 📂 Project Structure

```text
pcos-prediction/
│
├── frontend/
├── backend/
├── ml_pipeline/
├── README.md
├── .env.example
└── .gitignore
```

---

## ⚙️ Installation

### Clone Repository

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

---

## 📊 Machine Learning Models

- Random Forest
- XGBoost
- Logistic Regression
- Ensemble Model

The system predicts PCOS risk using clinical parameters and provides explainable predictions using SHAP.

---

## 👥 User Roles

### Patient

- Register/Login
- Enter Health Details
- View Prediction
- Download Report
- View Prediction History

### Doctor

- View Assigned Patients
- Review Predictions
- Add Clinical Notes

### Admin

- Manage Doctors
- Assign Patients
- View Dashboard Statistics
- Monitor System Activity

---

## 📷 Screenshots

> Add screenshots here.

- Home Page
- Patient Dashboard
- Doctor Dashboard
- Admin Dashboard
- Prediction Result

---

## 📌 Future Enhancements

- Email Notifications
- Cloud Deployment
- Real-time Analytics
- Mobile Application
- Multi-language Support

---

## 👩‍💻 Author

**Tammannagari Paavani**

- GitHub: https://github.com/TammannagariPaavani
- LinkedIn: *(https://www.linkedin.com/in/paavani-tammannagari-1240b9382)*

---

