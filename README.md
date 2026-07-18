Text-to-SQL Chatbot
Ask questions about your database in plain English and get back the generated SQL query along with the result. Built with a FastAPI backend (LangChain + OpenAI) and a Streamlit frontend.
How it works
You type a question in the Streamlit UI (e.g. "What was the budget of Product 12?")
The frontend sends it to the FastAPI backend
The backend uses an OpenAI model (via LangChain) to convert the question into a SQL query, using your database schema as context
The query runs against a MySQL database and the result is sent back and displayed
Project structure
```
text_to_sql/
├── backend/
│   └── main.py          # FastAPI app: builds the SQL chain, runs queries
├── frontend/
│   └── App.py            # Streamlit UI, calls the backend over HTTP
├── requirements.txt
├── .env.example           # Template for environment variables
└── README.md
```
Setup
1. Install dependencies
```bash
pip install -r requirements.txt
```
2. Configure environment variables
Copy the example file and fill in your real values:
```bash
cp .env.example .env
```
```dotenv
DB_HOST=your-mysql-host
DB_PORT=3306
DB_USER=your-mysql-user
DB_PASSWORD=your-mysql-password
DB_NAME=your-database-name

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
Never commit `.env` to version control — it's already listed in `.gitignore`.
3. Run the backend
```bash
uvicorn backend.main:app --reload --port 8000
```
Check it's up: visit `http://localhost:8000/health` — should return `{"status": "ok"}`.
4. Run the frontend
In a separate terminal:
```bash
streamlit run frontend/App.py
```
This opens the chat UI in your browser and connects to the backend running on port 8000.
Deployment
Database: hosted on Aiven (managed MySQL). Local MySQL instances aren't reachable from cloud-hosted backends, so the database needs to live somewhere publicly accessible.
Backend: deployed on Render as a Web Service.
Build command: `pip install -r requirements.txt`
Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
Environment variables set in the Render dashboard (same keys as `.env.example`)
Frontend: deployed on Streamlit Community Cloud, pointing `BACKEND_URL` in `frontend/App.py` to the deployed Render backend URL.
Notes
The database connection requires SSL, since managed hosts like Aiven enforce it (`ssl_mode: REQUIRED` in the SQLAlchemy engine args).
Passwords containing special characters (like `@`) are URL-encoded via `urllib.parse.quote_plus` before being used in the connection string.
The `/query` endpoint returns the generated SQL alongside the result, so you can sanity-check what the model produced.
Troubleshooting
Issue	Likely cause
`ModuleNotFoundError: No module named 'pymysql'`	Run `pip install -r requirements.txt` again
`Can't connect to MySQL server on '<garbled host>'`	Password contains `@` or another special character and isn't URL-encoded
Frontend shows connection errors	Backend isn't running, or `BACKEND_URL` in `App.py` doesn't match where the backend is hosted
`sql_require_primary_key` error on import	Some tables lack a primary key; either add one or disable the setting in your MySQL host's advanced configuration
