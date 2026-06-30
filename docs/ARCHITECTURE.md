# Architecture

## Flow

Excel task pane -> React UI -> frontend API client -> FastAPI backend -> LLM router -> validated response -> deterministic Office.js workbook actions

## Backend Layers

- `app/settings.py`
  - environment-backed configuration
- `app/llm/base.py`
  - provider interface
- `app/llm/router.py`
  - provider selection and fallback orchestration
- `app/llm/openai_provider.py`
  - cloud LLM through OpenAI
- `app/llm/ollama_provider.py`
  - local LLM through Ollama's OpenAI-compatible endpoint
- `app/llm/fallback_provider.py`
  - deterministic no-LLM responses
- `app/services/profiler.py`
  - deterministic spreadsheet profiling
- `app/services/action_planner.py`
  - deterministic cleaning plan generation

## Provider Modes

- `auto`
  - task-aware routing
- `openai`
  - force OpenAI, then fallback if unavailable
- `local`
  - force Ollama, then fallback if unavailable
- `fallback`
  - deterministic only

## Safety Model

- The LLM never mutates Excel directly
- The frontend never calls OpenAI or Ollama directly
- Secrets remain in `backend/.env`
- Full ranges are not sent to the LLM for large selections
- Cleaning and report writes go to new sheets only

## Frontend Responsibilities

- Read selected range context with Office.js
- Send prompt + safe context to backend
- Show provider and backend status
- Apply deterministic workbook actions only after explicit user clicks

## Deterministic Workbook Writes

- insert formula into one selected cell only
- write cleaned output to `AI_Cleaned_<Sheet>`
- write issues to `AI_Issues_<Sheet>` when needed
- write reports to `AI_Report_<Sheet>`
- write summary output to `AI_Summary_<Sheet>`
