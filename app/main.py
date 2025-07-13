import streamlit as st
import time
import json
import sqlite3
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text

# — Streamlit page config (must be first)
st.set_page_config(
    layout="wide",
    page_title="Cold Email Generator",
    page_icon="⚡🤖",
)

# — Meta-style CSS Styling —
st.markdown("""
<style>
.streamlit-expanderHeader, .streamlit-expanderContent {
    max-width: 100% !important;
}
pre, pre code {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-x: hidden !important;
}
.title {
    text-align: center;
    font-size: 3rem;
    font-weight: 700;
    margin: 1.5rem 0;
    color: #00f2ff;
    text-shadow: 2px 2px 6px rgba(0, 242, 255, 0.5);
}
div.stButton > button:first-child {
    background: linear-gradient(45deg, #00f2ff, #4facfe) !important;
    color: #0f2027 !important;
    font-size: 1.2rem !important;
    font-weight: bold;
    padding: 0.6rem 1.2rem !important;
    border: none !important;
    border-radius: 0.4rem !important;
    transition: transform 0.2s ease-in-out;
}
div.stButton > button:first-child:hover {
    transform: scale(1.05);
    background: linear-gradient(45deg, #4facfe, #00f2ff) !important;
}
</style>
""", unsafe_allow_html=True)

# — Main Streamlit App Logic —
def create_streamlit_app(llm, portfolio, clean_text):
    st.markdown('<h1 class="title">⚡🤖 Cold Email Generator</h1>', unsafe_allow_html=True)

    # --- Sidebar for Feedback ---
    st.sidebar.header("Feedback")
    feedback_text = st.sidebar.text_area("Share your feedback:", max_chars=500)
    feedback_submit = st.sidebar.button("Submit Feedback")

    # --- SQLite setup ---
    db_path = "feedback.db"
    txt_path = "feedback_responses.txt"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if table exists and has correct columns
    try:
        c.execute("SELECT text FROM feedback LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("DROP TABLE IF EXISTS feedback")
        c.execute("""
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    if feedback_submit and feedback_text.strip():
        c.execute("INSERT INTO feedback (text) VALUES (?)", (feedback_text.strip(),))
        conn.commit()
        st.sidebar.success("Thank you for your feedback!")
        # Save to txt file in JSON format
        feedback_entry = {
            "text": feedback_text.strip(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(txt_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry) + "\n")

    url_input = st.text_input(
        "Enter a Job Posting URL:",
        placeholder="Enter the job URL here..."
    )

    if st.button("Generate ⚡"):
        if not url_input.strip():
            st.warning("⚠️ Please enter a valid job URL before generating.")
        else:
            with st.spinner("🔄 Generating your cold email, please wait…"):
                try:
                    loader = WebBaseLoader([url_input])
                    data = clean_text(loader.load().pop().page_content)

                    portfolio.load_portfolio()
                    jobs = llm.extract_jobs(data)

                    # ✅ Show success message immediately before emails
                    st.success("✅ Cold email(s) generated!")

                    for idx, job in enumerate(jobs, start=1):
                        skills = job.get('skills', [])
                        links = portfolio.query_links(skills)
                        email = llm.write_mail(job, links)

                        with st.expander(f"📧 Generated Email #{idx}", expanded=True):
                            placeholder = st.empty()
                            typed_text = ""
                            for char in email:
                                typed_text += char
                                placeholder.code(typed_text, language="markdown")
                                time.sleep(0.002)  # Adjust typing speed here

                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")

# — Entry point —
if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    create_streamlit_app(chain, portfolio, clean_text)