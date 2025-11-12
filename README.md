# Accord25Validator

A document comparison and insurance compliance app with LLM-powered chatbot, voice features, and interactive data visualization.

---

## Project Structure

- `frontend/` — React app (UI, chatbot, charts, PDF export)
- `backend/` — FastAPI app (extraction, LLM, compliance logic)

---

## Prerequisites

- Node.js (v16+ recommended)
- Python 3.8+

---

## Backend Setup (FastAPI)

1. **Navigate to backend folder:**
   ```sh
   cd backend
   ```
2. **Create a virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   # Activate:
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up Claude API token:**
   - Place your Claude API key in `claude_token.txt`.
5. **Run the backend server:**
   ```sh
   uvicorn main:app --reload
   ```
   - The API will be available at `http://127.0.0.1:8000`

---

## Frontend Setup (React)

1. **Navigate to frontend folder:**
   ```sh
   cd frontend
   ```
2. **Install dependencies:**
   ```sh
   npm install
   ```
3. **Start the frontend app:**
   ```sh
   npm start
   ```
   - The app will run at `http://localhost:3000`

---

## Usage

- Upload Employee Agreement and Accord25 Certificate files.
- View compliance summary, interactive charts, and download PDF reports.
- Use the floating chatbot for LLM-powered Q&A, with voice input/output.

---

## Notes

- Ensure both frontend and backend are running for full functionality.
- Configure CORS in FastAPI if accessing backend from a different host/port.
- For production, use proper environment variable management for secrets.

---

## License

MIT
