import os
import re
from urllib.parse import quote_plus
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# --- Config (from environment, not hardcoded) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "regional_sales_data")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

mysql_uri = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
db = SQLDatabase.from_uri(mysql_uri, sample_rows_in_table_info=1)

# --- Prompt ---
TEMPLATE = """Based on the table schema below, write a SQL query that would answer the user's question:
Remember: Only provide the SQL query, don't include anything else.
          Provide the SQL query in a single line, don't add line breaks.
Table Schema:
{schema}

Question: {question}
SQL Query:
"""
prompt = ChatPromptTemplate.from_template(TEMPLATE)

# --- LLM: OpenAI instead of Gemini ---
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=OPENAI_API_KEY,
    temperature=0,
)


def get_schema(_):
    return db.get_table_info()


sql_chain = (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | llm.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
)


def extract_query(raw: str) -> str:
    """Pull the SQL out of a ```sql ... ``` block if present, else use raw text."""
    match = re.search(r"```sql\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else raw.strip()


# --- FastAPI app ---
app = FastAPI(title="Text-to-SQL Chatbot API")


class QuestionRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    sql_query: str
    result: str


@app.post("/query", response_model=QueryResponse)
def run_query(payload: QuestionRequest):
    try:
        raw = sql_chain.invoke({"question": payload.question})
        query = extract_query(raw)
        result = db.run(query)
        return QueryResponse(question=payload.question, sql_query=query, result=str(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}