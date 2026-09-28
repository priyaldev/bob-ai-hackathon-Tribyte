# Architecture

## System Architecture

[Describe the overall architecture of your system. Replace the Mermaid diagram below with your actual architecture.]

```mermaid
graph TD A[Investigator] -->|Case text / File upload| B[Frontend - React + Vite] B -->|POST /api/cases/analyze| C[Backend API - Python + FastAPI] C --> D[Input Processing & Normalization] D --> E[AI / Extraction Service] E -->|SDK| F[IBM watsonx.ai] F -->|Entities & Relationships| E E --> G[Entity Model - Pydantic] E --> H[Relationship Model - Pydantic] G --> I[Fraud Pattern Detection] H --> I G --> J[Graph Service] H --> J I --> K[Report Service] J --> K K --> L[Case Analysis Response] L --> B B --> M[Investigation Dashboard] M --> M1[Case Overview] M --> M2[Entities & Relationships] M --> M3[Fraud Patterns] M --> M4[Network Graph] M --> M5[Investigation Report] M --> M6[FIR-Ready Case Brief] N[IBM Bob] -.->|Development & Engineering| C N -.->|Development & Engineering| B N -.->|Testing & Debugging| E N -.->|Code Review & Documentation| K
```

## Components

| Component | Technology | Responsibility |
|Frontend | React + Vite | Investigation dashboard, case input, file upload, results visualization |
|Backend API | Python + FastAPI	| API endpoints, request handling, analysis orchestration |
|AI / Intelligence | IBM watsonx.ai | Extracts entities and relationships from unstructured fraud data |
|Entity & Relationship Models |	Pydantic |Structures people, victims, accounts, devices, phone numbers, and their relationships |
|Fraud Pattern Detection | Python | Detects multiple-source transactions, shared devices, and multi-hop transaction patterns |
|Graph Service | Python + React Flow | Builds and visualizes the fraud network as nodes and relationships |
|Report Service	| Python | Generates case summaries, key entities, findings, and recommended investigative actions |
|FIR-Ready Case Brief | Python + React | Presents investigation findings in a structured FIR-ready format |
|IBM Bob | IBM Bob | Supports development, architecture planning, implementation, debugging, testing, integration, and documentation |

## Data Flow

The system transforms unstructured cyber-fraud investigation information into a structured network and investigation report.

- The investigator provides case information through the React + Vite frontend using text or supported case files.
- The frontend sends the investigation data to the FastAPI backend through the /api/cases/analyze endpoint.
- The backend processes and normalizes the supplied information into a form suitable for analysis.
- The AI / extraction service analyzes the investigation data using IBM watsonx.ai and identifies relevant entities and relationships.
- Extracted information is represented using structured Pydantic entity and relationship models.
- The fraud pattern detection service analyzes the relationships and identifies potentially suspicious patterns, such as multiple victims or sources connected to the same account, shared device usage, and multi-hop transaction paths.
- The graph service converts the extracted entities and relationships into graph nodes and edges.
- The report service generates an investigation summary, key entities, identified patterns, and recommended investigative actions.
- The backend returns the complete case analysis to the frontend.
- The frontend displays the results through the investigation dashboard, including the case overview, entities, relationships, fraud patterns, network graph, investigation report, and FIR-ready case brief.

## Security Considerations

- Sensitive credentials such as IBM watsonx.ai API keys and project identifiers are stored using environment variables and are not committed to the repository.
- Secrets and configuration files containing credentials should be excluded through .gitignore.
- The prototype is designed around synthetic/mock investigation data rather than real personal banking or telecom records.
- The system does not treat a detected network relationship as proof of criminal activity. Findings are presented as indicators requiring investigation and verification.
- Person-level roles such as potential intermediary or potential central entity are derived from available network evidence and should not be interpreted as confirmed criminal status.
- Recommended investigative actions are based only on information identified in the supplied case data; the system should not invent missing evidence.
- CORS is configured on the FastAPI backend to allow communication with the development frontend.

## Scalability Notes

The current implementation is designed as a hackathon prototype with a modular frontend and FastAPI backend. The backend services are separated into AI extraction, fraud-pattern detection, graph generation, and report generation components, allowing individual parts of the pipeline to be extended independently.

For a larger production deployment, the architecture could be extended by:

- Deploying multiple stateless FastAPI instances behind a load balancer.
- Introducing a persistent database for investigation cases, entities, relationships, and analysis history.
- Using a graph database for large-scale relationship analysis and complex network queries.
- Processing large files asynchronously using background workers or a task queue.
- Adding caching and batching for AI inference requests.
- Introducing authentication, authorization, audit logging, and centralized secrets management.
- Scaling the frontend and API independently based on usage.
- Adding more advanced fraud-detection rules and network-analysis algorithms as additional investigation patterns are identified.
