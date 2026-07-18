import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/query"

st.set_page_config(page_title="Text-to-SQL Chatbot", page_icon="🗄️")
st.title("🗄️ Text-to-SQL Chatbot")
st.write("Ask a question about your database in plain English.")

if "history" not in st.session_state:
    st.session_state.history = []

question = st.text_input("Your question", placeholder="e.g. What was the budget of Product 12?")

if st.button("Ask") and question.strip():
    with st.spinner("Generating SQL and fetching results..."):
        try:
            resp = requests.post(BACKEND_URL, json={"question": question}, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            st.session_state.history.append(data)
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")

for item in reversed(st.session_state.history):
    st.markdown(f"**Q:** {item['question']}")
    st.code(item["sql_query"], language="sql")
    st.markdown(f"**Result:** {item['result']}")
    st.divider()