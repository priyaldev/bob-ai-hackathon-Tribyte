# Presentation Slides Plan — Cyber Fraud Network Analyzer (Team TriByte)

## Top-Level Overview

Create an 8-slide `presentation/slides.pptx` deck for the **Cyber Fraud Network Analyzer** project by Team TriByte, submitted to the IBM Bob AI Hackathon (AI Track). The deck follows the recommended structure in `presentation/README.md` and is authored entirely through the `office_edit` / `office_read` tooling.

Each slide is a single, focused unit. Visual hierarchy beats bullet-points. Colour palette: deep navy (#0f3460) background, white text, IBM cyan accent (#00b4d8), warning amber (#f4a261) for severity callouts.

**Additional confirmed scope:** Fill in `submission.yaml` with team info (TriByte, Priyal Jain, Aakriti Ghimire, Khushi Ganatra) before or alongside slide creation.

---

## Sub-Tasks

---

### Sub-Task 1 — Create the PPTX skeleton (blank file + master)

**Intent:** Bootstrap `presentation/slides.pptx` with 8 blank slides so every subsequent sub-task can target a known slide index.

**Expected Outcomes:**
- `presentation/slides.pptx` exists and can be opened with `office_read`.
- 8 slides are present (all blank at this stage).

**Todo List:**
1. Use `office_edit` batch operation to create the file and add 8 slides.
2. Verify with `office_read mode:outline` that 8 slides are listed.

**Relevant Context:**
- Output file: `presentation/slides.pptx`
- `office-insights` skill must be loaded before editing.

**Status:** [ ] pending

---

### Sub-Task 2 — Slide 1: Title

**Intent:** Establish project identity, team name, and track on the opening slide.

**Expected Outcomes:**
- Slide 1 has a large title, subtitle, and track badge.

**Content:**
| Element | Text |
|---------|------|
| Title | Cyber Fraud Network Analyzer |
| Subtitle | Turning Fragmented Fraud Data into Connected Intelligence |
| Team | Team TriByte  ·  IBM Bob AI Hackathon |
| Track badge | AI Track |

**Todo List:**
1. Add title shape (large, bold, white, centred).
2. Add subtitle shape below (medium, cyan, centred).
3. Add team + track line at the bottom.

**Relevant Context:** `submission.yaml` fields: team.name = TriByte, track = AI.

**Status:** [ ] pending

---

### Sub-Task 3 — Slide 2: Problem

**Intent:** Communicate the scale and pain of manual cyber-fraud investigation to judges quickly.

**Expected Outcomes:**
- Three compelling stat/fact blocks visible at a glance.
- One headline problem statement.

**Content:**
| Element | Text |
|---------|------|
| Slide title | The Problem |
| Headline | Cyber-fraud investigations are drowning in disconnected data |
| Stat 1 | 95 000+ UPI fraud cases — FY 2023, Jharkhand alone |
| Stat 2 | Investigators manually trace phones, accounts, SIMs, devices |
| Stat 3 | Most cases go unsolved — a missed link = a missed lead |
| Pain call-out | Manual investigation takes weeks. Patterns stay invisible. |

**Todo List:**
1. Add slide title shape.
2. Add headline shape.
3. Add three stat boxes as individual shapes.
4. Add pain call-out shape (amber accent).

**Relevant Context:** `docs/problem-statement.md`.

**Status:** [ ] pending

---

### Sub-Task 4 — Slide 3: Solution

**Intent:** Show the full investigation pipeline in one clear flow so judges understand what was built without reading code.

**Expected Outcomes:**
- Seven-step pipeline flow readable as a linear diagram (text boxes + arrows).

**Content (pipeline steps):**
1. Raw Investigation Text (unstructured notes, CSV, JSON)
2. Input Normalization
3. Entity Extraction — Persons, Phones, Accounts, Devices, UPI IDs
4. Relationship Mapping — USES, TRANSFERRED_TO, ASSOCIATED_WITH
5. Fraud Pattern Detection — 3 pattern types
6. Interactive Network Graph — React Flow visualization
7. FIR-Ready Investigation Brief

Tagline: *From raw notes to investigation-ready intelligence — in seconds.*

**Todo List:**
1. Add slide title "The Solution".
2. Add tagline shape.
3. Add 7 pipeline step shapes as a left-to-right flow.

**Relevant Context:** `docs/solution-overview.md`, `src/backend/app/services/`.

**Status:** [ ] pending

---

### Sub-Task 5 — Slide 4: Architecture

**Intent:** Give a technical overview of how the system is composed.

**Expected Outcomes:**
- Three-tier layout (Frontend | Backend | AI Layer) shown as labelled boxes.
- Key technologies named in each tier.

**Content:**
| Tier | Technology | Key Components |
|------|-----------|---------------|
| Frontend | React 18 + Vite + React Flow | Investigation form, Network graph, Entity panel, FIR brief |
| Backend | FastAPI + Python 3.10 | /api/cases/analyze, ai_service, fraud_service, graph_service, report_service |
| AI Layer | IBM watsonx.ai (Granite-13B) | Entity + relationship extraction (optional, with deterministic fallback) |

**Todo List:**
1. Add slide title "Architecture".
2. Add three tier boxes (stacked or side-by-side) with technology labels.
3. Add REST API arrow between Frontend and Backend.
4. Add watsonx.ai arrow from Backend to AI Layer (labelled "optional").

**Relevant Context:** `docs/architecture.md`, `src/backend/app/main.py`.

**Status:** [ ] pending

---

### Sub-Task 6 — Slide 5: Key Features / Demo Flow

**Intent:** Walk judges through the most impressive feature — the end-to-end analysis from paste-to-graph.

**Expected Outcomes:**
- Six feature callouts with concise labels.

**Content:**
| # | Feature | Detail |
|---|---------|--------|
| 1 | Entity Extraction | 7 entity types: Person, Victim, Phone, Device, Bank Account, UPI ID, Transaction |
| 2 | Relationship Mapping | 4 relationship types including TRANSFERRED_TO with amounts + timestamps |
| 3 | Fraud Pattern Detection | MULTIPLE_SOURCE · SHARED_DEVICE · MULTI_HOP — with severity levels |
| 4 | Interactive Network Graph | React Flow: drag, zoom, click-to-detail |
| 5 | Deterministic Fallback | Works without AI — regex-based extraction ensures reliability |
| 6 | FIR-Ready Brief | Structured case summary with recommended investigative actions |

**Todo List:**
1. Add slide title "Key Features".
2. Add six feature shapes, each with title + one-line description.

**Relevant Context:** `src/backend/app/services/`, `src/frontend/src/`.

**Status:** [ ] pending

---

### Sub-Task 7 — Slide 6: IBM Technologies

**Intent:** Explicitly demonstrate how IBM products were used — critical for hackathon scoring.

**Expected Outcomes:**
- Two IBM technology blocks clearly separated.
- Usage evidence (not just name-drops) in each block.

**Content:**
| Technology | Role | How Used |
|-----------|------|----------|
| IBM Bob | Primary dev agent | Architecture planning, backend services, entity extraction logic, React Flow integration, test suite, debugging, documentation |
| IBM watsonx.ai | Runtime AI inference | Granite-13B model for enhanced entity/relationship extraction from unstructured investigation text; optional with deterministic fallback |

**Todo List:**
1. Add slide title "IBM Technologies".
2. Add IBM Bob block (left): icon area + usage bullets.
3. Add IBM watsonx.ai block (right): icon area + model name + usage bullets.

**Relevant Context:** `submission.yaml` ibm_technologies field; `src/backend/app/services/ai_service.py`.

**Status:** [ ] pending

---

### Sub-Task 8 — Slide 7: Results / Impact

**Intent:** Quantify the value delivered and frame success for judges.

**Expected Outcomes:**
- Three measurable / qualitative impact statements.
- One clear before/after framing.

**Content:**
| Impact Area | Before | After |
|------------|--------|-------|
| Investigation time | Weeks of manual tracing | Minutes end-to-end from text to FIR brief |
| Pattern detection | Missed due to volume | Automated detection of 3 fraud pattern types |
| Accessibility | Requires expert analyst | Any investigator with the platform |

Additional callouts:
- Complete pipeline: 7 stages, from raw text to structured brief
- Supports 4 input formats: TXT, CSV, JSON, plain text
- 3 fraud pattern types detected automatically
- 100% working without external AI (deterministic fallback)

**Todo List:**
1. Add slide title "Impact & Results".
2. Add before/after table as two side-by-side column shapes.
3. Add four callout stat shapes at the bottom.

**Relevant Context:** `docs/solution-overview.md`, `README.md`.

**Status:** [ ] pending

---

### Sub-Task 9 — Slide 8: Team

**Intent:** Introduce the three team members and their contributions.

**Expected Outcomes:**
- Three member cards with name and primary contribution area.

**Content:**
| Member | Role |
|--------|------|
| Priyal Jain | Team Lead — Backend services, IBM watsonx.ai integration |
| Aakriti Ghimire | Frontend — React UI, React Flow network visualization |
| Khushi Ganatra | AI/ML — Entity extraction, relationship mapping, fraud patterns |

Footer: *Built with IBM Bob · IBM Bob AI Hackathon · AI Track*

**Todo List:**
1. Add slide title "Our Team".
2. Add three member card shapes.
3. Add footer line.

**Relevant Context:** `submission.yaml` team members section.

**Status:** [ ] pending

---

## Notes for Implementation

- Load `office-insights` skill before any `office_edit` call.
- All `office_edit` calls must be **serial** (never parallel).
- Prefer `operation:batch` when adding multiple shapes to a single slide.
- After all slides are populated, run `office_read mode:outline` to verify structure.
- Save final file as `presentation/slides.pptx`.
