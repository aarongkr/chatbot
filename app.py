import os
import streamlit as st
import requests
import json
from dotenv import load_dotenv
import re
import logging
from functools import lru_cache
import time

# Setup logging
logging.basicConfig(level=logging.INFO, filename="adigy_assist.log")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
MODEL_URL = os.getenv("MODEL_URL", "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2")
HUGGINGFACE_HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}", "Content-Type": "application/json"}
BREVO_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_HEADERS = {"api-key": BREVO_API_KEY, "Content-Type": "application/json"}

# Load FAQ from file (save FAQ_DATA as faq_data.json first)
try:
    with open("faq_data.json", "r") as f:
        FAQ_DATA = json.load(f)
except FileNotFoundError:
    FAQ_DATA = {"what is adigy": "Adigy (formerly Adsology) is an automated Amazon ads management software designed for Kindle Direct Publishing (KDP) publishers—those who self-publish books on Amazon. It optimizes Amazon advertising campaigns to improve performance and returns by adjusting bids, targeting, and budgets, making it especially useful for publishers with lower ad spend (e.g., under $2,000/month) or beginners new to Amazon ads.",
    "difference between adigy and adsdroid": "Adigy is a self-service software tool for publishers with lower ad spend or beginners, automating campaign management. AdsDroid is a premium 'done-for-you' agency service for advanced publishers with higher ad spend (e.g., over $5,000/month), providing a dedicated account manager for personalized monitoring and customization, offering more hands-on support than Adigy’s automated platform.",
    "why transition to adigy": "Adsology is rebranding to Adigy to reflect platform evolution and service enhancements. Your account functionality (e.g., campaign settings, budgets) remains identical; only the name changes to Adigy, aligning with our growth strategy.",
    "fiction or non-fiction": "Adigy supports both fiction and non-fiction books with tailored strategies. Fiction benefits from category and product targeting (e.g., ads on similar books), while non-fiction excels with keyword-focused campaigns (e.g., targeting search terms), adapting to each genre’s advertising strengths.",
    "cost": "Adigy costs $249/month, plus a 3.3% fee on ad spend over $2,000 (e.g., $33 for $1,000 extra spend). No free trial is offered, but a 30-day money-back guarantee applies. An affiliate program at https://Adigy.ai/partner provides 25% lifetime commissions.",
    "roi": "Return on investment (ROI) varies by book and category. Most see Advertising Cost of Sale (ACOS—ad spend divided by sales revenue) improve in 3-4 weeks as Adigy gathers data, with optimal results by month 3. New books with few reviews (under 5) take longer due to ranking and visibility challenges—often 4-6 months.",
    "free trial": "No free trial exists for Adigy, but a 30-day money-back guarantee ensures satisfaction. If unhappy within 30 days of subscribing, contact support for a full refund.",
    "money-back guarantee": "Yes, Adigy offers a 30-day money-back guarantee. If unsatisfied for any reason within 30 days of subscribing, email support@Adigy.ai for a full refund, no questions asked.",
    "cancel subscription": "Canceling keeps your subscription active until the billing period ends (e.g., 20 days left). To stop ads immediately: 1. Pause campaigns manually in the Amazon Ads console, 2. Click 'Master Undo' in Adigy to revert to pre-Adigy settings, 3. Set marketplaces to 'Off' in Adigy settings. See 'ads still running' for related info.",
    "affiliate program": "Join at https://Adigy.ai/partner for 25% lifetime commissions on referrals’ subscriptions (e.g., $62.25/month per referral). Referring 4 people covers your $249/month fee, effectively making it free.",
    "setup": "To set up Adigy: connect your Amazon KDP account via 'Login with Amazon,' install the free Chrome extension, select books to manage in the dashboard, and set marketplace budgets (e.g., US, UK) at Adigy.ai. No forms or calls needed—start by clicking 'Start Today.' Requires editor access (see 'editor access').",
    "sync time": "Initial syncing takes under 1 hour typically, but up to 6 hours for very large accounts (e.g., 100+ books) or if Amazon’s servers are slow. Delays are rare but possible during high-traffic periods like holidays.",
    "us marketplace connect": "US marketplace connection issues are usually temporary authentication errors. Log out of Amazon and Adigy, clear browser cache, then log back in. If it persists (e.g., after 2 tries), email support@Adigy.ai with screenshots of the error.",
    "sync stuck": "If syncing stalls, refresh the page (could be a UI glitch). If unresolved, clear cache/cookies, re-login to Amazon in Chrome with the Adigy extension, or switch browsers (Chrome recommended). Persistent issues (e.g., over 6 hours) require support contact—see 'support.'",
    "chrome extension": "Yes, the Chrome extension is required. It syncs Kindle Direct Publishing (KDP) royalty data into Adigy, merging it with ad spend to calculate net profitability (e.g., profit after ad costs), essential for performance insights.",
    "other browsers": "The Adigy extension works only with Google Chrome and may fail on Safari, Brave, Edge, etc., due to compatibility. Use Chrome for optimal syncing and functionality.",
    "permissions": "Adigy needs access to your Amazon KDP account (for royalties) and Amazon Advertising account (for ads), requiring editor access during onboarding (see 'editor access'). You must accept Amazon’s ad terms and add billing details in your Amazon account.",
    "editor access": "Grant editor access: 1. Visit https://advertising.amazon.com/user/management/invite, 2. Enter Adigy@Adigy.ai, 3. Choose 'Editor' permission, 4. Click 'Select all' for Country Access (e.g., US, UK), 5. Hit 'Invite users.' This allows Adigy to manage campaigns.",
    "not eligible books": "Books marked 'not eligible' or 'out of stock' despite availability stem from Amazon API limits or data glitches (e.g., stock updates lagging). If confirmed active on Amazon, contact support@Adigy.ai with ASINs (e.g., B0DD86533Y) for a manual fix.",
    "duplicate listings": "Duplicates arise from multiple formats (paperback, hardcover, Kindle) of the same book. Adigy groups them for management ease. If confused (e.g., same ASIN twice), contact support with specific ASINs for clarification.",
    "email notifications": "Hundreds of Amazon emails are normal at Adigy startup due to campaign creation/update notices. Reduce via Amazon Ads console notification settings or email filters to auto-delete (e.g., filter 'Amazon Advertising'). See 'stop emails.'",
    "set budget": "Set monthly budgets per marketplace (e.g., $500 for US, £200 for UK) in Adigy’s Marketplace and Budget dashboard section. This covers all campaigns/books in that marketplace, adjustable anytime.",
    "minimum budget": "The minimum budget is 100 units per marketplace in its currency (e.g., $100 USD, £100 GBP, €100 EUR), ensuring basic campaign operation.",
    "recommended budget": "Start at $100/marketplace minimum, but $500-$1,000 per marketplace is recommended for effective results, especially with multiple books or high visibility goals, enabling broader targeting and faster optimization.",
    "budget per book": "Budgets are set per marketplace (e.g., US, UK), not per book or account-wide. Each marketplace operates independently—e.g., $500 US budget covers all US books.",
    "individual book budgets": "No per-book budgets exist; control is at the marketplace level. Limit spend by pausing a book in specific marketplaces (e.g., UK off) or restricting formats (e.g., paperback only—see 'specific formats').",
    "stay within budget": "Yes, Adigy ensures ad spend stays within your set budget by adjusting bids and prioritizing high-performing targets, preventing overspending even with multiple campaigns.",
    "low ad spend": "Lower-than-set spend is normal early on as Adigy conservatively tests keywords/ASINs. Spend rises as profitable targets emerge (e.g., after 2 weeks). It also drops during low-demand times (e.g., post-Christmas) to save costs.",
    "allocate budget": "Typically allocate 60-70% to the US (highest sales volume), 20-25% to UK/CA, and 5-10% to others (e.g., DE, AU), adjusting based on your books’ audience (e.g., UK-heavy for British fiction).",
    "ad cost in fee": "No, the $249/month fee is for Adigy software access only. Amazon bills ad spend separately via your Advertising account (e.g., $300 ad spend = $300 Amazon charge).",
    "budget allocation": "Adigy dynamically allocates budget to top-performing targets (keywords/ASINs) using an algorithm factoring historical performance, ACOS, and conversion rates, optimizing across all campaigns daily.",
    "spend fluctuations": "Daily spend shifts are normal due to: 1. Bid adjustments from performance data, 2. Seasonal competition (e.g., holiday spikes), 3. Conversion changes (e.g., new reviews), 4. Amazon auction dynamics. Balances out monthly.",
    "holiday budget": "Adigy adjusts for Christmas: reduces spend in the last week of December (low conversions) and boosts weeks 2-3 (high demand), optimizing holiday performance automatically.",
    "existing campaigns": "Adigy integrates with your Amazon Ads account, taking over existing campaigns for managed books, optimizing bids and budgets for better performance (e.g., lowering ACOS).",
    "new campaigns": "Adigy auto-creates campaigns: Auto (product/keyword discovery), Broad (research), Product Targeting (competitor sales), Brand Defense (protect brand), Gold Panning (low CPC sniping—see 'gold panning') to expand reach.",
    "many campaigns": "Multiple campaigns, especially Gold Panning, launch at start for keyword discovery and optimization, respecting your budget to avoid overspending (e.g., $500 cap holds).",
    "campaign naming": "Names use: Book Abbreviation-Ad Type-Purpose-ASIN-Format-ID (e.g., TI1E-SP-GP-B0DD86533Y-Paperback-ZPOMTS). 'TI1E' is title, 'SP' is Sponsored Products, 'GP' is Gold Panning, aiding tracking.",
    "specific formats": "Yes, choose formats (paperback, Kindle, hardcover) to advertise per book on its Adigy page with toggles—e.g., paperback only, Kindle off.",
    "stop formats": "Pause formats (e.g., Kindle, hardcover) on the book’s Adigy detail page using pause buttons next to each format, stopping their ads instantly.",
    "top 10 targets": "Top 10 Targets let you pick up to 10 keywords and 10 ASINs (20 total) per book as priority ad focuses. Add via Adigy to direct budget and boost promotion—e.g., 'fantasy novel' or competitor ASIN.",
    "more than 10 targets": "You can exceed 10 Top Targets, but we suggest 10 highly relevant keywords/ASINs for focused ads (e.g., avoid diluting with 20+ vague terms).",
    "exact negatives": "Exact Negatives block only the exact term—e.g., 'dog training book' stops that phrase but not 'dog training books,' saving spend on irrelevant clicks.",
    "phrase negatives": "Phrase Negatives block any term with the phrase—e.g., 'dog training' stops 'dog training books,' 'best dog training,' cutting unprofitable searches.",
    "blockers in opportunities": "Relevant targets may be blockers in Opportunities if they underperform (e.g., high ACOS, 50 clicks/no sales). Unblock if you think they’re key; Adigy uses past data, but you override.",
    "gold panning": "Gold Panning (GP) campaigns target low-bid ad slots with: broad match keywords (generic, e.g., 'book'), low bids (~$0.11), research goal (find cheap conversions), low ACOS (~19%), safety (low risk), high keyword volume, no manual tweaks, hidden UI to reduce clutter.",
    "turn off gold panning": "Disable Gold Panning in Adigy’s Advanced settings if you don’t want this low-bid research strategy—e.g., preferring direct sales focus.",
    "random keywords": "Unusual/random keywords in Gold Panning (e.g., 'gift') are for research, seeking profitable, less obvious terms. They’re intentional, not errors.",
    "edit in amazon": "You can edit campaigns in Amazon Ads Console, but minimal changes are best. Frequent manual bid/budget/target edits disrupt Adigy’s learning (e.g., 2-3 weeks needed), risking poorer results.",
    "new book": "New books auto-appear in Unmanaged. Toggle Adigy ON, pick formats/markets, and it crafts campaigns per budget/book traits. Books under 2 months get launch mode—see 'new book launches.'",
    "video ads": "Adigy manages existing Sponsored Brands Video Ads, prioritizing exposure, but you must create them manually in Amazon Ads console—e.g., upload a 30-second book trailer.",
    "ad types": "Adigy focuses on Sponsored Products (best for KDP) and manages manually created Sponsored Brands Product Collection and Video ads—e.g., a video ad you set up.",
    "multiple marketplaces": "Adigy optimizes across 11 KDP marketplaces (US, UK, CA, AU, DE, FR, IT, ES, NL, MX, IN) with separate budgets/campaigns—e.g., $500 US, £200 UK.",
    "bid adjustments": "Adigy updates bids/budgets up to 6x/day (large accounts) or daily (small accounts), acting as a 'set it and forget it' tool for ongoing optimization.",
    "manage specific books": "Yes, pick which books Adigy manages in the dashboard, leaving others unmanaged—e.g., advertise only 3 of 10 titles.",
    "rename campaigns": "Rename Adigy campaigns in Amazon Ads console (e.g., 'TI1E-SP' to 'Fantasy-SP') for organization; it doesn’t affect Adigy’s management.",
    "stop emails": "Cut Amazon Ads email volume by tweaking notification settings in the platform (e.g., uncheck 'campaign updates') or using email filters to archive/delete—e.g., filter 'Amazon Advertising.'",
    "results time": "Some see results in days, but 2-3 weeks is typical for noticeable improvements as data builds. Full optimization takes ~3 months, longer for new books (e.g., 4-6 months).",
    "metrics": "Adigy optimizes for break-even ACOS (ad spend/sales revenue), adjusting bids/budgets to align ad costs with royalties—e.g., targeting 30% ACOS for Kindle.",
    "high acos initially": "High ACOS in the first 2-3 weeks is expected during discovery as Adigy tests keywords/targets—e.g., 80% ACOS dropping to 40% after optimization.",
    "reviews needed": "Effective ads need: 5-10 reviews (minimum), 15+ (good), 30+ (strong), 50-100+ (ideal for max conversions). Under 5 reviews means higher ACOS and fewer campaign options.",
    "high acos popular category": "High ACOS in a popular category signals conversion issues. Check: 1. Cover quality/professionalism, 2. Description clarity/appeal, 3. Review count/quality, 4. Category fit, 5. Pricing (competitive/discounts), 6. A+ content quality, 7. Sample quality, 8. Best seller badge, 9. Bonuses (e.g., freebies), 10. 5+ UGC videos (US only). See 'improve performance.'",
    "improve performance": "Boost ads by: getting 10-50+ reviews, optimizing description (benefit-driven), enhancing A+ content (visuals/info), ensuring pro cover, picking relevant targets/keywords, adding negatives (see 'add negatives'), refining categories—e.g., switch to narrower niche.",
    "seasonal books": "For seasonal books: 1. Start ads 4-6 weeks pre-peak (e.g., Halloween by September), 2. Raise budget 2 months before, 3. Add seasonal Top 10 Targets (e.g., 'Christmas gift'), 4. Pause post-season. Adigy adjusts bids for patterns.",
    "seasonal peaks": "Yes, Adigy adapts to peaks like Q4 (Oct-Dec), tweaking budgets/bids to maximize sales—e.g., higher bids in November, lower in late December.",
    "good acos": "Good ACOS by format: Paperbacks (25-45% break-even), Kindle (30-70% per price, e.g., $2.99 vs. $9.99), Hardcovers (20-30%). Launches may hit 100%+ for visibility; aim below break-even for established books.",
    "target acos": "Adigy targets break-even ACOS (e.g., 30% for Kindle) to balance spend/royalties. For new launches, it allows higher ACOS (e.g., 80%) for visibility/ranking—see 'new book launches.'",
    "bid changes": "Frequent bid shifts optimize based on performance/market—e.g., upping bids on 'fantasy novel' (10 sales) and cutting 'book' (no sales)—maximizing ROI daily.",
    "low bids good keywords": "Low bids on low-ACOS keywords are strategic, balancing budget, relevance, and goals—e.g., testing new terms or spreading funds across campaigns.",
    "new book launches": "Adigy detects new books (<2 months) and uses launch mode, aggressively bidding/allocating budget for visibility/sales velocity—e.g., 100% ACOS to boost rankings initially.",
    "negative keywords": "Adigy’s AI auto-adds negative keywords from performance data—e.g., 'free book' if it wastes spend—reducing irrelevant clicks.",
    "add negatives": "Manually add negatives in Adigy’s 'Negatives' tab. Click Add Negatives, review suggestions (e.g., 'dog training'), and add to keyword/ASIN lists—e.g., block competitor ASIN B012345678.",
    "low budgets": "Low budgets (e.g., $1.01/day) mark underperforming/lower-priority campaigns, focusing spend on better targets—e.g., a keyword with no sales after 100 clicks.",
    "ineligible book": "'Ineligible' means Amazon Ads blocks new campaigns for that book (e.g., policy or stock issues). Adigy may still manage existing ones—check with support.",
    "account suspended": "Adigy doesn’t cause suspensions; it’s an Amazon Ads partner following policies. Causes: 1. Prohibited content (e.g., banned genres), 2. Odd activity (e.g., rapid changes), 3. Violations. Contact Amazon Ads support; pause Adigy—see 'suspension.'",
    "suspension": "For suspension/termination, pause Adigy subscription immediately. Contact Amazon Ads support to fix; Adigy support (support@Adigy.ai) guides but can’t intervene—e.g., can’t lift bans.",
    "policy violations": "Adigy adheres to Amazon rules. For violations (e.g., ad content flags), resolve with Amazon directly; Adigy support clarifies software use but can’t fix—e.g., explain bid adjustments.",
    "book details change": "Yes, changes affect ads: 1. Better covers/descriptions lift conversions (e.g., 2% to 5%), 2. Price shifts alter margins/competitiveness, 3. Category changes shift visibility. Adigy adapts with new data over weeks.",
    "support": "Get help by replying to support@Adigy.ai emails or using the website form. For urgent issues (e.g., sync failure), book a call via the link in support emails—expect 24-48 hour replies.",
    "ads still running": "Post-cancellation, ads run until billing ends (e.g., 15 days left). Stop by: 1. Pausing in Amazon Ads console, 2. Using 'Master Undo' to revert, 3. Setting marketplaces 'Off' in Adigy—see 'cancel subscription.'",
    "cancel refund": "Cancel in 'Account Settings' on the Adigy dashboard (follow prompts). For refunds within 30 days, email support@Adigy.ai per the guarantee—e.g., 'Refund request, subscribed March 1.'",
    "extension sync": "Fix extension sync issues: 1. Refresh page, 2. Clear cache/cookies, 3. Confirm Chrome (others unsupported), 4. Reinstall extension, 5. Ensure KDP login in same browser, 6. Wait 20-30 min (server lag). If stuck, send screenshots to support@Adigy.ai.",
    "pause advertising": "Pause ads for books or marketplaces in the Adigy dashboard—e.g., toggle US off or pause a paperback—stopping spend instantly.",
    "payment fails": "Failed payments may pause your Adigy account until billing updates and succeeds—e.g., card expired, retry with new card in dashboard.",
    "incorrect sales data": "Sales discrepancies come from: 1. Sync delays (KDP/Ads/Adigy, e.g., 24-hour lag), 2. KENP (Kindle page reads) counting diffs, 3. Returns/cancellations, 4. Currency conversions (e.g., £ to $). Use weekly/monthly data for accuracy."
}

