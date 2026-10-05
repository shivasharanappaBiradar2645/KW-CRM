from flask import Blueprint, request, jsonify
from app.services.woocommerce_service import get_woocommerce_client, sync_woocommerce_order, verify_webhook_signature

woocommerce_bp = Blueprint('woocommerce', __name__, url_prefix='/api/woocommerce')

@woocommerce_bp.route('/webhook/order-created', methods=['POST'])
def handle_order_created_webhook():
    """Webhook endpoint triggered by WooCommerce when a new order is created."""
    signature = request.headers.get('X-Wc-Webhook-Signature')
    payload = request.get_data()

    if not verify_webhook_signature(payload, signature):
        return jsonify({'error': 'Invalid webhook signature'}), 401

    order_data = request.get_json() or {}
    if not order_data or 'id' not in order_data:
        return jsonify({'error': 'Invalid order payload'}), 400

    crm_order = sync_woocommerce_order(order_data)
    return jsonify({
        'message': 'WooCommerce order synced successfully',
        'crm_order_id': crm_order.id
    }), 200

@woocommerce_bp.route('/sync/orders', methods=['POST'])
def manual_sync_orders():
    """Manual sync endpoint to fetch orders directly from WooCommerce API."""
    wc = get_woocommerce_client()
    if not wc:
        return jsonify({'error': 'WooCommerce API credentials not configured'}), 400

    try:
        response = wc.get('orders', params={'per_page': 50})
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch WooCommerce orders', 'details': response.json()}), 400

        orders = response.json()
        synced_orders = []
        for wc_order in orders:
            order = sync_woocommerce_order(wc_order)
            synced_orders.append(order.id)

        return jsonify({
            'message': f'Successfully synced {len(synced_orders)} orders from WooCommerce',
            'synced_order_ids': synced_orders
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
