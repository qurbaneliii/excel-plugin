# Local Setup

## 1. Backend

```powershell
cd "C:\Users\qurba\OneDrive\Desktop\excel plugin\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## 2. Frontend

```powershell
cd "C:\Users\qurba\OneDrive\Desktop\excel plugin\frontend"
npm install
npm start
```

## 3. Optional OpenAI

Put your backend-only key in `backend/.env`:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
LLM_PROVIDER=auto
```

## 4. Optional Ollama

```powershell
ollama pull qwen3:4b
```

Optional models:

```powershell
ollama pull llama3.2:3b
ollama pull qwen3:8b
```

Then configure:

```env
LOCAL_LLM_ENABLED=true
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen3:4b
LOCAL_LLM_TIMEOUT_SECONDS=120
```

## 5. Excel Sideloading

1. Open Excel desktop
2. Go to `Insert` -> `My Add-ins`
3. Upload `C:\Users\qurba\OneDrive\Desktop\excel plugin\frontend\manifest.xml`
4. Open the task pane from the add-in command

## 6. In-Add-In Validation

- Refresh backend status
- Refresh selected range
- Check provider availability
- Test local LLM if using Ollama
- Run analysis on a selected range