SYSTEM_PROMPT = """
You are AdigyAssist, a helpful and friendly support specialist for Adigy, an automated Amazon ads management software for KDP publishers. Use the provided information to answer user queries concisely and accurately in plaintext, using bullet points or numbered lists only when necessary for clarity. Do not repeat the query, conversation history, or input structure in your response — provide only the answer. Prioritize accurate information above all. If the info is insufficient, say "I’m not sure about that" and suggest contacting support@Adigy.ai for complex issues if necessary (e.g., Amazon suspensions, policy violations). Try to layout the answer in a nice way to improve readability where possible
"""

def extract_relevant_info(query, faq_data):
    query = query.lower().strip()
    exact_matches = []
    matched_info = []
    for key, value in faq_data.items():
        key_words = key.split()
        query_words = query.split()
        if query == key:
            exact_matches.append(value)
        elif all(word in query_words for word in key_words):
            matched_info.append(value)
        elif any(word in query for word in key_words):
            matched_info.append(value)
    if exact_matches:
        return " ".join(exact_matches)
    if matched_info:
        return " ".join(matched_info[:2])
    return "I’m not sure about that. Try rephrasing your question or contact support@Adigy.ai for help."

def clean_response(text):
    text = re.sub(r'.*Assistant:', '', text, flags=re.DOTALL)
    text = re.sub(r'Below is the relevant information.*?:\n', '', text, flags=re.DOTALL)
    text = re.sub(r'Conversation History.*?:\n', '', text, flags=re.DOTALL)
    text = re.sub(r'Latest User Query.*?:\n', '', text, flags=re.DOTALL)
    return text.strip()

