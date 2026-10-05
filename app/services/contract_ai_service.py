import json
from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models import Contract, Customer, Communication
from app.services.ai_service import get_gemini_client, gather_customer_context

def analyze_expiring_contract_with_ai(contract, days_remaining):
    """
    Uses Gemini LLM to analyze an expiring contract, evaluate customer history,
    and generate a personalized renewal strategy with suggested discount percentages.
    """
    customer_context = gather_customer_context(contract.customer_id)
    client = get_gemini_client()

    prompt = f"""
You are an AI Revenue & Contract Renewal Strategist for KW CRM.
A customer contract is expiring soon. Analyze their account context and generate an optimal renewal proposal.

[CONTRACT DETAILS]
Contract ID: {contract.id}
Start Date: {contract.start_date}
End Date: {contract.end_date}
Days Remaining: {days_remaining}
Terms: {contract.terms_text or 'Standard Terms'}
Status: {contract.status}

[CUSTOMER ACCOUNT CONTEXT]
{json.dumps(customer_context, indent=2)}

Please provide your response in JSON format with three fields:
1. "contract_summary": A concise analysis of the contract status, remaining days, and total account spending.
2. "suggested_discount_percentage": A recommended discount percentage (e.g. 5, 10, 15) to incentivize early renewal based on their order volume.
3. "renewal_pitch_email": A personalized outreach email to the customer contact proposing a contract extension with the suggested discount.

Return ONLY valid JSON.
"""

    if client:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith('```json'):
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
            return json.loads(raw_text)
        except Exception as e:
            current_app.logger.error(f"Gemini API Error in contract analysis: {e}")

    # Fallback if Gemini key is not set or API fails
    discount = 10 if len(customer_context.get('orders', [])) > 1 else 5
    company_name = customer_context.get('company_name', 'Valued Customer')
    return {
        "contract_summary": f"Contract expires in {days_remaining} days. Customer has {len(customer_context.get('orders', []))} completed orders.",
        "suggested_discount_percentage": discount,
        "renewal_pitch_email": f"Dear {company_name},\n\nYour contract is set to expire in {days_remaining} days on {contract.end_date}. To thank you for your partnership, we are pleased to offer a {discount}% early renewal discount if renewed this week.\n\nBest regards,\nKW CRM Sales Team"
    }


def check_expiring_contracts_job(app, warning_days=30):
    """
    Background job function executed by APScheduler.
    Scans active contracts expiring within `warning_days` (default 30 days).
    Generates AI-powered renewal pitches with suggested discounts and logs them into Communications.
    """
    with app.app_context():
        today = datetime.now().date()
        target_expiry_window = today + timedelta(days=warning_days)

        # Query active contracts ending on or before the target window that haven't expired yet
        expiring_contracts = Contract.query.filter(
            Contract.status == 'Active',
            Contract.end_date >= today,
            Contract.end_date <= target_expiry_window
        ).all()

        for contract in expiring_contracts:
            days_remaining = (contract.end_date - today).days

            # Run AI analysis for renewal proposal & discount
            ai_proposal = analyze_expiring_contract_with_ai(contract, days_remaining)

            discount_pc = ai_proposal.get('suggested_discount_percentage', 10)
            summary_text = ai_proposal.get('contract_summary', '')
            pitch_email = ai_proposal.get('renewal_pitch_email', '')

            # 1. Log System Notification for Manager with AI Discount Recommendation
            manager_log = Communication(
                customer_id=contract.customer_id,
                contract_id=contract.id,
                direction='Outbound',
                channel='System_Notification',
                subject=f"[AI Contract Alert] Expiration in {days_remaining} days ({discount_pc}% Discount Suggested)",
                body=f"Summary: {summary_text}\n\nSuggested Discount: {discount_pc}%\n\nProposed Email Pitch:\n{pitch_email}"
            )
            db.session.add(manager_log)

            # 2. Log Outbound Email Pitch to Customer
            customer_log = Communication(
                customer_id=contract.customer_id,
                contract_id=contract.id,
                direction='Outbound',
                channel='Email',
                subject=f"Contract Renewal Proposal - {discount_pc}% Early Renewal Discount",
                body=pitch_email
            )
            db.session.add(customer_log)

        db.session.commit()
