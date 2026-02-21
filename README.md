# NJORO AI - Production Autonomous Desktop AI System

NJORO AI is a personal autonomous desktop operator that runs a continuous Sense → Plan → Act → Evaluate loop. It uses the Gemini API for intelligent planning and a local SQLite database for state management. The UI is built with PyQt6 featuring a dark cyber theme.

## Features

- **Autonomous Agent Loop:** Continuously senses goals, plans actions, and executes tools.
- **Silent Planning:** Uses Gemini API for reasoning without cluttering the UI.
- **Human-in-the-Loop:** High-risk actions require explicit user confirmation.
- **Persistent Memory:** All goals, journals, and confirmations are stored in SQLite.
- **Cyber UI:** A modern, dark-themed interface built with PyQt6.
- **Safe Execution:** Sandboxed tool execution with idempotency checks.

## Setup Instructions (Windows)

1.  **Prerequisites:**
    - Python 3.9 or higher installed.
    - A Google Gemini API Key (Get one [here](https://aistudio.google.com/app/apikey)).

2.  **Create Virtual Environment:**
    Open PowerShell or Command Prompt in the project folder:
    ```powershell
    python -m venv venv
    ```

3.  **Activate Virtual Environment:**
    ```powershell
    .\venv\Scripts\Activate
    ```

4.  **Install Dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```

5.  **Configuration:**
    - Copy `.env.example` to `.env`:
      ```powershell
      copy .env.example .env
      ```
    - Open `.env` in a text editor and paste your `GEMINI_API_KEY`.

## Running the Application

Ensure your virtual environment is activated, then run:

```powershell
python -m src.main
```
(Note: Using `-m src.main` ensures correct import resolution)

## Architecture

- **`src/agent`**: Contains the core agent loop (`loop.py`) and LLM client (`llm_client.py`).
- **`src/persistence`**: Handles database connections (`database.py`) and schema (`models.py`).
- **`src/tools`**: Manages tool registration (`registry.py`) and built-in tools (`builtin.py`).
- **`src/ui`**: PyQt6 user interface (`main_window.py`) and theme (`theme.py`).
- **`src/utils`**: Configuration and logging.

## Troubleshooting

- **ModuleNotFoundError:** Ensure you are running from the project root using `python -m src.main`.
- **API Errors:** Check your `.env` file and ensure the API key is valid.
- **Database Locks:** The database handles concurrency, but avoid opening it in external viewers while the agent is writing.

## License

Private Project.
