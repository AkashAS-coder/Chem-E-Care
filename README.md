# Chem-E-Care

Chem-E-Care is a unified dashboard and AI-powered management tool for chemical energy facilities. It provides real-time event logging, smart orchestration, compliance tracking, AI insights, and actionable todo lists to help you manage operations efficiently and safely.

## Features

- Unified event entry and logging
- Smart orchestrator for event triage
- Dynamic alert matrix with AI-driven urgency
- ONE Dashboard: assets, compliance, cost, training, and AI insights
- Automated documentation and reporting
- AI-powered analysis and recommendations (Google Gemini API)
- Interactive, persistent todo/action list
- Benefits comparison: legacy vs. new system

## Setup Instructions

### 1. Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <repo-directory>
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Add your Gemini API key:**
   - Create a folder named `.streamlit` in your project root (if it doesn't exist).
   - Create a file `.streamlit/secrets.toml` with:
     ```toml
     GEMINI_API_KEY = "your-gemini-api-key-here"
     ```
4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

### 2. Deploy on Streamlit Cloud

1. **Push your code to GitHub.**
2. **On [Streamlit Cloud](https://streamlit.io/cloud):**
   - Create a new app from your repo.
   - In the app settings, add your Gemini API key under "Secrets" as:
     ```toml
     GEMINI_API_KEY = "your-gemini-api-key-here"
     ```
   - Streamlit Cloud will install dependencies from `requirements.txt` automatically.

## Usage Notes

- **Events and todos are persisted locally as `events.json` and `todos.json`.**
- **AI features require a valid Gemini API key.**
- **All data is processed locally except for AI calls (sent to Google Gemini API).**

## File Structure

- `app.py` — Main Streamlit app
- `requirements.txt` — Python dependencies
- `.streamlit/secrets.toml` — (local only) API secrets
- `events.json` — Local event log (auto-created)
- `todos.json` — Local todo list (auto-created)

## License

MIT License
