# Solution Overview

## What We Built

We built a Cyber Fraud Network Analyzer that helps investigators turn fragmented cyber-fraud information into a connected investigation.

Fraud intelligence often arrives as messy complaint notes, transaction records, phone numbers, bank accounts, device IDs, and names. Looking at these pieces individually can make important connections difficult to identify.

Our solution takes this information as unstructured or semi-structured input and automatically extracts the important entities and relationships between them. It then builds a visual network, identifies potentially suspicious fraud patterns, highlights important connected entities, and generates an investigation-oriented case brief with recommended actions.

Instead of only showing individual records, the system helps investigators answer questions such as:

Which people are connected to which accounts?
Which accounts received money from multiple victims?
Is the same device associated with multiple accounts?
Does money appear to move through multiple accounts?
Which entities are highly connected and therefore worth investigating further?
What evidence should investigators verify next?

The system is designed as an investigative aid. It identifies relationships and patterns from the supplied information but does not treat an automatically identified person as a confirmed offender.

## How It Works

The core workflow converts raw investigation information into a structured fraud network.

1. Investigator provides case information

The investigator can provide cyber-fraud intelligence through the application, including unstructured investigation notes and supported structured files.

Examples include:

Victim complaints
Transaction information
Phone numbers
Bank accounts
Device IDs
Names of people
Other investigation notes

The system is designed to support text and file-based investigation data such as TXT, CSV and JSON where extraction is available.

2. The input is normalized

Different input formats are converted into a common text representation.

This allows information coming from different sources to enter the same analysis pipeline instead of requiring a separate investigation workflow for every file format.

3. Entities are extracted

The analysis service identifies important entities from the investigation information.

Examples include:

People
Victims
Phone numbers
Devices
Bank accounts
Transactions

Each extracted entity receives a structured identifier and relevant metadata.

4. Relationships are extracted

The system determines how the identified entities are connected.

For example:

Person → uses → Phone
Person → belongs to → Bank Account
Device → accesses → Bank Account
Victim → transferred to → Bank Account
Bank Account → transferred to → Bank Account

This converts unstructured investigation notes into a relationship network.

5. Fraud patterns are detected

The system examines the relationships for potentially suspicious patterns.

Examples include:

Multiple-source transactions: one account receives transfers from multiple sources.
Shared device: one device is associated with multiple accounts.
Multi-hop transaction path: transactions form a path through multiple accounts.
Highly connected entities: entities connected to many other entities can be highlighted for further investigation.

These are investigative indicators, not automatic proof of criminal activity.

6. The network graph is generated

The extracted entities become nodes and their relationships become edges.

For example:

Victim
   │
   ▼
Bank Account A
   │
   ▼
Bank Account B
   │
   ▼
Bank Account C

The frontend presents this network visually so investigators can inspect connections that may be difficult to see in raw records.

7. Investigation findings are generated

The system combines the extracted entities, relationships, and detected patterns to produce an investigation-oriented summary.

It identifies:

Entity counts
Transaction information
Detected patterns
Key connected entities
Evidence that may require verification
Recommended investigative actions

8. A FIR-ready case brief is prepared

The final output organizes the available information into a structured case brief that can assist investigators in preparing further documentation.

The brief is based only on the information supplied to the system. It does not invent missing evidence or treat investigative indicators as confirmed facts.

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the detailed diagram.

[Optionally include a simple ASCII or Mermaid diagram here for quick reference.]

```
[User] → [Frontend: React] → [API: FastAPI] → [watsonx.ai] → [Dashboard]
                                    ↓
                             [PostgreSQL DB]
```

## Key Design Decisions

| Decision | Rationale |
| Use a structured entity-relationship model |	Cyber-fraud investigations depend heavily on connections between people, accounts, devices, phones, transactions, and victims. Representing these relationships explicitly makes the information easier to analyze and visualize.|
| Separate extraction, pattern detection, graph construction, and reporting into services | Keeping these responsibilities separate makes the system easier to test, debug, extend, and integrate with the frontend.|
| Use deterministic extraction as a fallback | The system can still analyze investigation text when runtime LLM access is unavailable. This provides a reliable development and demonstration path without making the entire application dependent on an external AI service. |
| Support optional watsonx.ai analysis | When enabled, runtime AI can improve extraction from less structured investigation text while keeping the deterministic pipeline available as a fallback.|
|Use a network graph rather than only tables |	A graph makes relationships such as shared devices, multiple victims connected to one account, and multi-hop transaction paths easier to inspect.|
|Generate evidence-based investigative recommendations | The report focuses on relationships and patterns found in the supplied information and identifies items that investigators should verify rather than presenting assumptions as facts.|
|Keep potential roles investigative rather than definitive | Terms such as intermediary or potential central entity are treated as investigation indicators. The system does not declare a person a confirmed offender based solely on automated analysis.|
|Use synthetic demonstration data	| The hackathon prototype can demonstrate the complete workflow without requiring access to real private banking, telecom, or law-enforcement records.|

## IBM Technologies Used

**IBM Bob**

IBM Bob is used as the team's AI-powered software engineering agent throughout development.

Bob supports the development lifecycle rather than acting as the application's runtime inference API. The team uses Bob for:

Architecture planning
Backend implementation
Frontend development
Entity and relationship extraction logic
Fraud-pattern detection
Debugging
Testing
Frontend/backend integration
Code review
Documentation

The development workflow is:

Understand → Plan → Implement → Test → Review

This makes IBM Bob a load-bearing part of the software development process rather than simply mentioning it as a technology.

**IBM watsonx.ai**

IBM watsonx.ai provides the runtime AI capability used to analyze cyber-fraud investigation information.

The backend AI service connects to watsonx.ai through the IBM watsonx.ai Python SDK. The configured model is:

ibm/granite-13b-instruct-v2

The model is used to help identify structured entities and relationships from cyber-fraud investigation text.

The runtime flow is:

Investigation Text
       ↓
FastAPI Backend
       ↓
AI Service
       ↓
IBM watsonx.ai
       ↓
Structured Entities + Relationships
       ↓
Fraud Analysis + Graph + Report

The extracted information is then passed to the fraud-pattern detection, graph construction, and reporting components to produce the final investigation view.
