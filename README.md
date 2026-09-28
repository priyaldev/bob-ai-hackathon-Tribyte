# 🚀 Cyber Fraud Network Analyzer

> **Team TriByte** — IBM × NFSU Hackathon 2026

---

## 👥 Team

| Field         | Value                                                                   |
| ------------- | ----------------------------------------------------------------------- |
| **Team Name** | TriByte                                                                 |
| **Track**     | AI                                                                      |
| **Team Lead** | Priyal Jain — [jainpriyal048@gmail.com](mailto:jainpriyal048@gmail.com) |
| **Members**   | Priyal Jain, Aakriti Ghimire, Khushi Ganatra                            |

---

## 🎯 Problem Statement

Cyber-fraud investigations often involve large amounts of disconnected data such as transaction records, call logs, phone numbers, SIM cards, devices, and accused individuals. Investigators need to manually connect these entities to identify relationships, fraud patterns, and the roles played by different individuals in a criminal network.

Our project focuses on the **Jamtara-style SIM-swap and mule-account fraud scenario**, helping investigators transform scattered case data into a connected fraud network that can be analyzed more efficiently.

---

## 💡 Solution

**Cyber Fraud Network Analyzer** is an investigation-support platform that converts raw cyber-fraud case information into a visual and structured network of entities and relationships.

The system identifies entities such as **persons, phone numbers, SIM cards, devices, bank accounts, and transactions**, connects them through relationships, detects suspicious fraud patterns, and presents the investigation through an interactive dashboard. It also provides a structured case analysis and supports the generation of an investigation-ready case brief.

---

## ✨ Key Features

* **🔍 Entity Extraction:** Identifies important entities such as persons, phone numbers, SIM cards, devices, accounts, and transactions from case data.

* **🕸️ Fraud Network Visualization:** Displays relationships between entities using an interactive network graph, making complex connections easier to investigate.

* **🚨 Fraud Pattern Detection:** Highlights suspicious patterns such as **SIM-swap indicators** and **mule-account networks**.

* **👑 Criminal Network Hierarchy:** Helps visualize relationships between potential **kingpins, mules, and victims** within a fraud network.

* **📊 Investigation Dashboard:** Provides an overview of entities, relationships, risk indicators, and important investigation findings in a single interface.

* **📄 Case Brief Generation:** Converts the analyzed investigation into a structured case summary with findings and recommended investigative actions.

* **⚡ Investigation Workflow:** Allows investigators to create and analyze a case through a dedicated investigation interface.

---

## 🛠️ Tech Stack

| Category             | Technologies                              |
| -------------------- | ----------------------------------------- |
| **Languages**        | JavaScript, Python                        |
| **Frontend**         | React, CSS                                |
| **Backend**          | Python, FastAPI                           |
| **AI / Analysis**    | AI-based entity and relationship analysis |
| **IBM Technologies** | IBM Bob                                   |
| **Visualization**    | React Flow                                |
| **Icons / UI**       | Lucide React                              |
| **Version Control**  | Git, GitHub                               |

---

## 🏗️ System Overview

The application follows a pipeline-based investigation workflow:

```text
                    ┌──────────────────────┐
                    │     Case Input       │
                    │ Transactions / Logs  │
                    │ Devices / Accused    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    AI Processing     │
                    │ Entity Extraction   │
                    │ Relationship Mining │
                    │ Pattern Detection   │
                    └──────────┬───────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │      Fraud Network Model       │
              │                                │
              │ Persons ↔ SIMs ↔ Devices       │
              │    ↕           ↕                │
              │ Accounts ↔ Transactions        │
              └───────────────┬────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ Investigation UI     │
                    │                      │
                    │ • Network Graph      │
                    │ • Entity Details     │
                    │ • Fraud Analysis     │
                    │ • Risk Indicators    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Case Brief         │
                    │ Findings + Actions   │
                    └──────────────────────┘
```

---

## 📁 Repository Structure

```text
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EntityDetails.jsx
│   │   │   ├── FraudAnalysis.jsx
│   │   │   └── NetworkGraph.jsx
│   │   │
│   │   ├── data/
│   │   │   └── mockCase.js
│   │   │
│   │   ├── pages/
│   │   │   ├── Investigation.jsx
│   │   │   └── NewInvestigation.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── entities.py
│   │   │   └── relationships.py
│   │   └── ...
│   │
│   └── requirements.txt
│
├── docs/
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
│
├── demo/
│   ├── screenshots/
│   └── demo-video-link.txt
│
├── presentation/
│   └── slides.pdf
│
└── README.md
```

> Update the structure above if your final repository folders differ before submission.

---

## ⚡ How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/<your-repository>.git
cd <your-repository>
```

### 2. Start the Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

The backend will run locally at:

```text
http://127.0.0.1:8000
```

### 3. Start the Frontend

Open a new terminal:

```bash
cd frontend

npm install
npm run dev
```

The frontend will be available at the URL displayed by Vite, typically:

```text
http://localhost:5173
```

---

## 🖥️ Demo

| Artifact            | Link                       |
| ------------------- | -------------------------- |
| 📹 **Demo Video**   | `demo/demo-video-link.txt` |
| 🌐 **Live Demo**    | `demo/live-demo-url.txt`   |
| 🖼️ **Screenshots** | `demo/screenshots/`        |
| 📊 **Presentation** | `presentation/slides.pdf`  |

---

## ⚠️ Known Limitations

* The current prototype is primarily designed as an **investigation-support and analysis tool**, not a replacement for a complete law-enforcement investigation system.
* Some case inputs and investigation data may use **mock/synthetic data** for demonstration purposes.
* AI-generated findings should be treated as **investigative leads requiring human verification**.
* The prototype does not independently verify information against external criminal or financial databases.
* Production deployment would require stronger authentication, authorization, audit logging, data encryption, and secure handling of sensitive investigation data.
* The current prototype is optimized for the hackathon demonstration environment and may require additional scalability and security work for production use.

---

## 🏅 What We're Most Proud Of

We are most proud of turning a complex cyber-fraud investigation problem into an **interactive visual investigation workflow**.

Instead of presenting investigators with disconnected records, our system brings entities and relationships together into a single fraud network. The combination of **AI-assisted analysis, relationship mapping, fraud-pattern identification, and interactive network visualization** allows investigators to move from raw case information toward a clearer understanding of how a fraud network may be structured.

Our goal is to make complex cyber-fraud cases **easier to explore, understand, and act upon** while keeping human investigators in control of the final decisions.

---

## 🔐 Responsible AI & Investigation

The system is intended to **support investigators, not make final accusations or legal decisions**.

AI-generated entities, relationships, patterns, and recommendations should be reviewed and verified against appropriate evidence before being used in an actual investigation or legal proceeding.

---

## 👨‍💻 Team TriByte

**Priyal Jain · Aakriti Ghimire · Khushi Ganatra**

> **Turning fragmented fraud data into connected intelligence.**
