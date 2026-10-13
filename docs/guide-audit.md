# Google Cloud Build with Gemini Track 3 — Comprehensive Guide Audit

**Audit Date:** 2026-10-13  
**Guide Source:** [Google Cloud Build with Gemini Track 3 VM Manual](https://storage.googleapis.com/bwg-track3-demo-guide/VM-Manual/index.html)  
**Environment Target:** Linux Workstation (`/config/Desktop/BuildWithGemini`), Qwiklabs ephemeral environment `qwiklabs-gcp-04-9ecf92a8e298`.

---

## 1. Executive Summary & Audit Scope

This document provides a rigorous, resource-by-resource audit of the Track 3 lab guide ("Agent-First Apps") for the Build with Gemini World Tour. The lab illustrates how to build a cloud-native agentic application by composing Google Cloud Agent Platform primitives (ADK, `agents-cli`, Memory Bank, Firestore, Cloud Storage, Gemini Generative Models, Code Execution Sandbox, A2UI, and Cloud Run).

Our objective is to assess each component's applicability to an **AI Workout Coach** prototype, establish whether it is required, optional, or unnecessary for our working prototype, and define deterministic local alternatives to prevent blocking on external cloud quotas, billing restrictions, or network disruptions.

---

## 2. Resource-by-Resource Technical Audit

### 2.1. Antigravity 2.0 (AGY) & Antigravity IDE
* **Official URL:** [https://antigravity.google](https://antigravity.google)
* **Purpose:** Google's standalone agentic coding environment equipped with autonomous tool calling, file management, terminal execution, and contextual skill loading.
* **Role in Prototype:** **Required** (Current execution environment).
* **Prerequisites & Credentials:** Lab identity login (`antigravity-sa@qwiklabs-...`), active session.
* **Access & Configuration:** Pre-installed on the workstation. Verified active in session.
* **Integration:** Hosts the pair-programming and development workflow.
* **Local Alternative:** Standard VS Code / Cursor / CLI with local Python venv (can be used if GUI/remote desktop is disconnected).
* **Risks & Limitations:** Ephemeral workspace resets when the Qwiklabs VM is torn down.

---

### 2.2. Google Agents CLI (`agents-cli`) & ADK (Agent Development Kit)
* **Official URL:** [https://google.github.io/agents-cli/guide/getting-started/](https://google.github.io/agents-cli/guide/getting-started/) · [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
* **Purpose:** Unified CLI toolchain and Python framework for scaffolding, running, evaluating, and deploying Google Cloud ADK agents.
* **Role in Prototype:** **Required / Core Architecture**.
* **Prerequisites & Credentials:** Python 3.10+; GCP credentials (`gcloud auth application-default login` or Service Account key).
* **Access & Configuration:** Installed at `/opt/venv/bin/agents-cli` (v1.4.0) with ADK tools.
* **Integration:** Used for agent lifecycle, local playground (`adk web`), tool schemas, and deployment packaging.
* **Local Alternative:** Standalone Python FastAPI backend running direct agent domain logic with pluggable model adapter.
* **Risks & Limitations:** ADK GA (1.1.0+) deploys agents via A2A (Agent-to-Agent) protocol. Running bare `adk` without `uv run` or project venv can lead to module resolution issues.

---

### 2.3. Google Developer Knowledge MCP
* **Official URL:** [https://codelabs.developers.google.com/developer-knowledge-mcp-antigravity](https://codelabs.developers.google.com/developer-knowledge-mcp-antigravity) · `https://developerknowledge.googleapis.com/mcp`
* **Purpose:** Provides grounded, current access to official Google Cloud, Firebase, and ADK documentation via Model Context Protocol over SSE.
* **Role in Prototype:** **Optional** (Assists development and documentation lookup).
* **Prerequisites & Credentials:** Authenticated Google credentials (`authProviderType: google_credentials`).
* **Access & Configuration:** Configured in `.agents/mcp_config.json` and `~/.gemini/config/mcp_config.json`.
* **Integration:** Queried during development to confirm exact API signatures and IAM roles.
* **Local Alternative:** Local markdown documentation and offline specification files.
* **Risks & Limitations:** Requires outbound internet access to Google Developer Knowledge endpoints.

---

### 2.4. Firebase CLI & Firebase MCP Server
* **Official URL:** [https://firebase.google.com/docs/ai-assistance/mcp-server](https://firebase.google.com/docs/ai-assistance/mcp-server)
* **Purpose:** Local stdio MCP server exposing over 30 tools for interacting with Firebase services, managing Firestore schemas, security rules, and project configs.
* **Role in Prototype:** **Optional / Supporting Tool**.
* **Prerequisites & Credentials:** Node.js (v20+), `firebase-tools` npm package, active GCP project credentials.
* **Access & Configuration:** Installed globally via npm (`firebase-tools@15.33.0`) and registered in both workspace and global `mcp_config.json`.
* **Integration:** Used by coding agent to inspect cloud databases and deployment state.
* **Local Alternative:** Direct Python SDK access or local SQLite database for development.
* **Risks & Limitations:** Interactive CLI logins are disabled in headless containers; must rely on GCP Application Default Credentials.

---

### 2.5. Cloud Firestore (Database)
* **Official URL:** [https://console.cloud.google.com/firestore](https://console.cloud.google.com/firestore)
* **Purpose:** Serverless NoSQL document database for structured persistent application storage (user profiles, workout logs, plans).
* **Role in Prototype:** **Optional Cloud Target / Local-First Alternative Recommended**.
* **Prerequisites & Credentials:** Active GCP project with Firestore in Native mode (`roles/datastore.user` IAM role).
* **Access & Configuration:** Requires setting explicit project ID string (not number).
* **Integration:** Backend repository layer can target Firestore via `google-cloud-firestore`.
* **Local Alternative:** **SQLite3** or file-based JSON repository with identical repository interface. This provides 100% deterministic, zero-latency, offline-capable unit and integration testing.
* **Risks & Limitations:** On Agent Engine/Platform, `GOOGLE_CLOUD_PROJECT` returns the project *number*, which causes `NotFound: The database (default) does not exist` unless hardcoded or pinned by ID. Firestore also introduces network latency into unit test suites.

---

### 2.6. Google Cloud Storage (GCS)
* **Official URL:** [https://cloud.google.com/storage](https://cloud.google.com/storage)
* **Purpose:** Object storage for binary media assets (generated exercise demo images, user media, video clips).
* **Role in Prototype:** **Optional / Future Enhancement**.
* **Prerequisites & Credentials:** GCP Storage bucket with public read permissions (`roles/storage.objectViewer` on `allUsers`) or signed URLs.
* **Access & Configuration:** `gsutil mb` or `gcloud storage buckets create`.
* **Integration:** Image generation tool writes bytes to GCS and returns public `https://storage.googleapis.com/...` URLs for A2UI cards.
* **Local Alternative:** Local static asset directory (`/static/images/...`) served by FastAPI.
* **Risks & Limitations:** Qwiklabs organizational policies frequently enforce "Public Access Prevention" (PAP), which blocks public bucket creation and breaks external image URLs.

---

### 2.7. Gemini Generative Models (`gemini-2.5-flash`, `gemini-3.8-flash`)
* **Official URL:** [https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal-overview](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal-overview)
* **Purpose:** High-speed LLMs for intent classification, workout plan generation, contextual coaching dialogue, and tool calling.
* **Role in Prototype:** **Required for LLM Layer** (with Mock Model fallback).
* **Prerequisites & Credentials:** Vertex AI API (`aiplatform.googleapis.com`) enabled, `roles/aiplatform.user` IAM role.
* **Access & Configuration:** Vertex AI SDK (`google-genai` or `google-cloud-aiplatform`).
* **Integration:** Connected via an abstract `ModelAdapter` interface in the coaching engine.
* **Local Alternative:** Deterministic Mock Model Adapter (`MockWorkoutCoachLLM`) providing validated, predictable responses for unit/integration tests without token consumption or network dependencies.
* **Risks & Limitations:** Rate limits, transient 503 errors, and token latency. Non-deterministic generation can violate fitness plan schema unless strictly validated.

---

### 2.8. Gemini Image Generation (`gemini-3.1-flash-lite-image` / Nano Banana 2 Lite)
* **Official URL:** [https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-flash-lite-image](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-flash-lite-image)
* **Purpose:** Generates visual exercise illustrations or anatomical diagrams from text prompts in the `global` region.
* **Role in Prototype:** **Optional / Stretch Goal**.
* **Prerequisites & Credentials:** Global Vertex AI endpoint access and GCS bucket for public hosting.
* **Access & Configuration:** Vertex AI GenAI SDK image generation call.
* **Integration:** Callable tool `generate_exercise_visual(exercise_name)`.
* **Local Alternative:** Curated SVG/PNG anatomical exercise asset library or placeholder thumbnails.
* **Risks & Limitations:** Model availability is restricted to specific regions; generation adds 3–6 seconds per turn.

---

### 2.9. Agent Platform Code Execution Sandbox (`AgentEngineSandboxCodeExecutor`)
* **Official URL:** [https://docs.cloud.google.com/gemini-enterprise-agent-platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform)
* **Purpose:** Isolated serverless Python execution environment for running generated code safely.
* **Role in Prototype:** **Unnecessary for MVP**.
* **Prerequisites & Credentials:** Agent Platform provisioned instance.
* **Access & Configuration:** Configured via ADK runtime deployment metadata.
* **Integration:** Used for executing dynamic user Python code.
* **Why Unnecessary:** Our AI Workout Coach requires **deterministic, auditable fitness arithmetic** (volume load calculations, 1RM progression formulas, training frequency checks) implemented directly in validated application Python code, rather than unverified LLM-generated sandbox scripts.

---

### 2.10. Vertex AI Memory Bank
* **Official URL:** [https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank)
* **Purpose:** Managed cross-session episodic and factual memory store for remembering user preferences, restrictions, and history across disparate sessions.
* **Role in Prototype:** **Optional Cloud Enhancement / Local Profile Persistence Used First**.
* **Prerequisites & Credentials:** Deployed Agent Engine runtime resource (`agentengine://<id>`).
* **Access & Configuration:** `adk web` launched with `--memory_service_uri`.
* **Integration:** `PreloadMemoryTool` and post-turn memory callbacks.
* **Local Alternative:** Normalized relational User Profile and Fitness Restriction database tables in SQLite/PostgreSQL, which are deterministic, queryable, and immediate.
* **Risks & Limitations:** Asynchronous background extraction means memories are not immediately available on the next turn; cannot guarantee 100% recall of critical medical/injury contraindications.

---

### 2.11. Agent-to-User Interface (A2UI)
* **Official URL:** [https://a2ui.org/](https://a2ui.org/) · [https://adk.dev/integrations/a2ui/](https://adk.dev/integrations/a2ui/)
* **Purpose:** Open standard for agents to emit structured UI components (cards, tables, action forms) as JSON instead of unstructured Markdown text.
* **Role in Prototype:** **Supported in presentation layer**.
* **Prerequisites & Credentials:** `a2ui-agent-sdk`, `A2uiSchemaManager` (v0.8), and `a2ui_utils.py` callback.
* **Access & Configuration:** Bundled in `.agents/skills/enable-a2ui`.
* **Integration:** The agent's responses format workout plans and session summaries into A2UI card schemas.
* **Local Alternative:** Standard REST JSON responses rendered by a clean, lightweight web UI.
* **Risks & Limitations:** Streaming tokens breaks A2UI parsing in certain dev UIs; requires strict adherence to schema version 0.8.

---

### 2.12. FastAPI Proxy & Chat Frontend
* **Official URL:** [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
* **Purpose:** Lightweight proxy server providing REST/WebSocket endpoints to web clients, managing session tokens, and routing turns to the agent.
* **Role in Prototype:** **Required (Core App Serving)**.
* **Prerequisites & Credentials:** Python 3.10+, `uvicorn`, `fastapi`.
* **Access & Configuration:** Bundled in `.agents/skills/build-agent-frontend/template`.
* **Integration:** Serves both static frontend assets and REST API endpoints (`/profiles`, `/workout-plans`, `/workout-sessions`, `/coach/chat`).
* **Local Alternative:** Same FastAPI server running locally at `http://localhost:8080`.
* **Risks & Limitations:** Minimal risks; robust, standard, and easy to test.

---

### 2.13. Google Cloud Run Deployment
* **Official URL:** [https://cloud.google.com/run](https://cloud.google.com/run)
* **Purpose:** Fully managed serverless container runtime for hosting the FastAPI web application.
* **Role in Prototype:** **Optional Deployment Target (Phase 7)**.
* **Prerequisites & Credentials:** Cloud Run API enabled, IAM permissions (`roles/run.admin`), container build support.
* **Access & Configuration:** `gcloud run deploy workout-coach --source . --region us-central1 --allow-unauthenticated`.
* **Integration:** Production cloud target for the complete application container.
* **Local Alternative:** Local Docker container or direct `uvicorn` runner.
* **Risks & Limitations:** Service account needs explicit IAM bindings (`roles/aiplatform.user`, `roles/datastore.user`) to talk to GCP services.

---

## 3. Technology Selection Matrix for AI Workout Coach

| Component | Lab Guide Default | Selected Prototype Choice | Justification |
|---|---|---|---|
| **Architecture** | Cloud-only Agent Platform | Modular Python Service (FastAPI + Agent Domain) | Ensures 100% offline testability, zero quota dependencies, and fast iteration. |
| **Persistence** | Cloud Firestore | SQLite3 (with repository interface) | Deterministic, ACID-compliant, zero network overhead, easily swappable to Firestore via repository pattern. |
| **Model Adapter** | Vertex AI Gemini only | Pluggable `ModelAdapter` (Gemini API + Deterministic Mock) | Allows full automated test suites to run deterministically and cost-free, while supporting live Gemini 2.5/3.8 Flash. |
| **Domain Logic** | Prompt-driven arithmetic | Deterministic Python Fitness Engine | Progress percentages, 1RM estimates, and volume totals must never hallucinate. |
| **Safety System** | General prompt instructions | Hardcoded Medical Red-Flag & Movement Contraindication Guardrails | Health and safety cannot rely solely on soft prompt compliance. |
| **Frontend** | Static single-file chat | HTML5 / Modern CSS / Vanilla JS dashboard + chat | Provides structured workout views, logging forms, and conversation without bloated NPM frameworks. |
