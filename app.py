import os
import streamlit as st
import requests
import json
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure Hugging Face API
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

SYSTEM_PROMPT = """
You are AdigyAssist, a helpful and friendly support specialist for Adigy, an automated Amazon ads management software for KDP publishers.

Overview: Adigy (formerly Adsology) optimizes Amazon advertising campaigns for KDP publishers, ideal for beginners or those with lower ad spend ($100–$1,000/month per marketplace). It automates campaign creation and bid management to improve ACOS (Advertising Cost of Sale) and profitability. Unlike AdsDroid (a premium "done-for-you" agency service with account managers), Adigy is self-service and software-driven. It works for both fiction (category/product targeting) and non-fiction (keyword-focused) books.

Key Features:
- Campaign Types: Auto, Broad, Product Targeting, Brand Defense, Gold Panning (low-bid research campaigns, ~$0.11 bids, 19% ACOS).
- Management: Takes over existing campaigns, creates new ones, adjusts bids up to 6x/day, and optimizes for break-even ACOS.
- Targeting: Supports Top 10 Targets (manual keywords/ASINs) and auto-adds negative keywords/phrases.
- Marketplaces: Manages ads across 11 Amazon markets (US, UK, CA, etc.) with separate budgets.
- Formats: Advertises Kindle, paperback, hardcover (toggle per book).
- Extras: Integrates royalty data via Chrome extension for profitability insights; manages Sponsored Products (primary) and existing Sponsored Brands/Video ads.

Pricing & Budget:
- Cost: $249/month and 3.3 per cent fee on ad spend over $2,000. 30-day money-back guarantee; no free trial.
- Budget: Minimum $100/marketplace; recommended $500–$1,000 for best results. Set monthly per marketplace, not per book.
- ROI: ACOS improves in 3–4 weeks, optimal at 3 months. New books may take longer due to ranking needs.
- Affiliate: 25 per cent lifetime commissions (4 referrals = free subscription).

Setup & Requirements:
- Setup: Connect via "Login with Amazon," install Chrome extension, select books, set marketplace budgets in dashboard (Adigy.ai).
- Sync: <1 hour typically, up to 6 hours for large accounts.
- Requirements: Chrome browser, Amazon KDP/Ads editor access (Adigy@Adigy.ai), accepted Amazon ad terms/billing.
- Cancellation: Pause manually in Amazon Ads or use "Master Undo" in Adigy; set marketplaces to "Off."

Common Issues & FAQs:
1. Sync Stuck? Refresh page, clear cache, re-login, use Chrome, or wait 20–30 min (Amazon server delays).
2. Can’t Connect US Market? Logout, clear cache, re-login; contact support if persistent.
3. High ACOS Initially? Normal for 2–3 weeks as data gathers; optimize book (cover, reviews, price).
4. Low Spend? Adigy starts conservatively, ramps up with data; seasonal dips (e.g., late Dec) normal.
5. Too Many Emails? Adjust Amazon Ads notifications or filter emails.
6. New Book Setup? Toggle "ON" in Unmanaged section; launch mode boosts visibility for 2 months.
7. Reviews Needed? 5–10 minimum, 15+ good, 30–50+ optimal for conversions.
8. Support: Email support@Adigy.ai or use website contact form.

Always respond concisely and helpfully in plain text. Use line breaks where necessary for an output that is easy to read. For complex issues (e.g., Amazon suspensions, policy violations), suggest contacting support@Adigy.ai.
"""

def get_model_response(user_query, conversation_history=[]):
    formatted_conversation = (
        SYSTEM_PROMPT + "\n\n"
        "You are assisting a user with questions about Adigy. Below is the conversation history (if any) and the user's latest query. "
        "Respond directly to the latest query, taking into account the conversation history to maintain context. "
        "Keep your response relevant, concise, and helpful, using plain text without extra formatting or line breaks unless necessary.\n\n"
    )
    
    if conversation_history:
        formatted_conversation += "Conversation History:\n"
        for message in conversation_history[-5:]:
            if message["role"] == "user":
                formatted_conversation += f"User: {message['content']}\n"
            else:
                formatted_conversation += f"Assistant: {message['content']}\n"
        formatted_conversation += "\n"
    
    formatted_conversation += f"Latest User Query: {user_query}\nAssistant:"
    
    payload = {
        "inputs": formatted_conversation,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.6,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(MODEL_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                print(f"Full generated text: {generated_text}")
                assistant_response = generated_text.split("Assistant:")[-1].strip()
                return assistant_response
            else:
                return "I apologize, but I encountered an error processing your query. Please try again."
        else:
            return f"I apologize, but I encountered an error (Status Code: {response.status_code}). Please try again in a moment."
    except Exception as e:
        return f"I apologize, but an error occurred: {str(e)}. Please try again."

# Streamlit UI
st.set_page_config(
    page_title="Adigy Customer Support",
    page_icon="📈",
    layout="centered"
)

st.title("📈 Adigy Customer Support")
st.markdown("Welcome to Adigy customer support! How can I assist you with your Amazon ads today?")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about Adigy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_model_response(
                prompt, 
                st.session_state.messages[:-1]
            )
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("""
<style>
body {
    background-color: #1e1e1e;
    color: #ffffff;
}
.stChatMessage {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    background-color: #2b2b2b;
    color: #ffffff;
}
.stChatMessage.user {
    background-color: #3a3a3a;
    color: #e0e0e0;
}
.stChatMessage.assistant {
    background-color: #2b2b2b;
    color: #ffffff;
}
.stTextInput > div > div > input {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #555555;
}
h1, .stMarkdown {
    color: #ffffff;
}
.stSpinner > div > div {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)