@lru_cache(maxsize=100)
def get_cached_response(query):
    return get_model_response(query)

def get_model_response(user_query, conversation_history=[]):
    if not HUGGINGFACE_API_KEY:
        return "Error: API key not configured. Contact support@Adigy.ai."
    
    logger.info(f"Processing query: {user_query}")
    relevant_info = extract_relevant_info(user_query, FAQ_DATA)
    if "I’m not sure" not in relevant_info and user_query.lower().strip() in FAQ_DATA:
        return FAQ_DATA[user_query.lower().strip()]
    
    formatted_conversation = (
        SYSTEM_PROMPT + "\n\n"
        "Below is the relevant information for the user’s query:\n"
        f"{relevant_info}\n\n"
        "Conversation History (if any):\n"
    )
    if conversation_history:
        for message in conversation_history[-5:]:
            formatted_conversation += f"{message['role'].capitalize()}: {message['content']}\n"
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
    
    for attempt in range(3):
        try:
            response = requests.post(MODEL_URL, headers=HUGGINGFACE_HEADERS, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                logger.info(f"Generated text: {generated_text}")
                return clean_response(generated_text)
            return "I apologize, but I encountered an error processing your query. Please try again."
        except requests.Timeout:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return "Request timed out. Please try again later or contact support@Adigy.ai."
        except requests.HTTPError as e:
            if e.response.status_code == 429 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return f"API error (Status {e.response.status_code}). Contact support@Adigy.ai."
        except Exception as e:
            return f"Unexpected error: {str(e)}. Please try again or contact support@Adigy.ai."

def send_support_email(user_query, conversation_history):
    if not BREVO_API_KEY:
        return "Error: Brevo API key not configured. Please contact an administrator."

    # Build email content
    email_body = f"Subject: Support Request from AdigyAssist User\n\n"
    email_body += f"Latest Question:\n{user_query}\n\n"
    email_body += "Conversation History (Last 5 Messages):\n"
    if conversation_history:
        for message in conversation_history[-5:]:
            email_body += f"{message['role'].capitalize()}: {message['content']}\n"
    else:
        email_body += "No prior conversation history available.\n"

    # Brevo API payload
    payload = {
        "sender": {"name": "AdigyAssist User", "email": "support@Adigy.ai"},  # Must be a verified sender in Brevo
        "to": [{"email": "aaronmichaelrazey@gmail.com", "name": "Adigy Support"}],
        "subject": "Support Request from AdigyAssist User",
        "textContent": email_body
    }

    try:
        response = requests.post(BREVO_URL, headers=BREVO_HEADERS, json=payload)
        response.raise_for_status()
        logger.info(f"Email sent successfully: {response.status_code}")
        return "Email sent successfully to support@Adigy.ai!"
    except requests.HTTPError as e:
        logger.error(f"Failed to send email: {e.response.status_code} - {e.response.text}")
        return f"Failed to send email: API error (Status {e.response.status_code}). Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return f"Unexpected error sending email: {str(e)}. Please try again later."

# Streamlit UI
st.set_page_config(page_title="Adigy Customer Support", page_icon="📈", layout="centered")
st.title("📈 Adigy Customer Support")
st.write("Welcome to Adigy customer support! How can I assist you with your Amazon ads today?")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(message["content"])
            # Add support button only for the latest assistant message
            if message == st.session_state.messages[-1] and len(st.session_state.messages) > 1:
                if st.button("Contact Support with this Question", key=f"support_{len(st.session_state.messages)}"):
                    user_query = st.session_state.messages[-2]["content"]  # Last user question
                    result = send_support_email(user_query, st.session_state.messages[:-1])
                    st.success(result) if "success" in result.lower() else st.error(result)
        else:
            st.write(message["content"])

if prompt := st.chat_input("Ask about Adigy..."):
    if prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_cached_response(prompt)
                st.markdown(response)
            if st.button("Contact Support with this Question", key=f"support_new_{len(st.session_state.messages)}"):
                result = send_support_email(prompt, st.session_state.messages[:-1])
                st.success(result) if "success" in result.lower() else st.error(result)
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.warning("Please enter a question!")

st.markdown("""
<style>
body { background-color: #1e1e1e; color: #ffffff; }
.stChatMessage { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; background-color: #2b2b2b; color: #ffffff; }
.stChatMessage.user { background-color: #3a3a3a; color: #e0e0e0; }
.stChatMessage.assistant { background-color: #2b2b2b; color: #ffffff; }
.stTextInput > div > div > input { background-color: #3a3a3a; color: #ffffff; border: 1px solid #555555; }
h1, .stMarkdown { color: #ffffff; }
.stSpinner > div > div { color: #ffffff; }
.stButton > button { background-color: #4a4a4a; color: #ffffff; border: 1px solid #555555; }
.stButton > button:hover { background-color: #5a5a5a; }
</style>
""", unsafe_allow_html=True)