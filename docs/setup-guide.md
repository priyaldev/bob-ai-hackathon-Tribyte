# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10+
- Node.js 18+
- npm
- Git
- IBM Bob — used during development for AI-assisted planning, implementation, debugging, testing, code review, and integration
- IBM Cloud account with watsonx.ai access — required only when runtime watsonx.ai analysis is enabled

## Environment Variables

The backend supports an optional watsonx.ai runtime integration.

Create the environment file:

cd src/backend
copy .env.example .env

Then configure the values as required.

Variable | Description | Required |
USE_LLM | Enables or disables runtime watsonx.ai analysis. Set to true to enable it.| No |
WATSONX_API_KEY	| IBM watsonx.ai API key used for runtime AI analysis. | Required when USE_LLM=true |
WATSONX_PROJECT_ID | IBM watsonx.ai project ID.	| Required when USE_LLM=true |
WATSONX_URL | IBM watsonx.ai service URL. Default: https://us-south.ml.cloud.ibm.com | No |
WATSONX_MODEL_ID | watsonx.ai model used for extraction. Default: ibm/granite-13b-instruct-v2 | No |

Example .env
USE_LLM=false

WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2

For the default deterministic extraction mode, USE_LLM=false can be used and watsonx.ai credentials are not required.

When USE_LLM=true, valid watsonx.ai credentials must be provided.

Do not commit .env or API keys to GitHub.

## Installation

1. Clone the repository
   
git clone https://github.com/priyaldev/bob-ai-hackathon-Tribyte.git
cd bob-ai-hackathon-Tribyte

3. Set up the backend
   
cd src/backend
python -m venv .venv

Activate the virtual environment on Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Install the backend dependencies:

python -m pip install -r requirements.txt

Verify the installation:

python -c "import fastapi; import uvicorn; print('Backend dependencies installed successfully')"

If watsonx.ai support is included in requirements.txt, verify it with:

python -c "import ibm_watsonx_ai; print('watsonx.ai SDK installed successfully')"

3. Set up the frontend

Open a new terminal from the repository root:

cd src/frontend
npm install

## Running the Application

The application consists of a FastAPI backend and a React/Vite frontend.

1. Start the backend

From the backend directory:

cd src/backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

The backend will normally be available at:

http://127.0.0.1:8000

FastAPI interactive API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/api/health

2. Start the frontend

Open a second terminal:

cd src/frontend
npm run dev

Vite will normally make the frontend available at:

http://localhost:5173

Open the displayed Vite URL in a browser.

**Application Flow**

The application processes an investigation through the following pipeline:

User Input
    ↓
React/Vite Frontend
    ↓
FastAPI Backend
    ↓
Input Normalization
    ↓
Entity & Relationship Extraction
    ↓
Fraud Pattern Detection
    ↓
Network Graph Construction
    ↓
Investigation Report
    ↓
FIR-Ready Case Brief

The primary analysis API is:

POST /api/cases/analyze

Example request:

{
  "text": "Victim Anjali Gupta transferred 75000 to account 3344556677. Account 3344556677 later transferred 90000 to account 5566778899."
}

The response contains the generated:

Case ID
Entities
Relationships
Fraud patterns
Network graph
Investigation report
Supported Input

The investigation pipeline is designed to work with unstructured and semi-structured cyber-fraud intelligence.

Supported input formats include:

Plain text
.txt
.csv
.json

The extracted content is normalized into text before being passed through the analysis pipeline.

For demonstration and testing, synthetic cyber-fraud investigation data is provided under:

demo/test-data/

## Running Tests

From the backend directory with the virtual environment activated:

cd src/backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q

For more detailed test output:

python -m pytest -v

Tests should be run after backend changes to verify entity extraction, relationship extraction, fraud-pattern detection, graph construction, and report generation.

## Quick Demo (Optional)

**Option 1: Run the complete application**

Start the backend:

cd src/backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

In a second terminal, start the frontend:

cd src/frontend
npm run dev

Then open:

http://localhost:5173

Enter cyber-fraud investigation notes or upload supported test data through the frontend.

The application analyzes the submitted intelligence and displays:

- Case overview
- Extracted entities
- Relationships
- Detected fraud patterns
- Network visualization
- Investigation findings
- Recommended investigative actions
- FIR-ready case brief

**Option 2: Test the API directly**

Open:

http://127.0.0.1:8000/docs

Find:

POST /api/cases/analyze

Use an input such as:

{
  "text": "Anjali Gupta transferred 75000 to account 3344556677. Rajesh Patel transferred 46000 to the same account. Account 3344556677 transferred 90000 to account 5566778899. Account 5566778899 transferred 85000 to account 7788990011. Device DEV-4455 was observed accessing both accounts."
}

Click Execute to inspect the generated entities, relationships, patterns, graph, and report.

## Troubleshooting

| Issue                                         |                         Solution             |
ModuleNotFoundError: No module named 'fastapi' | Activate the backend virtual environment and run python -m pip install -r requirements.txt. |
uvicorn is not recognized	| Use python -m uvicorn app.main:app --reload instead of calling uvicorn directly.|
Import "ibm_watsonx_ai" could not be resolved	| Activate .venv and run python -m pip install ibm-watsonx-ai. Make sure Bob/Python is using src/backend/.venv/Scripts/python.exe.|
watsonx.ai returns 401 Unauthorized	| Check WATSONX_API_KEY and WATSONX_PROJECT_ID in src/backend/.env.|
watsonx.ai analysis fails	| Verify the credentials, project ID, service URL, and model ID. The deterministic extraction mode can be used by setting USE_LLM=false.|
Frontend shows vite is not recognized	| Run npm install inside src/frontend, then run npm run dev.|
npm install reports dependency errors |	Ensure Node.js 18+ is installed and check the project's package.json and package-lock.json. |
Frontend cannot connect to backend | Make sure the FastAPI server is running on http://127.0.0.1:8000 and that the frontend is using the configured backend API URL.|
CORS error in browser |	Ensure the backend is running and the frontend origin is included in the FastAPI CORS configuration. |
API returns no expected relationships |	Check the input structure and ensure the relationship is expressed clearly, such as Person operates Account, Device accesses Account, or Account A -> Account B.|
Application returns validation errors	| Check the JSON request body and ensure the /api/cases/analyze request contains a non-empty text field.|
PowerShell does not allow virtual-environment activation |	Run PowerShell with the appropriate execution policy for your environment, or activate the environment using the available Python/terminal method.|
Port 8000 is already in use	| Stop the existing backend process or start Uvicorn on another available port.|
Port 5173 is already in use |	Stop the existing Vite process or use the alternative port displayed by Vite.|
