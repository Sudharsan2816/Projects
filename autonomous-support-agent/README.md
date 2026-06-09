# Autonomous Support Operations Agent

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-multi--agent-F97316)
![LangGraph](https://img.shields.io/badge/LangGraph-orchestration-8B5CF6)
![Claude](https://img.shields.io/badge/Anthropic-Claude-FF6B35)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-task--queue-DC382D?logo=redis&logoColor=white)

> Multi-agent AI system that autonomously classifies, validates, routes, and resolves 1,000+ daily student support tasks at **Edvoy** — reducing manual handling from 100% to under 6% and average response time from 4–8 hours to under 3 minutes.

---

## The Problem

Edvoy's operations team handled 1,000+ student support tasks daily: application status checks, document verification, university query routing, deadline reminders, and escalation triage. Manual processing at this volume created:

- **4–8 hour response delays** on routine, rule-based tasks
- **Inconsistent classification** of urgency and task type
- **Agent burnout** from repetitive work that required no judgment
- **Zero pipeline visibility** — no metrics on task volume, accuracy, or bottlenecks

---

## Solution

A CrewAI + LangGraph multi-agent system with four specialized agents, a confidence-gated routing layer, retry logic with exponential backoff, and a real-time evaluation dashboard.

---

## Architecture

```
Inbound Tasks  (1,000+ / day)
[Email  ·  CRM webhook  ·  Form  ·  API]
         │
         ▼
  FastAPI Ingestion Layer
  (schema validation, deduplication)
         │
         ▼
  Redis Task Queue
         │
         ▼
┌──────────────────────────────────────────────────────┐
│                LangGraph Orchestrator                │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │             CrewAI Agent Pipeline              │  │
│  │                                                │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │         Classifier Agent                 │  │  │
│  │  │  Claude Sonnet                           │  │  │
│  │  │  → Task category (12 types)              │  │  │
│  │  │  → Urgency: CRITICAL / HIGH / MEDIUM /   │  │  │
│  │  │            LOW                           │  │  │
│  │  │  → Routing: AUTO | HUMAN | ESCALATE      │  │  │
│  │  │  → Confidence score (0.0 – 1.0)          │  │  │
│  │  └──────────────────┬───────────────────────┘  │  │
│  │                     │                           │  │
│  │  ┌──────────────────▼───────────────────────┐  │  │
│  │  │         Validator Agent                  │  │  │
│  │  │  → Required field completeness check     │  │  │
│  │  │  → Data quality score                    │  │  │
│  │  │  → Flag incomplete tasks for collection  │  │  │
│  │  └──────────────────┬───────────────────────┘  │  │
│  │                     │                           │  │
│  │         ┌───────────┴────────────┐             │  │
│  │    conf ≥ 0.75                conf < 0.75       │  │
│  │    urgency ≤ HIGH              OR CRITICAL      │  │
│  │         │                          │            │  │
│  │  ┌──────▼──────┐           Human Queue         │  │
│  │  │   Resolver  │           (with full context) │  │
│  │  │    Agent    │                               │  │
│  │  │  → Status   │                               │  │
│  │  │    lookups  │                               │  │
│  │  │  → Template │                               │  │
│  │  │    responses│                               │  │
│  │  │  → CRM      │                               │  │
│  │  │    updates  │                               │  │
│  │  └──────┬──────┘                               │  │
│  └─────────┼────────────────────────────────────┘  │
│            │                                        │
│    Retry Manager                                    │
│    (3 attempts, exponential backoff: 2s / 4s / 8s) │
│    → escalate after max retries                     │
└────────────────────────┬────────────────────────────┘
                         │
            ┌────────────┴───────────┐
            │                        │
        MongoDB                 Evaluation
        (task log,              Dashboard
         audit trail,          (FastAPI + MongoDB
         outcomes)              aggregations)
                               → automation rate
                               → avg latency
                               → confidence dist
                               → accuracy vs labels
```

---

## Key Features

| Feature | Detail |
|---------|--------|
| **Multi-agent orchestration** | CrewAI agents with defined roles, goals, and backstories |
| **LangGraph control flow** | State machine handles branching: auto-resolve vs human escalation |
| **12-category classification** | Application status, document verification, deadline, university query, financial, visa, accommodation, escalation, and more |
| **Confidence thresholding** | Tasks below 0.75 confidence auto-routed to human queue |
| **Human-in-the-loop** | CRITICAL urgency always routes to human, regardless of confidence |
| **Validation pipeline** | Per-category schema check before any automated action |
| **Retry logic** | 3 attempts with exponential backoff (2s, 4s, 8s) before escalation |
| **Audit trail** | Every decision, confidence score, agent action, and outcome logged |
| **Evaluation dashboard** | Real-time metrics on accuracy, latency, automation rate, escalation rate |
| **Full task context on escalation** | Human agents receive classification, validator notes, and all retry errors |

---

## How It Works

**Step 1 — Ingest**
Tasks arrive from email parsing, CRM webhooks, or the API. FastAPI validates the schema, deduplicates by task hash, and pushes to the Redis queue.

**Step 2 — Classify**
The Classifier Agent reads the task description with Claude Sonnet. Returns: category (one of 12), urgency level, routing decision (`AUTO`/`HUMAN`/`ESCALATE`), and confidence score.

**Step 3 — Validate**
The Validator Agent checks required fields for the detected task category. Incomplete tasks are flagged and a data collection follow-up is triggered before processing.

**Step 4 — Route**
- Confidence ≥ 0.75 AND urgency ≤ HIGH → Resolver Agent handles autonomously
- Confidence < 0.75 OR urgency = CRITICAL → routed to human queue with full context packet

**Step 5 — Resolve**
Resolver Agent executes the task: queries downstream systems (university portals, CRM, document store), generates a response from the appropriate template, updates the CRM, and fires any notifications.

**Step 6 — Retry or Escalate**
Any downstream failure triggers retry with exponential backoff. After 3 failures, the task is escalated with full context and the error log attached.

**Step 7 — Evaluate**
Every task outcome is logged. The dashboard tracks automation rate, average end-to-end latency, classification accuracy (vs sampled human labels), and confidence score distribution.

---

## Results

| Metric | Before | After |
|--------|--------|-------|
| Manual handling rate | 100% | **6%** |
| Average response time | 4–8 hours | **< 3 minutes** |
| Daily task capacity | ~200 (team ceiling) | **1,000+** |
| Classification accuracy | N/A | **94%** |
| Escalation rate | 100% | **12%** |
| Agent time on routine tasks | ~80% | **~10%** |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | CrewAI |
| Orchestration | LangGraph StateGraph |
| AI Model | Claude `claude-sonnet-4-6` (Anthropic) |
| Task Queue | Redis |
| API Layer | FastAPI (async) |
| Database | MongoDB (task log, audit trail) |
| Evaluation | FastAPI + MongoDB aggregation pipeline |
| Runtime | Python 3.11+ |
| Deployment | Docker + Railway |

---

## Environment Variables

```bash
# LLM
ANTHROPIC_API_KEY=your_key

# Database
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Agent settings
AUTO_RESOLVE_THRESHOLD=0.75   # confidence cutoff for autonomous resolution
MAX_RETRIES=3                  # attempts before escalation
RETRY_BASE_DELAY=2             # seconds (doubled each attempt)
```

---

## Agent Definitions (CrewAI)

```python
classifier = Agent(
    role="Support Task Classifier",
    goal="Accurately classify task type, urgency, and routing path",
    backstory="Expert in Edvoy's support taxonomy with deep knowledge of "
              "student application workflows and university onboarding processes.",
    llm=claude_sonnet,
    verbose=False,
)

validator = Agent(
    role="Data Completeness Validator",
    goal="Ensure all required fields are present before automated processing",
    backstory="Quality gate specialist who prevents downstream failures "
              "by catching missing information early.",
    llm=claude_sonnet,
    verbose=False,
)

resolver = Agent(
    role="Autonomous Support Resolver",
    goal="Execute routine support tasks accurately and efficiently",
    backstory="Experienced support operator who handles status checks, "
              "document requests, and standard communication autonomously.",
    llm=claude_sonnet,
    verbose=False,
)
```

---

> **Note:** This repository contains architecture documentation and a sanitized reference implementation. Production code is maintained privately within Edvoy's internal infrastructure.
