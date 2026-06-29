import gradio as gr
import google.generativeai as genai
import json
import re
import os

# 🔑 Replace with your Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# Customer information
customer = {
    "name": "Rahul",
    "due_amount": 10000,
    "days_overdue": 15
}

# System prompt
SYSTEM_PROMPT = f"""
You are an AI debt collection agent for a fintech company.

Customer Name: {customer['name']}
Due Amount: ₹{customer['due_amount']}
Days Overdue: {customer['days_overdue']}

Your job:
- Be polite and professional.
- Understand the customer's situation.
- Try to get a payment commitment.
- Extract payment details.

Always respond ONLY in JSON like this:

{{
  "reply": "message to customer",
  "payment_commitment": "yes/no/maybe",
  "amount_promised": "number or null",
  "date_promised": "date or null"
}}
"""

# Chat memory
chat_history = SYSTEM_PROMPT + f"""

AI: Hello {customer['name']}, your payment of ₹{customer['due_amount']} is overdue. When do you think you'll be able to make the payment?
"""


# Risk scoring function
def get_risk(commitment, amount, date):
    commitment = str(commitment).lower()

    if commitment == "yes" and date not in [None, "null", "N/A"]:
        return "🟢 Low Risk"

    elif commitment == "no":
        return "🔴 High Risk"

    else:
        return "🟡 Medium Risk"


# Chat function
def chat(user_input):
    global chat_history

    chat_history += f"\nUser: {user_input}"

    response = model.generate_content(chat_history)
    raw = response.text

    chat_history += f"\nAI: {raw}"

    # Remove ```json formatting if Gemini adds it
    cleaned = raw.strip()
    cleaned = re.sub(r"```json", "", cleaned)
    cleaned = re.sub(r"```", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)

        reply = data.get("reply", "")
        commitment = data.get("payment_commitment", "unknown")
        amount = data.get("amount_promised", "N/A")
        date = data.get("date_promised", "N/A")

        risk = get_risk(commitment, amount, date)

        return f"""
👤 Customer: {customer['name']}
💬 {reply}

────────────────────
💰 Payment Status: {commitment}
💵 Amount Promised: {amount}
📅 Date Promised: {date}
⚠️ Risk Level: {risk}
"""

    except Exception:
        return raw


# Gradio UI
demo = gr.Interface(
    fn=chat,
    inputs=gr.Textbox(
        placeholder="Type your response here...",
        label="Customer Message"
    ),
    outputs=gr.Textbox(label="AI Collection Agent"),
    title="💰 AI Debt Collection Simulator",
    description=f"""
Customer: {customer['name']}
Due Amount: ₹{customer['due_amount']}
Days Overdue: {customer['days_overdue']}
"""
)

demo.launch()