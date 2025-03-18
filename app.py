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

# Lean system prompt
SYSTEM_PROMPT = """
You are AdigyAssist, a helpful and friendly support specialist for Adigy, an automated Amazon ads management software for KDP publishers. Use the provided information to answer user queries concisely and accurately, using formatting to present the informating in an easily readable way. If the info is insufficient, say "I’m not sure about that" and suggest contacting support@Adigy.ai for complex issues (e.g., Amazon suspensions, policy violations).
"""

# Full FAQ data
FAQ_DATA = {
    "what is adigy": "Adigy (formerly Adsology) is an automated Amazon ads management software for KDP publishers, optimizing campaigns to improve performance and returns, ideal for lower ad spend or beginner publishers.",
    "difference between adigy and adsdroid": "Adigy is a self-service tool for lower ad spend or beginners. AdsDroid is a premium 'done-for-you' service with a dedicated account manager for advanced publishers with higher ad spend.",
    "why transition to adigy": "Adsology is rebranding to Adigy as part of evolving our platform. Functionality remains the same; only the name changes.",
    "fiction or non-fiction": "Adigy works for both fiction (category/product targeting) and non-fiction (keyword-focused) books, with differing strategies.",
    "cost": "Adigy costs $249/month plus a 3.3% fee on ad spend over $2,000. No free trial, but a 30-day money-back guarantee is offered.",
    "roi": "ACOS improves in 3-4 weeks, optimal at 3 months. New books with few reviews take longer to reach profitability.",
    "free trial": "No free trial is available, but Adigy offers a 30-day money-back guarantee.",
    "money-back guarantee": "Yes, a 30-day money-back guarantee is available. Contact support within 30 days for a full refund.",
    "cancel subscription": "Subscription stays active until billing period ends. To stop ads immediately: pause in Amazon Ads, use 'Master Undo,' or set marketplaces to 'Off' in Adigy.",
    "affiliate program": "Join at https://Adigy.ai/partner for 25% lifetime commissions. Refer 4 people for a free subscription.",
    "setup": "Connect via 'Login with Amazon,' install the Chrome extension, select books, and set budgets in the Adigy dashboard (Adigy.ai).",
    "sync time": "Syncing takes less than 1 hour, up to 6 hours for large accounts or overloaded Amazon servers.",
    "us marketplace connect": "If you can’t connect, log out of Amazon and Adigy, clear cache, and log back in. Contact support if it persists.",
    "sync stuck": "Refresh the page, clear cache/cookies, re-login to Amazon in Chrome, or try another browser. Contact support if unresolved.",
    "chrome extension": "Yes, it’s required to sync KDP royalty data into Adigy for profitability insights.",
    "other browsers": "Adigy’s extension is Chrome-only. Use Google Chrome for best results.",
    "permissions": "Adigy needs editor access to your Amazon KDP and Ads accounts, plus accepted Amazon ad terms and billing details.",
    "editor access": "Go to https://advertising.amazon.com/user/management/invite, enter Adigy@Adigy.ai, select 'Editor,' grant all country access, and invite.",
    "not eligible books": "This is due to Amazon API issues. Contact support with ASINs to fix if books are active.",
    "duplicate listings": "Duplicates occur from different formats (paperback, Kindle). They’re grouped for management. Contact support if unsure.",
    "email notifications": "Normal when starting. Adjust Amazon Ads notification settings or set email filters to reduce them.",
    "set budget": "Set monthly budgets per marketplace (e.g., US, UK) in the Adigy dashboard’s Marketplace and Budget section.",
    "minimum budget": "Minimum is $100 per marketplace (e.g., $100 USD, £100 GBP).",
    "recommended budget": "Start at $100, but $500-$1,000 per marketplace is recommended for effective results.",
    "budget per book": "Budgets are set per marketplace, not per book or account.",
    "individual book budgets": "No per-book budgets, but pause books or formats in specific marketplaces to limit spend.",
    "stay within budget": "Yes, Adigy optimizes spend to stay within your set budget by adjusting bids.",
    "low ad spend": "Normal at first; Adigy starts conservatively, increasing spend as data shows profitable targets.",
    "allocate budget": "Typically 60-70% to US, 20-25% to UK/CA, rest to others, depending on your books.",
    "ad cost in fee": "No, $249/month is for software only. Amazon bills ad spend separately.",
    "budget allocation": "Adigy dynamically allocates budget to high-performing targets based on ACOS and conversion rates.",
    "spend fluctuations": "Normal due to bid adjustments, seasonal competition, conversion changes, or Amazon auctions.",
    "holiday budget": "Adigy adjusts budgets for Christmas, reducing spend in late December and boosting it in weeks 2-3.",
    "existing campaigns": "Adigy takes over and optimizes existing campaigns for managed books.",
    "new campaigns": "Yes, Adigy creates Auto, Broad, Product Targeting, Brand Defense, and Gold Panning campaigns.",
    "many campaigns": "Multiple campaigns, especially Gold Panning, aid keyword discovery within your budget.",
    "campaign naming": "Format is Book-Ab-Type-Purpose-ASIN-Format-ID (e.g., TI1E-SP-GP-B0DD86533Y-Paperback-ZPOMTS).",
    "specific formats": "Yes, toggle formats (paperback, Kindle) on each book’s page in Adigy.",
    "stop formats": "Pause formats on the book’s detail page in Adigy.",
    "top 10 targets": "Manually select up to 10 keywords and 10 ASINs per book to focus Adigy’s budget.",
    "more than 10 targets": "Possible, but stick to 10 for focused advertising.",
    "exact negatives": "Block exact search terms (e.g., 'dog training book') to avoid irrelevant spend.",
    "phrase negatives": "Block phrases (e.g., 'dog training') and all terms containing them.",
    "blockers in opportunities": "Relevant targets may be blocked if they perform poorly. Unblock if you disagree.",
    "gold panning": "Low-bid ($0.11), broad-match campaigns to find cheap, converting keywords with ~19% ACOS.",
    "turn off gold panning": "Disable in Advanced settings if unwanted.",
    "random keywords": "Unusual keywords in Gold Panning campaigns are for research to find profitable terms.",
    "edit in amazon": "Yes, but minimal manual edits are best to let Adigy optimize.",
    "new book": "New books go to Unmanaged; toggle ON, select formats/markets for launch campaigns.",
    "video ads": "Adigy manages existing Sponsored Brands Video Ads; create them manually in Amazon.",
    "ad types": "Primarily Sponsored Products; also manages manual Sponsored Brands/Video ads.",
    "multiple marketplaces": "Optimizes across 11 marketplaces (US, UK, etc.) with separate budgets.",
    "bid adjustments": "Up to 6x/day for large accounts, daily for small, to optimize performance.",
    "manage specific books": "Yes, choose which books Adigy manages.",
    "rename campaigns": "Yes, rename in Amazon Ads console without affecting Adigy.",
    "stop emails": "Adjust Amazon Ads notification settings or use email filters.",
    "results time": "2-3 weeks for initial improvements, 3 months for full optimization.",
    "metrics": "Adigy optimizes for break-even ACOS, balancing spend and royalties.",
    "high acos initially": "Normal for 2-3 weeks during discovery phase.",
    "reviews needed": "5-10 minimum, 15+ good, 30-50+ optimal for conversions.",
    "high acos popular category": "Check cover, description, reviews, pricing, category, A+ content, sample, badges, bonuses, UGC videos.",
    "improve performance": "Get 10-50+ reviews, optimize description, A+ content, cover, targets, negatives, categories.",
    "seasonal books": "Start 4-6 weeks before peak, boost budget 2 months prior, add seasonal targets, pause post-season.",
    "seasonal peaks": "Yes, Adigy adjusts budgets and bids for peaks like Q4.",
    "good acos": "Paperbacks: 25-45%, Kindle: 30-70%, Hardcovers: 20-30%. Higher during launches.",
    "target acos": "Aims for break-even ACOS, higher for new book visibility.",
    "bid changes": "Frequent bid adjustments optimize based on performance and market conditions.",
    "low bids good keywords": "Strategic to redistribute budget or test new opportunities.",
    "new book launches": "Launch mode boosts visibility for first 2 months.",
    "negative keywords": "Yes, Adigy auto-adds negatives based on performance.",
    "add negatives": "Use the 'Negatives' tab in Adigy to add keywords/ASINs manually.",
    "low budgets": "Low budgets ($1.01/day) are for underperforming campaigns.",
    "ineligible book": "Amazon Ads restriction; Adigy may still manage existing campaigns.",
    "account suspended": "Not caused by Adigy. Contact Amazon Ads support; pause Adigy subscription.",
    "suspension": "Pause Adigy, contact Amazon Ads support. Adigy can’t intervene.",
    "policy violations": "Address with Amazon directly; Adigy complies but can’t resolve violations.",
    "book details change": "Yes, affects performance. Covers/descriptions boost conversions, price/categories shift results.",
    "support": "Email support@Adigy.ai or use the website contact form.",
    "ads still running": "Pause in Amazon Ads, use 'Master Undo,' or set marketplaces to 'Off.'",
    "cancel refund": "Cancel in Account Settings, email support@Adigy.ai for refunds within 30 days.",
    "extension sync": "Refresh, clear cache, use Chrome, reinstall, check KDP login, wait 20-30 min, then contact support.",
    "pause advertising": "Pause books or marketplaces in the Adigy dashboard.",
    "payment fails": "Account pauses until payment is updated.",
    "incorrect sales data": "Due to sync delays, KENP differences, returns, or currency conversion. Check weekly/monthly data."
}

def extract_relevant_info(query, faq_data):
    query = query.lower().strip()
    matched_info = []
    for key, value in faq_data.items():
        if any(word in query for word in key.split()):
            matched_info.append(value)
    return " ".join(matched_info) if matched_info else "I’m not sure about that. Could you provide more details or contact support@Adigy.ai?"

def get_model_response(user_query, conversation_history=[]):
    # Extract relevant FAQ info based on query
    relevant_info = extract_relevant_info(user_query, FAQ_DATA)
    
    formatted_conversation = (
        SYSTEM_PROMPT + "\n\n"
        "Below is the relevant information for the user’s query:\n"
        f"{relevant_info}\n\n"
        "Conversation History (if any):\n"
    )
    
    if conversation_history:
        for message in conversation_history[-5:]:
            if message["role"] == "user":
                formatted_conversation += f"User: {message['content']}\n"
            else:
                formatted_conversation += f"Assistant: {message['content']}\n"
    
    formatted_conversation += f"\nLatest User Query: {user_query}\nAssistant:"
    
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
st.write("Welcome to Adigy customer support! How can I assist you with your Amazon ads today?")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask about Adigy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_model_response(
                prompt, 
                st.session_state.messages[:-1]
            )
            st.write(response)
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