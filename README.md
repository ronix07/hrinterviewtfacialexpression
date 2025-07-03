# StressIQ – AI-Powered Interview Login System

**StressIQ** is a role-based login portal built using **Streamlit** with a stylish UI and integrated **Firebase Authentication**. It’s designed as the entry point to an AI-powered platform that evaluates candidates' interview performance using facial expression and stress-level analysis.

---

## 🚀 Features

- 🎭 **Role Selection**: Candidate or Interviewer
- 🔐 **Firebase Authentication**: Secure login & registration
- 🎨 **Custom UI**: Fully themed with a modern purple gradient look
- 🔁 **Automatic App Launching**:
  - Candidates are redirected to a **React-based interview platform**
  - Interviewers are redirected to a **Streamlit dashboard**
- 💻 **Port Check**: Automatically checks and launches the necessary backend/frontend

---

## 🧩 Tech Stack

| Purpose            | Technology          |
|--------------------|---------------------|
| Web Framework      | Streamlit           |
| Backend Auth       | Firebase Admin SDK  |
| Frontend (AI View) | React.js (on port 5173) |
| Dashboard          | Streamlit (on port 8502) |
| Styling            | Custom HTML/CSS in Streamlit |
| Environment        | Localhost (dev mode) |

---

## 📂 Project Structure

```bash
.
├── streamlit_login.py             # Main Streamlit login script
├── app.py                         # Interviewer dashboard (Streamlit)
├── aidriven/                      # React front-end for candidate interview
├── firebase-adminsdk.json         # Firebase credentials (do not share)
├── README.md                      # This file



TO START THE PROJECT RUN MOCK.PY 


✅ 1. Main Login System (Streamlit)
Used In: streamlit_login.py

Purpose: Firebase Authentication for Candidate & Interviewer login

Credential File:
Example:
credentials/mock-20306-firebase-adminsdk-fbsvc-e03a8e8956.json

✅ 2. Google Sheets Integration
Used In: Scripts that read/write to Google Sheets (e.g. feedback forms, results)

Credential File:
Example:
credentials/moonlit-haven-452014-i4-248bff09d735.json

 3. Mock Interview App / Dashboard
Used In: mockapp.py or app.py

Purpose: Firebase integration in the interviewer dashboard or mock evaluation

Credential File:
Example:
credentials/assessai-44afc-firebase-adminsdk-fbsvc-9de16c3d2d.json
