# NXTINT V1

> **Next-generation intelligence and OSINT analysis framework**

NXTINT V1 is a modular intelligence-oriented framework designed to bring together **OSINT ingestion, semantic analysis, evidence-based decision support, investigation timelines, media analysis, and explainable reasoning** in a unified architecture.

It is designed as the next-generation evolution of the earlier [`OSINT-prototype`](https://github.com/jonny14-bro/OSINT-prototype) project, with a stronger separation between core validation, application services, AI/ML components, and investigation intelligence.

---

## ✨ Overview

NXTINT combines multiple intelligence components into a single workflow:

- **OSINT ingestion and normalization**
- **Semantic intelligence and similarity analysis**
- **Evidence-based decision modeling**
- **Investigation assistant and reasoning**
- **Timeline reconstruction and analysis**
- **Media and metadata intelligence**
- **Face/evidence similarity workflows**
- **FAISS-powered vector indexing**
- **Audit and integrity mechanisms**
- **Modular backend architecture**

The goal is to transform scattered evidence and investigation artifacts into structured, searchable, explainable intelligence.

---

## 🧠 Core Architecture

```text
                         ┌─────────────────────┐
                         │       NXTINT UI     │
                         │ Index.html / ui.py  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Flask API       │
                         │      main.py        │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
      ┌─────────────┐       ┌───────────────┐      ┌─────────────┐
      │   Ingest    │       │ AI / Semantic │      │ Core Layer  │
      │   Pipeline  │       │ Intelligence  │      │             │
      └──────┬──────┘       └───────┬───────┘      └──────┬──────┘
             │                      │                     │
             ▼                      ▼                     ▼
      ┌─────────────┐       ┌────────────────┐      ┌─────────────┐
      │ Normalized  │       │ Model 1        │      │ Schema      │
      │ OSINT Data  │       │ Decision       │      │ Validation  │
      └──────┬──────┘       └────────────────┘      ├─────────────┤
             │                                      │ Audit       │
             ▼               ┌────────────────┐     │ Integrity   │
      ┌─────────────┐        │ Model 2        │     └─────────────┘
      │ FAISS /     │◄───────│ Investigation  │
      │ Vector      │        │ Assistant      │
      │ Indexing    │        └────────────────┘
      └──────┬──────┘
             │
             ▼
      ┌──────────────────────┐
      │ Intelligence Output  │
      │ • Evidence           │
      │ • Similarity         │
      │ • Reasoning          │
      │ • Timeline           │
      │ • Confidence         │
      └──────────────────────┘
```

---

## 📁 Project Structure

```text
NXTINT V1/
│
├── Index.html
├── main.py
├── shared.py
├── ui.py
│
├── backend/
│   ├── ai/
│   │   ├── intelligence_builder.py
│   │   ├── semantic_engine.py
│   │   ├── semantic_normalizer.py
│   │   ├── timeline_engine.py
│   │   │
│   │   └── models/
│   │       ├── model1/
│   │       │   ├── config.py
│   │       │   ├── explain.py
│   │       │   ├── features.py
│   │       │   ├── inference.py
│   │       │   ├── model.py
│   │       │   ├── train.py
│   │       │   ├── training_data.csv
│   │       │   └── decision_model_v1.pkl
│   │       │
│   │       └── model 2/
│   │           ├── assistant.py
│   │           ├── chat.py
│   │           ├── compare.py
│   │           ├── config.py
│   │           ├── context.py
│   │           ├── intent.py
│   │           ├── reasoning.py
│   │           ├── responses.py
│   │           └── timeline.py
│   │
│   ├── app/
│   │   ├── faiss_manager.py
│   │   ├── faiss_registry.py
│   │   └── ingest.py
│   │
│   └── tools/
│       └── clean.py
│
├── core/
│   ├── audit.py
│   ├── integrity.py
│   └── schema.py
│
└── .gitignore
```

## 🛠️ Technology Stack

### Backend & AI

- **Python** — Core application and intelligence processing
- **Flask** — REST API and application server
- **FAISS** — Vector similarity search and indexing
- **Machine Learning** — Evidence-based decision modeling
- **Semantic Processing** — Intelligence normalization and similarity analysis

### Frontend & Visuals

- **HTML5** — Interface structure
- **CSS3** — Styling and responsive visual presentation
- **JavaScript** — Client-side interaction and API communication
- **Python UI Layer** — Application-level UI integration
- **Flask** — Frontend/backend communication

### Intelligence & Security

- **OSINT Processing** — Investigation data ingestion and normalization
- **Evidence Analysis** — Multi-factor evidence evaluation
- **Timeline Intelligence** — Temporal investigation and reconstruction
- **Audit & Integrity** — Data validation and integrity mechanisms
- **Vector Intelligence** — FAISS-powered similarity and retrieval

---

## 🔍 Major Components

### 1. OSINT Ingestion

The application layer provides the ingestion pipeline for bringing investigation material into the intelligence workflow. Metadata can then be normalized and prepared for downstream analysis.

### 2. Semantic Intelligence

The semantic layer provides normalization, similarity-oriented processing, and vector-based retrieval through FAISS-backed components.

### 3. Evidence-Based Decision Model

**Model 1** provides an evidence-oriented decision layer using engineered investigation features such as:

- Face similarity
- Image quality
- Metadata similarity
- Username similarity
- Source count
- Platform overlap
- Temporal distance

The model also includes an explanation component for interpreting decisions.

### 4. Investigation Assistant

**Model 2** provides investigation-oriented reasoning workflows, including capabilities around:

- Decision explanation
- Confidence reasoning
- Missing evidence
- Confirmation workflows
- Case comparison
- Suggested next steps
- Timeline-oriented reasoning

### 5. Timeline Intelligence

NXTINT contains dedicated timeline processing for organizing investigation events and supporting temporal reconstruction of evidence.

### 6. FAISS Intelligence Layer

FAISS managers and registries provide the vector-index infrastructure used by the intelligence pipeline for similarity and retrieval operations.

### 7. Audit & Integrity

The `core/` layer provides schema validation, audit functionality, and integrity-related processing to help maintain consistency across investigation data and generated intelligence.

---

## ⚙️ Technology Stack

- **Python**
- **Flask**
- **FAISS**
- **Machine Learning / model inference**
- **Semantic analysis**
- **OSINT data processing**
- **HTML / Python-based UI components**

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/jonny14-bro/NXTINT.git
cd NXTINT
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install project dependencies

Install the Python packages required by the modules in this repository.

```bash
pip install -r requirements.txt
```

> **Note:** A `requirements.txt` file is not included in the current V1 repository snapshot. Dependencies should therefore be documented/generated before publishing a reproducible installation workflow.

### 4. Start the application

The main application is exposed through the Flask entry point:

```bash
python3 main.py
```

The application exposes API endpoints under `/api/`, including a system ping endpoint and analysis-related routes.

---

## 🔐 Security & Data Handling

NXTINT is intended for legitimate research, security analysis, and authorized OSINT investigations.

Do not commit:

- Credentials or API keys
- `.env` files
- Private investigation records
- Personally identifiable datasets
- Generated runtime databases
- Local FAISS indexes
- Sensitive media or evidence

Runtime and sensitive artifacts are excluded through `.gitignore` where appropriate.

---

## 🧩 Design Philosophy

NXTINT V1 is built around four principles:

**Evidence first** — intelligence should be grounded in available evidence rather than unsupported assumptions.

**Modularity** — ingestion, semantic processing, models, timeline analysis, and integrity mechanisms are separated into reusable components.

**Explainability** — decisions should be accompanied by useful reasoning and confidence context where available.

**Integrity** — investigation artifacts should remain structured, auditable, and internally consistent.

---

## 🔗 Relationship to OSINT-prototype

NXTINT is the next-generation evolution of the earlier [`OSINT-prototype`](https://github.com/jonny14-bro/OSINT-prototype) project.

The earlier repository represents the original prototype/research direction, while NXTINT V1 introduces a more modular intelligence-oriented architecture combining semantic processing, evidence-based modeling, investigation reasoning, timeline intelligence, and integrity mechanisms.

---

## ⚠️ Disclaimer

NXTINT is a research/prototype framework. Its outputs should be treated as decision-support information and **not as definitive proof of identity, attribution, or wrongdoing**. Results require appropriate human review and contextual verification.

Use the system only with data and systems you are authorized to analyze.

---

## 📜 License

No license has been specified for this repository yet.

If you intend to make NXTINT open source, add an appropriate license before treating the repository as formally licensed for reuse.

---

## 👨‍💻 Project

**NXTINT V1**  
Next-generation intelligence and OSINT analysis framework.

GitHub: https://github.com/jonny14-bro/NXTINT
