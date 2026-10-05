import hmac
import hashlib
import base64
from flask import current_app
from woocommerce import API
from app.extensions import db
from app.models import Customer, Product, Order, OrderItem, Billing, ShipmentTracking
from datetime import datetime

def get_woocommerce_client():
    url = current_app.config.get('WOOCOMMERCE_URL')
    ck = current_app.config.get('WOOCOMMERCE_CONSUMER_KEY')
    cs = current_app.config.get('WOOCOMMERCE_CONSUMER_SECRET')
    
    if not ck or not cs:
        return None
        
    return API(
        url=url,
        consumer_key=ck,
        consumer_secret=cs,
        version="wc/v3"
    )

def verify_webhook_signature(payload, signature_header):
    """Verify WooCommerce Webhook HMAC SHA256 Signature"""
    secret = current_app.config.get('WOOCOMMERCE_WEBHOOK_SECRET')
    if not secret or not signature_header:
        return True  # If no secret configured, skip check (or return False for strict mode)

    expected_signature = base64.b64encode(
        hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).digest()
    ).decode('utf-8')
    
    return hmac.compare_digest(expected_signature, signature_header)

def sync_woocommerce_order(wc_order):
    """
    Sync WooCommerce order payload into CRM models:
    - Customer
    - Products
    - Order & OrderItems
    - Billing
    """
    billing_info = wc_order.get('billing', {})
    customer_email = billing_info.get('email') or f"wc_user_{wc_order.get('customer_id')}@store.local"
    company_name = billing_info.get('company') or f"{billing_info.get('first_name', '')} {billing_info.get('last_name', '')}".strip() or "WooCommerce Customer"

    # 1. Sync or Find Customer
    customer = Customer.query.filter_by(email=customer_email).first()
    if not customer:
        customer = Customer(
            company_name=company_name,
            email=customer_email
        )
        db.session.add(customer)
        db.session.commit()

    # 2. Sync Products & Line Items
    line_items = wc_order.get('line_items', [])
    order_items_to_create = []

    for item in line_items:
        sku = item.get('sku') or f"WC-PROD-{item.get('product_id')}"
        prod_name = item.get('name', 'WooCommerce Product')
        price = float(item.get('price', 0.0))

        product = Product.query.filter_by(sku=sku).first()
        if not product:
            product = Product(
                name=prod_name,
                sku=sku,
                price=price
            )
            db.session.add(product)
            db.session.commit()

        order_items_to_create.append({
            'product_id': product.id,
            'quantity': item.get('quantity', 1),
            'unit_price': price
        })

    # 3. Create CRM Order
    total_amount = float(wc_order.get('total', 0.0))
    status_mapping = {
        'pending': 'Pending',
        'processing': 'Processing',
        'on-hold': 'Pending',
        'completed': 'Delivered',
        'cancelled': 'Cancelled',
        'refunded': 'Cancelled',
        'failed': 'Cancelled'
    }
    wc_status = wc_order.get('status', 'pending')
    crm_order_status = status_mapping.get(wc_status, 'Pending')

    order = Order(
        customer_id=customer.id,
        total_amount=total_amount,
        order_status=crm_order_status
    )
    db.session.add(order)
    db.session.commit()

    # 4. Attach Order Items
    for item_data in order_items_to_create:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price']
        )
        db.session.add(order_item)

    # 5. Create Billing Record
    payment_status = 'Paid' if wc_status in ['processing', 'completed'] else 'Unpaid'
    billing = Billing(
        order_id=order.id,
        invoice_number=f"WC-INV-{wc_order.get('id')}",
        payment_status=payment_status,
        due_date=datetime.now().date(),
        amount_due=total_amount if payment_status == 'Unpaid' else 0.00
    )
    db.session.add(billing)
    db.session.commit()

    return order
