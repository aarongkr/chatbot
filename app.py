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
You are AdigyAssist, a helpful and friendly support specialist for Adigy, an automated Amazon ads management software for KDP publishers. Use the provided information to answer user queries concisely and accurately in plaintext, using formatting to present the informating in an easily readable way. If the info is insufficient, say "I’m not sure about that" and suggest contacting support@Adigy.ai for complex issues if necessary (e.g., Amazon suspensions, policy violations). Prioritise accurate information above everything.
"""

# Full FAQ data
FAQ_DATA = {
    "what is adigy": "Adigy (formerly Adsology) is an automated Amazon ads management software designed for KDP publishers. It optimizes Amazon advertising campaigns to improve performance and returns, making it particularly beneficial for publishers with lower ad spend or beginners.",
    "difference between adigy and adsdroid": "Adigy is a self-service software tool ideal for lower ad spend or beginner publishers. AdsDroid is a premium 'done-for-you' agency service for advanced publishers with higher ad spend, featuring a dedicated account manager for hands-on support and customization, unlike the automated Adigy platform.",
    "why transition to adigy": "Adsology is transitioning to Adigy as part of a rebranding process to evolve our platform and services. Account functionality remains unchanged; only the name is updated to Adigy.",
    "fiction or non-fiction": "Adigy works for both fiction and non-fiction books with tailored strategies. Fiction benefits more from category and product targeting, while non-fiction performs well with keyword-focused campaigns.",
    "cost": "Adigy’s standard subscription costs $249 per month, plus a 3.3% fee on ad spend exceeding $2,000. It also offers affiliate commission opportunities through its program.",
    "roi": "Return on investment varies by book and category. Most users see ACOS (Advertising Cost of Sale) improve within 3-4 weeks as data accumulates, with optimal results around month 3. New books with few reviews may take longer to reach profitability due to ranking and visibility needs.",
    "free trial": "Adigy does not offer a free trial, but provides a 30-day money-back guarantee if you’re unsatisfied within the first 30 days of your subscription.",
    "money-back guarantee": "Yes, Adigy offers a 30-day money-back guarantee. If unsatisfied within 30 days of subscribing, contact support to request a full refund.",
    "cancel subscription": "Upon cancellation, your subscription remains active until the billing period ends. To stop ads immediately: 1. Manually pause campaigns in the Amazon Ads console, 2. Use the 'Master Undo' button to revert your account to its pre-Adigy state, 3. Set marketplaces to 'Off' in Adigy settings.",
    "affiliate program": "Join the affiliate program at https://Adigy.ai/partner for 25% lifetime commissions. Referring 4 people grants a 100% discount on your subscription going forward.",
    "setup": "Set up Adigy by connecting your Amazon KDP account via 'Login with Amazon,' installing the free Chrome extension, selecting books to manage, and setting marketplace budgets in the Adigy dashboard at Adigy.ai. No forms or calls needed—just click 'Start Today.'",
    "sync time": "Initial syncing typically takes less than 1 hour, but can extend to 6 hours for large accounts or if Amazon’s servers are overloaded.",
    "us marketplace connect": "If you can’t connect to the US marketplace, it’s likely a temporary authentication issue. Log out of Amazon and Adigy, clear your browser cache, then log back in. If unresolved, contact support with screenshots.",
    "sync stuck": "If syncing stalls, refresh the page first (it might be a UI glitch). If it persists, clear cache/cookies, re-login to Amazon in Chrome with the Adigy extension, or try another browser (Chrome recommended). Contact support if the issue continues.",
    "chrome extension": "Yes, the Chrome extension is essential. It syncs KDP royalty data into Adigy, combining it with ad spend data to provide net profitability insights.",
    "other browsers": "The Adigy extension is designed for Google Chrome only and may not work with browsers like Safari, Brave, or Edge. Use Chrome for the best experience.",
    "permissions": "Adigy requires connection to your Amazon KDP and Advertising accounts, with editor access granted to your Amazon Ads account during onboarding. Ensure Amazon’s ad terms are accepted and billing details are added.",
    "editor access": "To grant editor access: 1. Go to https://advertising.amazon.com/user/management/invite, 2. Enter Adigy@Adigy.ai, 3. Select 'Editor' permission, 4. Press 'Select all' for Country Access, 5. Click 'Invite users.'",
    "not eligible books": "Books showing as 'not eligible' or 'out of stock' despite availability may reflect Amazon API limitations or temporary data issues. Contact support with ASINs for a manual fix if books are active.",
    "duplicate listings": "Duplicate listings occur when different formats (paperback, hardcover, Kindle) exist. They’re grouped for easier management. Contact support with ASINs if clarification is needed.",
    "email notifications": "Receiving hundreds of emails from Amazon when starting Adigy is normal due to campaign setup notifications. Reduce them by adjusting Amazon Ads notification preferences or setting email filters to delete automatically.",
    "set budget": "Set monthly budgets for each marketplace (e.g., US, UK, CA) in the Marketplace and Budget section of the Adigy dashboard. Budgets apply across all campaigns and books in that marketplace.",
    "minimum budget": "The minimum budget per marketplace is 100 units in the local currency (e.g., $100 USD, £100 GBP).",
    "recommended budget": "While $100 per marketplace is the minimum, $500-$1,000 is recommended for effective results, especially with multiple books or to maximize visibility, allowing more testing and optimization.",
    "budget per book": "Budgets are set per marketplace, not per book or the entire account. Each marketplace (US, UK, CA, etc.) has its own budget.",
    "individual book budgets": "Individual book budgets aren’t available; budgets are marketplace-level. Limit a book’s spend by pausing it in specific marketplaces or restricting advertised formats (e.g., paperback only).",
    "stay within budget": "Yes, Adigy optimizes ad spend to stay within your set budget, adjusting bids and allocating funds to promising targets to prevent overspending.",
    "low ad spend": "Lower-than-set ad spend is normal initially. Adigy starts conservatively, gathering data on keyword/ASIN performance, increasing spend as profitable opportunities emerge. It also reduces spend during low-demand periods like post-Christmas.",
    "allocate budget": "For most publishers, allocate 60-70% of your budget to the US (highest sales potential), 20-25% to UK/CA, and the rest to other marketplaces, adjusting based on your books and audience.",
    "ad cost in fee": "No, the $249/month fee covers Adigy software only. Amazon bills ad spend separately through your Advertising account.",
    "budget allocation": "Adigy dynamically allocates budget to targets (keywords/ASINs) with better performance, using an algorithm factoring historical data, ACOS, and conversion rates to optimize across campaigns.",
    "spend fluctuations": "Daily ad spend fluctuations are normal due to: 1. Bid adjustments based on performance, 2. Seasonal competition changes (e.g., holidays), 3. Conversion rate shifts (reviews/pricing), 4. Amazon auction dynamics. These typically balance monthly.",
    "holiday budget": "Adigy adjusts budgets for Christmas, cutting spend in the last week of December (low conversions) and boosting it in weeks 2 and 3 (high demand).",
    "existing campaigns": "Adigy integrates with your Amazon Ads account, taking over and optimizing existing campaigns for managed books by adjusting bids and budgets.",
    "new campaigns": "Adigy creates new campaigns to expand reach, including: Auto campaigns (product/keyword discovery), Broad campaigns (research), Product Targeting (competitor sales), Brand Defense (brand protection), and Gold Panning (low CPC sniping).",
    "many campaigns": "Multiple new campaigns, especially Gold Panning, are created initially for keyword discovery and optimization, staying within your budget to avoid overspending.",
    "campaign naming": "Campaign names follow: Book Title Abbreviation-Ad Type-Campaign Purpose-ASIN-Format-Unique Identifier (e.g., TI1E-SP-GP-B0DD86533Y-Paperback-ZPOMTS). 'TI1E' is from the title, 'SP' is Sponsored Products, 'GP' is Gold Panning, etc., for tracking.",
    "specific formats": "Yes, select formats (paperback, Kindle, hardcover) to advertise per book on its Adigy page using format toggles.",
    "stop formats": "Pause advertising for specific formats (Kindle, paperback, hardcover) on the book’s detail page in Adigy using pause buttons.",
    "top 10 targets": "Top 10 Targets are up to 10 keywords and 10 ASINs you manually select per book as key advertising focuses. Add them to prioritize budget and attention, enhancing promotion.",
    "more than 10 targets": "You can add more than 10 Top Targets, but we recommend sticking to 10 highly relevant keywords/ASINs for focused, effective advertising.",
    "exact negatives": "Exact Negatives block ads for a specific search term only (e.g., 'dog training book' won’t block 'dog training books'), preventing spend on irrelevant searches.",
    "phrase negatives": "Phrase Negatives block ads for any term containing the phrase (e.g., 'dog training' blocks 'dog training books,' 'best dog training'), reducing unprofitable spend.",
    "blockers in opportunities": "Relevant targets may appear as blockers in the Opportunities tab if they perform poorly (high ACOS, many clicks/no sales). Unblock them if you believe they’re valuable; the system uses historical data, but you have control.",
    "gold panning": "Gold Panning (GP) campaigns snipe low-bid ad opportunities with: broad match keywords (generic, may seem unrelated), low bids (~$0.11), research focus (find low-cost conversions), low ACOS (~19%), safety (low risk), high keyword volume, no manual management, and hidden UI to avoid clutter.",
    "turn off gold panning": "Yes, disable Gold Panning campaigns in the Advanced settings subsection if you prefer not to use this strategy.",
    "random keywords": "Unusual or random keywords in Gold Panning campaigns are intentional for research, aiming to identify profitable, less obvious search terms.",
    "edit in amazon": "You can edit campaigns in the Amazon Ads Console, but minimal intervention is recommended. Frequent manual changes to bids, budgets, or targets disrupt Adigy’s learning process, potentially reducing results.",
    "new book": "New books are added to the Unmanaged section. Toggle Adigy ON, select formats and markets, and it creates campaigns based on budget and book traits. Books under 2 months old get special launch campaign treatment.",
    "video ads": "Adigy manages existing Sponsored Brands Video Ads, prioritizing their exposure, but video ad creation must be done manually in the Amazon Ads console.",
    "ad types": "Adigy primarily supports Sponsored Products ads (most effective for KDP) and can manage manually created Sponsored Brands Product Collection and Video ads.",
    "multiple marketplaces": "Adigy optimizes ads across 11 marketplaces (US, UK, CA, AU, DE, FR, IT, ES, NL, MX, IN), with separate budgets and campaign management per marketplace.",
    "bid adjustments": "Adigy adjusts bids and budgets up to 6 times daily for large accounts or once daily for smaller ones, designed as a 'set it and forget it' tool.",
    "manage specific books": "Yes, you control which books Adigy manages, selecting specific titles and leaving others unmanaged to tailor your ad strategy.",
    "rename campaigns": "Rename Adigy-created campaigns in the Amazon Ads console for organization without affecting management.",
    "stop emails": "Reduce Amazon Ads email notifications by adjusting settings in the Advertising platform or setting up email filters to manage them automatically.",
    "results time": "Initial results may appear in days, but noticeable improvements take 2-3 weeks as data is gathered. Full optimization requires about 3 months, especially for new books.",
    "metrics": "Adigy focuses on optimizing break-even ACOS (Advertising Cost of Sale), dynamically adjusting bids and budgets to balance ad spend with royalty income.",
    "high acos initially": "High ACOS in the first 2-3 weeks is normal during the discovery phase as Adigy tests keywords/targets to find effective strategies.",
    "reviews needed": "For effective advertising: 5-10 reviews (minimum viable), 15+ (good), 30+ (strong potential), 50-100+ (ideal for max conversions). Fewer than 5 reviews means higher ACOS and limited campaigns.",
    "high acos popular category": "High ACOS in a popular category suggests conversion issues. Check: 1. Book cover quality, 2. Description clarity/appeal, 3. Review quantity/quality, 4. Category fit, 5. Pricing competitiveness, 6. A+ content quality, 7. Sample quality, 8. Best seller badge, 9. Bonuses, 10. 5+ UGC videos (US only).",
    "improve performance": "Boost ad performance by: getting 10-50+ reviews, optimizing description with compelling copy, enhancing A+ content with visuals/info, ensuring a professional cover, selecting relevant targets/keywords, adding negative keywords, refining categories.",
    "seasonal books": "For seasonal books: 1. Start ads 4-6 weeks before peak, 2. Boost budget 2 months prior, 3. Add seasonal Top 10 Targets, 4. Pause post-season. Adigy detects patterns and adjusts bids.",
    "seasonal peaks": "Yes, Adigy adapts to seasonal demand (e.g., Q4), adjusting budgets and bids to maximize performance during peak sales periods.",
    "good acos": "Good ACOS varies: Paperbacks (25-45% break-even), Kindle (30-70% depending on price), Hardcovers (20-30%). Higher ACOS (100%+) is okay during launches; aim below break-even for established books.",
    "target acos": "Adigy targets a profitable break-even ACOS per book, balancing spend and royalties. For new launches, it allows higher ACOS to boost visibility/ranking.",
    "bid changes": "Frequent bid changes are part of optimization, raising bids on performing keywords and lowering them on underperformers based on performance and market conditions.",
    "low bids good keywords": "Lower bids on low-ACOS keywords are strategic, considering budget allocation, relevance, and campaign goals, to test new opportunities or optimize overall performance.",
    "new book launches": "Adigy detects new books and enters launch mode for the first 2 months, prioritizing visibility and sales velocity with aggressive bidding and budget allocation.",
    "negative keywords": "Yes, Adigy’s AI auto-adds negative keywords based on performance data to cut wasted spend on irrelevant/underperforming terms.",
    "add negatives": "Manually add negative keywords/ASINs in Adigy’s 'Negatives' tab. Review Negative Suggestions after clicking Add Negatives buttons, then add to your lists.",
    "low budgets": "Campaigns with low budgets (e.g., $1.01/day) are lower priority or underperforming, per Adigy’s strategy to focus spend on promising targets.",
    "ineligible book": "An 'ineligible' book means Amazon Ads restricts new campaigns for it due to system factors. Adigy may still manage existing campaigns.",
    "account suspended": "Adigy doesn’t cause suspensions; it’s a verified Amazon Ads partner. Suspensions stem from: 1. Prohibited content, 2. Unusual activity, 3. Policy violations. Contact Amazon Ads support; pause Adigy and seek guidance from support@Adigy.ai.",
    "suspension": "If suspended/terminated, pause your Adigy subscription immediately. Contact Amazon Ads support to resolve; Adigy support offers guidance but can’t intervene.",
    "policy violations": "Adigy complies with Amazon policies. For violations, address them with Amazon directly; Adigy support can explain software use but not resolve violations.",
    "book details change": "Yes, changes impact performance: 1. Better covers/descriptions raise conversions, 2. Price shifts affect competitiveness/margins, 3. Category changes alter ad visibility. Adigy adjusts over time with new data.",
    "support": "For support, reply to support@Adigy.ai emails or use the website contact form. For urgent issues, schedule a call via the booking link in support emails.",
    "ads still running": "After cancellation, ads run until the billing period ends. Stop them by: 1. Pausing in Amazon Ads console, 2. Using 'Master Undo,' 3. Setting marketplaces to 'Off' in Adigy.",
    "cancel refund": "Cancel via 'Account Settings' in the Adigy dashboard. For refunds within 30 days, email support@Adigy.ai, referencing the guarantee policy.",
    "extension sync": "If the Chrome extension isn’t syncing: 1. Refresh page, 2. Clear cache/cookies, 3. Ensure Chrome use, 4. Reinstall extension, 5. Verify KDP login in same browser, 6. Wait 20-30 min (Amazon server delays). Contact support with screenshots if unresolved.",
    "pause advertising": "Pause advertising for specific books or marketplaces directly in the Adigy dashboard.",
    "payment fails": "If payment fails, your Adigy account may pause until billing is updated and payment succeeds.",
    "incorrect sales data": "Sales data discrepancies arise from: 1. Sync delays (KDP, Amazon Ads, Adigy), 2. KENP counting differences, 3. Returns/cancellations, 4. Currency conversion variances. Compare weekly/monthly data for accuracy."
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