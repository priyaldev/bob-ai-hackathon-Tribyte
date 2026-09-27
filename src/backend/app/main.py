from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.cases import router as cases_router

app = FastAPI(
    title="Cyber Fraud Network Analyzer",
    description="Backend API for analyzing cyber fraud networks.",
    version="1.0.0",
)

# Allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)

@app.get("/")
def root():
    return {
        "message": "Cyber Fraud Network Analyzer backend is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "cyber-fraud-network-analyzer"
    }
    
