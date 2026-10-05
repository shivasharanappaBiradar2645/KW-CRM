from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import User, Customer, Contact, Product, Contract, Order, OrderItem, Billing, ShipmentTracking, Communication
from app.services.ai_service import process_customer_complaint
from app.services.pipeline_analytics_service import calculate_dynamic_pipeline_value, calculate_product_stock_depletion_analytics, check_snoozed_leads_job

api_bp = Blueprint('api', __name__, url_prefix='/api')

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


# ==========================================
# 1. AUTHENTICATION & USERS ENDPOINTS
# ==========================================

@api_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required.'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'User with given username or email already exists.'}), 400

    user = User(
        username=username,
        email=email,
        full_name=data.get('full_name'),
        role=data.get('role', 'Staff')
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully', 'user': user.to_dict()}), 201

@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username_or_email = data.get('username_or_email')
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify({'error': 'Username/email and password are required.'}), 400

    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    session['user_id'] = user.id
    return jsonify({'message': 'Logged in successfully', 'user': user.to_dict()}), 200

@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@api_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


# ==========================================
# 2. CUSTOMERS ENDPOINTS
# ==========================================

@api_bp.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([c.to_dict() for c in customers]), 200

@api_bp.route('/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify(customer.to_dict()), 200

@api_bp.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json() or {}
    if not data.get('company_name') or not data.get('email'):
        return jsonify({'error': 'company_name and email are required'}), 400

    if Customer.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Customer with this email already exists'}), 400

    customer = Customer(
        company_name=data['company_name'],
        email=data['email']
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify(customer.to_dict()), 201

@api_bp.route('/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json() or {}

    if 'company_name' in data:
        customer.company_name = data['company_name']
    if 'email' in data:
        customer.email = data['email']

    db.session.commit()
    return jsonify(customer.to_dict()), 200

@api_bp.route('/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'}), 200


# ==========================================
# 3. CONTACTS (PEOPLE & MANAGERS) ENDPOINTS
# ==========================================

@api_bp.route('/contacts', methods=['GET'])
def get_contacts():
    customer_id = request.args.get('customer_id')
    query = Contact.query
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    contacts = query.all()
    return jsonify([c.to_dict() for c in contacts]), 200

@api_bp.route('/contacts', methods=['POST'])
def create_contact():
    data = request.get_json() or {}
    if not data.get('customer_id') or not data.get('first_name') or not data.get('last_name'):
        return jsonify({'error': 'customer_id, first_name, and last_name are required'}), 400

    contact = Contact(
        customer_id=data['customer_id'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        job_title=data.get('job_title'),
        email=data.get('email'),
        phone=data.get('phone'),
        birthday=parse_date(data.get('birthday')),
        anniversary=parse_date(data.get('anniversary')),
        notes=data.get('notes')
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify(contact.to_dict()), 201


# ==========================================
# 4. PRODUCTS ENDPOINTS
# ==========================================

@api_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products]), 200

@api_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('sku') or data.get('price') is None:
        return jsonify({'error': 'name, sku, and price are required'}), 400

    product = Product(
        name=data['name'],
        sku=data['sku'],
        price=data['price']
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


# ==========================================
# 5. CONTRACTS ENDPOINTS
# ==========================================

@api_bp.route('/contracts', methods=['GET'])
def get_contracts():
    contracts = Contract.query.all()
    return jsonify([c.to_dict() for c in contracts]), 200

@api_bp.route('/contracts', methods=['POST'])
def create_contract():
    data = request.get_json() or {}
    if not data.get('customer_id') or not data.get('start_date') or not data.get('end_date'):
        return jsonify({'error': 'customer_id, start_date, and end_date are required'}), 400

    contract = Contract(
        customer_id=data['customer_id'],
        terms_text=data.get('terms_text'),
        start_date=parse_date(data['start_date']),
        end_date=parse_date(data['end_date']),
        status=data.get('status', 'Active')
    )
    db.session.add(contract)
    db.session.commit()
    return jsonify(contract.to_dict()), 201


# ==========================================
# 6. ORDERS & ORDER ITEMS ENDPOINTS
# ==========================================

@api_bp.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([o.to_dict() for o in orders]), 200

@api_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json() or {}
    if not data.get('customer_id'):
        return jsonify({'error': 'customer_id is required'}), 400

    order = Order(
        customer_id=data['customer_id'],
        contract_id=data.get('contract_id'),
        order_status=data.get('order_status', 'Pending')
    )
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201

@api_bp.route('/orders/<order_id>/items', methods=['POST'])
def add_order_item(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}

    if not data.get('product_id') or not data.get('quantity') or data.get('unit_price') is None:
        return jsonify({'error': 'product_id, quantity, and unit_price are required'}), 400

    quantity = int(data['quantity'])
    unit_price = float(data['unit_price'])
    if quantity <= 0:
        return jsonify({'error': 'quantity must be > 0'}), 400

    item = OrderItem(
        order_id=order.id,
        product_id=data['product_id'],
        quantity=quantity,
        unit_price=unit_price
    )
    db.session.add(item)
    
    # Recalculate total amount for order
    order.total_amount = float(order.total_amount or 0) + (quantity * unit_price)
    db.session.commit()

    return jsonify(order.to_dict()), 201


# ==========================================
# 7. COMMUNICATIONS & AI COMPLAINT AUTO-REPLY ENDPOINTS
# ==========================================

@api_bp.route('/communications', methods=['GET'])
def get_communications():
    customer_id = request.args.get('customer_id')
    order_id = request.args.get('order_id')

    query = Communication.query
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if order_id:
        query = query.filter_by(order_id=order_id)

    comms = query.order_by(Communication.sent_at.desc()).all()
    return jsonify([c.to_dict() for c in comms]), 200

@api_bp.route('/communications', methods=['POST'])
def create_communication():
    data = request.get_json() or {}
    if not data.get('customer_id') or not data.get('direction') or not data.get('channel') or not data.get('body'):
        return jsonify({'error': 'customer_id, direction, channel, and body are required'}), 400

    if data['direction'] not in ['Inbound', 'Outbound']:
        return jsonify({'error': "direction must be 'Inbound' or 'Outbound'"}), 400

    comm = Communication(
        customer_id=data['customer_id'],
        order_id=data.get('order_id'),
        contract_id=data.get('contract_id'),
        direction=data['direction'],
        channel=data['channel'],
        subject=data.get('subject'),
        body=data['body'],
        read_at=parse_datetime(data.get('read_at'))
    )
    db.session.add(comm)
    db.session.commit()

    # Trigger Gemini AI Complaint Processing for Inbound customer messages
    ai_result = None
    if comm.direction == 'Inbound':
        ai_result = process_customer_complaint(comm.id)

    return jsonify({
        'communication': comm.to_dict(),
        'ai_processing': ai_result
    }), 201


# ==========================================
# 8. ANALYTICS & SNOOZED LEADS ENDPOINTS
# ==========================================

@api_bp.route('/analytics/pipeline', methods=['GET'])
def get_pipeline_analytics():
    """Returns dynamic financial value of Pending + Processing orders."""
    pipeline_data = calculate_dynamic_pipeline_value()
    return jsonify(pipeline_data), 200

@api_bp.route('/analytics/stock-depletion', methods=['GET'])
def get_stock_depletion_analytics():
    """Returns product depletion velocity and sales spike analytics."""
    days = int(request.args.get('days', 30))
    stock_analytics = calculate_product_stock_depletion_analytics(days_window=days)
    return jsonify(stock_analytics), 200

@api_bp.route('/analytics/run-snoozed-check', methods=['POST'])
def trigger_snoozed_check():
    """Manually trigger snoozed leads job for testing/admin purposes."""
    from flask import current_app
    hours = int(request.args.get('hours', 48))
    alerts_triggered = check_snoozed_leads_job(current_app._get_current_object(), max_pending_hours=hours)
    return jsonify({
        'message': f'Snoozed leads check completed. Triggered {alerts_triggered} high-priority alerts.',
        'alerts_triggered': alerts_triggered
    }), 200
