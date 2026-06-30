# Excel AI Assistant

`excel-ai-assistant` is a local Microsoft Excel Office Add-in MVP with a React + TypeScript task pane and a Python FastAPI backend. The add-in reads the selected Excel range through Office.js, sends safe spreadsheet context to the backend, routes requests across OpenAI, a local Ollama model, or deterministic fallback logic, and writes results back to Excel only through deterministic Office.js actions.

## Features

- Excel task pane add-in with Office.js selection reading
- Safe range profiling with headers, metadata, and sampled rows only
- Hybrid LLM routing:
  - `auto`
  - `openai`
  - `local`
  - `fallback`
- Formula assistant:
  - generate
  - explain
  - fix
  - safe insert into one selected cell only
- Safe cleaning workflow:
  - plan cleaning actions
  - apply deterministic cleaning to a new sheet only
  - optional issues sheet
- Report generation to task pane and new sheet
- Basic summary sheet creation
- Backend-only secret handling

## Architecture

- Frontend: React + TypeScript + Office.js task pane
- Backend: FastAPI
- LLM router:
  - OpenAI provider
  - Ollama local provider
  - deterministic fallback provider
- Workbook writes:
  - deterministic Office.js functions only

See [docs/ARCHITECTURE.md](C:/Users/qurba/OneDrive/Desktop/excel%20plugin/docs/ARCHITECTURE.md).

## Prerequisites

- Windows with Microsoft Excel desktop
- Node.js 18+
- Python 3.11+
- Office Add-in sideloading enabled
- Optional:
  - OpenAI API key for cloud LLM mode
  - Ollama for local LLM mode

## Backend Setup

```powershell
cd "C:\Users\qurba\OneDrive\Desktop\excel plugin\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Put your OpenAI key in `backend/.env`:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
LLM_PROVIDER=auto
LOCAL_LLM_ENABLED=true
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen3:4b
LOCAL_LLM_TIMEOUT_SECONDS=120
```

Start the backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

## Frontend Setup

```powershell
cd "C:\Users\qurba\OneDrive\Desktop\excel plugin\frontend"
npm install
npm start
```

The manifest is at `frontend/manifest.xml`.

## Run Modes

### OpenAI

- Set `OPENAI_API_KEY` in `backend/.env`
- Set `LLM_PROVIDER=openai` or `auto`
- Start backend and frontend

### Ollama / Local LLM

1. Install Ollama
2. Pull a model:

```powershell
ollama pull qwen3:4b
```

Lighter option:

```powershell
ollama pull llama3.2:3b
```

Stronger option:

```powershell
ollama pull qwen3:8b
```

3. Ensure Ollama is running
4. Confirm the local endpoint is `http://localhost:11434/v1`
5. Set in `backend/.env`:

```env
LLM_PROVIDER=local
LOCAL_LLM_ENABLED=true
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen3:4b
```

### Fallback Only

Set:

```env
LLM_PROVIDER=fallback
```

This mode does not require an OpenAI key or Ollama.

## Excel Sideloading

1. Start the frontend dev server
2. Open Excel desktop
3. Go to `Insert` -> `My Add-ins` -> `Upload My Add-in`
4. Choose `frontend/manifest.xml`
5. Open the task pane from the ribbon command

Detailed setup is in [docs/LOCAL_SETUP.md](C:/Users/qurba/OneDrive/Desktop/excel%20plugin/docs/LOCAL_SETUP.md).

## API Endpoints

- `GET /health`
- `GET /api/llm/status`
- `POST /api/llm/test-local`
- `POST /api/analyze-range`
- `POST /api/formula/generate`
- `POST /api/formula/explain`
- `POST /api/formula/fix`
- `POST /api/action-plan`
- `POST /api/report`

## Security

- `backend/.env` is gitignored
- OpenAI API key stays backend-only
- Frontend never receives or stores the API key
- Local LLM requests also go through the backend
- Original Excel sheets are never overwritten

## Troubleshooting

- If the task pane shows backend disconnected, confirm `uvicorn` is running on port `8000`
- If local LLM is unavailable, confirm Ollama is running and the model is pulled
- If Excel does not load the add-in, re-sideload `frontend/manifest.xml`
- If a large selection is chosen, the add-in sends only sampled rows to the LLM and keeps full apply operations under the safe size limit

## Known Limitations

- Live Excel desktop interaction was not testable from this environment
- Chart creation is intentionally skipped for reliability
- Local model quality depends on hardware and model size
- Custom functions are deferred and documented in [docs/CUSTOM_FUNCTIONS_PLAN.md](C:/Users/qurba/OneDrive/Desktop/excel%20plugin/docs/CUSTOM_FUNCTIONS_PLAN.md)
