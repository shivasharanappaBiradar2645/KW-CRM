import os
import json
from flask import current_app
from google import genai
from app.extensions import db
from app.models import Customer, Order, OrderItem, Product, Billing, ShipmentTracking, Communication

def get_gemini_client():
    api_key = current_app.config.get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def gather_customer_context(customer_id):
    """Pulls full context of a customer from the CRM DB for the Gemini model."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return {}

    context = {
        'customer_id': customer.id,
        'company_name': customer.company_name,
        'email': customer.email,
        'contacts': [c.to_dict() for c in customer.contacts],
        'contracts': [ct.to_dict() for ct in customer.contracts],
        'orders': [o.to_dict() for o in customer.orders],
        'recent_communications': [comm.to_dict() for comm in customer.communications[-5:]]
    }
    return context


def process_customer_complaint(communication_id):
    """
    Analyzes an incoming complaint/communication using Gemini LLM:
    1. Pulls full customer, order, billing, and shipment history from CRM DB.
    2. Uses Gemini to analyze the complaint, generate an automated response draft/action plan,
       and produce a clear summary for management.
    3. Saves automated response & issue summary back to CRM Communications timeline.
    """
    comm = Communication.query.get(communication_id)
    if not comm:
        return None

    customer_context = gather_customer_context(comm.customer_id)
    client = get_gemini_client()

    prompt = f"""
You are an expert AI CRM Customer Support Assistant for KW CRM.
Analyze the following customer complaint/inquiry and the full background context pulled from our CRM database.

[CUSTOMER COMPLAINT]
Channel: {comm.channel}
Subject: {comm.subject or 'No Subject'}
Message Body: {comm.body}

[CRM BACKGROUND CONTEXT]
{json.dumps(customer_context, indent=2)}

Please provide your response in JSON format with two fields:
1. "summary_for_management": A concise summary of the issue, customer status, order/shipment status, and recommended action steps so managers can handle or review it.
2. "automated_reply": A professional, helpful, and empathetic reply to be sent back to the customer addressing their concern with relevant details from their account.

Return ONLY valid JSON.
"""

    summary_text = ""
    reply_text = ""

    if client:
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith('```json'):
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
            parsed = json.loads(raw_text)
            summary_text = parsed.get('summary_for_management', '')
            reply_text = parsed.get('automated_reply', '')
        except Exception as e:
            current_app.logger.error(f"Gemini API Error: {e}")
            summary_text = f"[AI Summary Fallback] Customer reported issue: '{comm.body}'. Context reviewed."
            reply_text = f"Dear {customer_context.get('company_name', 'Valued Customer')},\n\nThank you for reaching out. We have received your message regarding '{comm.subject or 'your issue'}' and our support team is reviewing your account history to resolve it promptly.\n\nBest regards,\nKW CRM Support"
    else:
        summary_text = f"[AI Summary Mode (Rule-based)] Customer {customer_context.get('company_name')} reported: '{comm.body}'. Active orders: {len(customer_context.get('orders', []))}."
        reply_text = f"Hello {customer_context.get('company_name', 'Customer')},\n\nWe received your inquiry: '{comm.body}'. Our team is currently investigating your request alongside your recent order history.\n\nBest regards,\nSupport Team"

    # Store Automated AI Reply in Communications timeline
    ai_reply_comm = Communication(
        customer_id=comm.customer_id,
        order_id=comm.order_id,
        contract_id=comm.contract_id,
        direction='Outbound',
        channel='Email',
        subject=f"Re: {comm.subject or 'Your Inquiry'}",
        body=reply_text
    )
    db.session.add(ai_reply_comm)

    # Store AI Management Summary in Communications timeline
    summary_comm = Communication(
        customer_id=comm.customer_id,
        order_id=comm.order_id,
        contract_id=comm.contract_id,
        direction='Outbound',
        channel='System_Notification',
        subject=f"[AI Manager Summary] {comm.subject or 'Issue Analysis'}",
        body=summary_text
    )
    db.session.add(summary_comm)
    db.session.commit()

    return {
        'summary': summary_text,
        'reply': reply_text
    }
