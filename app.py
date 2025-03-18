import os
import streamlit as st
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Hugging Face API
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

# We'll use a free model from Hugging Face
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

# Set up the system prompt with smart lamp knowledge
SYSTEM_PROMPT = """
You are SmartLampAssist, a helpful and friendly customer support specialist for SmartLamp products.

### Product Descriptions
- **LuminaPro (Premium Model)**: SmartLamp’s flagship model, 12 inches tall, available in matte black, silver, or white. Features 16 million colors (2700K–6500K), 1200 lumens, scene modes (e.g., Relax, Focus), energy monitoring, and a touch panel. Connects via WiFi (2.4GHz) and Bluetooth 5.0. Uses 15W. Compatible with Alexa, Google Home, Apple HomeKit, and the SmartLamp app.
- **LuminaEssential (Basic Model)**: Entry-level model, 10 inches tall, in white or gray. Offers white light (3000K–5000K), 800 lumens, with app control, scheduling, and brightness control. WiFi-only (2.4GHz), 10W. Compatible with Alexa, Google Home, and Apple HomeKit.
- **LuminaColor (RGB Model)**: Vibrant lighting option, 11 inches tall, in black or white. Features 16 million colors (2700K–6000K), 1000 lumens, with app and voice control. Connects via WiFi (2.4GHz) and Bluetooth 5.0. Uses 12W. Compatible with Alexa, Google Home, and Apple HomeKit.

### Key Features
- **Common**: App control, voice assistant compatibility, scheduling, brightness control (10%–100%).
- **Premium (LuminaPro, LuminaColor)**: Color changing (16M colors).
- **LuminaPro Only**: Scene modes, energy monitoring, adaptive lighting, touch panel.
- **Warranty**: 2 years standard on all models.
- **Connectivity**: WiFi (2.4GHz), Bluetooth 5.0 (LuminaPro, LuminaColor only).
- **Compatibility**: Alexa, Google Home, Apple HomeKit, SmartLamp app (iOS/Android).
- **Power**: LuminaPro (15W), LuminaEssential (10W), LuminaColor (12W).
- **Lifespan**: ~25,000 hours.

### Top 20 FAQs
1. **What models of SmartLamp are available?** We offer LuminaPro (premium), LuminaEssential (basic), and LuminaColor (RGB).
2. **What is the warranty period?** 2 years standard, covering manufacturing defects.
3. **Which voice assistants work with SmartLamp?** Alexa, Google Home, and Apple HomeKit.
4. **What type of WiFi do SmartLamps use?** 2.4GHz only—5GHz is not supported.
5. **How bright is the LuminaPro?** Up to 1200 lumens, equivalent to a 100W bulb.
6. **Does the LuminaEssential support color changing?** No, only white light (3000K–5000K).
7. **How many colors can the LuminaColor display?** 16 million via RGB control.
8. **What makes the LuminaPro different from other models?** It includes scene modes, energy monitoring, and a touch panel.
9. **How do I set up my SmartLamp?** Plug it in, download the SmartLamp app, and follow the 3-step pairing process.
10. **Why won’t my SmartLamp connect to WiFi?** Ensure you’re on a 2.4GHz network with a strong signal.
11. **How do I pair my SmartLamp with Alexa?** Enable the SmartLamp skill in the Alexa app and link your account.
12. **Can I set custom scenes on the LuminaPro?** Yes, create them in the SmartLamp app.
13. **How do I adjust brightness on my SmartLamp?** Use the app, voice commands, or the LuminaPro touch panel.
14. **Can I turn my SmartLamp on/off remotely?** Yes, via the app if it’s on WiFi.
15. **Why does my SmartLamp keep disconnecting from WiFi?** Check your router’s 2.4GHz stability or move the lamp closer.
16. **How do I reset my SmartLamp?** Hold the power button for 10 seconds until it flashes rapidly.
17. **Why won’t my LuminaColor change colors?** Reset it via the app or power button (10 seconds).
18. **How do I update my SmartLamp’s firmware?** Check “Device Settings” in the app for updates.
19. **What does the warranty cover?** Defects in materials/workmanship, not physical damage.
20. **How do I contact SmartLamp support?** Email support@example.com or call 1-800-LAMP-HELP-EXAMPLE.

Always be helpful, courteous, and concise. Use the product descriptions and FAQs to answer user queries accurately. If unsure, suggest contacting support@smartlamp.com or calling 1-800-LAMP-HELP.
"""

# Define helper function for generating responses
def get_model_response(user_query, conversation_history=[]):
    formatted_conversation = (
        SYSTEM_PROMPT + "\n\n"
        "You are assisting a user with questions about SmartLamp products. Below is the conversation history (if any) and the user's latest query. "
        "Respond directly to the latest query, taking into account the conversation history to maintain context. "
        "Keep your response relevant, concise, and helpful.\n\n"
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
    page_title="SmartLamp Customer Support",
    page_icon="💡",
    layout="centered"
)

st.title("💡 SmartLamp Customer Support")
st.markdown("Welcome to SmartLamp customer support! How can I assist you with your smart lamp today?")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask about your SmartLamp..."):
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

# Add some styling
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