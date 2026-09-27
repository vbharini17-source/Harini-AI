# EduGenie

EduGenie is a Gemini-powered learning assistant for question answering, concept explanations, multiple-choice quizzes, summaries, and guided learning paths.

## Requirements

- Python 3.10 or newer
- Git for Windows
- A Google Gemini API key for generated responses

## Quick Start (Windows)

1. Install Python 3.10+ and Git for Windows if they are not already installed.
2. Open PowerShell in this repository and run:

   ```powershell
   .\setup.ps1
   ```

   The script creates `.venv`, installs `requirements.txt`, runs the tests, initializes Git on `main` if needed, and stages the project. It does not create a commit or push anything.
3. Copy the environment template and add your API key:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

4. Start the app:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

5. Open <http://127.0.0.1:8000>.

Without a key, the home page and health endpoint still work; generation endpoints return a clear setup error.

## Configuration

Settings are read from environment variables or `.env`:

| Variable | Default | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | empty | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model name |
| `GEMINI_FALLBACK_MODEL` | `gemini-flash-lite-latest` | Used automatically if the primary model is overloaded |
| `HOST` | `127.0.0.1` | Development server host |
| `PORT` | `8000` | Development server port |
| `RELOAD` | `true` | Enable Uvicorn reload when run with `python main.py` |

## API

- `GET /health` reports service status and whether a Gemini key is configured.
- `POST /qa` accepts `{"question": "..."}`.
- `POST /explain` accepts `{"topic": "..."}`.
- `POST /quiz` accepts `{"text": "..."}`.
- `POST /summarize` accepts `{"text": "..."}`.
- `POST /learn/recommendations` accepts `{"topic": "...", "level": "beginner"}`. Levels are `beginner`, `intermediate`, and `advanced`.
- Interactive API docs are available at `/docs`.

Inputs are trimmed and length-limited. Generated text is rendered as text in the browser rather than interpreted as HTML.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests do not make Gemini API calls.

## Push to GitHub

After setup, create an empty GitHub repository, then connect and push:

```powershell
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git commit -m "Initial EduGenie project"
git push -u origin main
```

`.env` and the virtual environment are excluded from Git. Never commit your API key.