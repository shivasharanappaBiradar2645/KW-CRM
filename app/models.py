import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), default='Staff')  # Admin, Manager, Staff
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    company_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    contacts = db.relationship('Contact', backref='customer', cascade='all, delete-orphan', lazy=True)
    contracts = db.relationship('Contract', backref='customer', cascade='all, delete-orphan', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    communications = db.relationship('Communication', backref='customer', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'contacts': [contact.to_dict() for contact in self.contacts]
        }


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    anniversary = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'job_title': self.job_title,
            'email': self.email,
            'phone': self.phone,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'anniversary': self.anniversary.isoformat() if self.anniversary else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'price': float(self.price) if self.price is not None else 0.0
        }


class Contract(db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    terms_text = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='Active')

    orders = db.relationship('Order', backref='contract', lazy=True)
    communications = db.relationship('Communication', backref='contract', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'terms_text': self.terms_text,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    contract_id = db.Column(db.String(36), db.ForeignKey('contracts.id'), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    order_status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=utc_now)

    order_items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)
    billing = db.relationship('Billing', backref='order', uselist=False, cascade='all, delete-orphan', lazy=True)
    shipment_tracking = db.relationship('ShipmentTracking', backref='order', uselist=False, cascade='all, delete-orphan', lazy=True)
    communications = db.relationship('Communication', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'contract_id': self.contract_id,
            'total_amount': float(self.total_amount) if self.total_amount is not None else 0.0,
            'order_status': self.order_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.order_items],
            'billing': self.billing.to_dict() if self.billing else None,
            'shipment_tracking': self.shipment_tracking.to_dict() if self.shipment_tracking else None
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_quantity_positive'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price is not None else 0.0
        }


class Billing(db.Model):
    __tablename__ = 'billing'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    payment_status = db.Column(db.String(50), default='Unpaid')
    due_date = db.Column(db.Date, nullable=False)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'invoice_number': self.invoice_number,
            'payment_status': self.payment_status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'amount_due': float(self.amount_due) if self.amount_due is not None else 0.0
        }


class ShipmentTracking(db.Model):
    __tablename__ = 'shipment_tracking'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    carrier = db.Column(db.String(100), nullable=False)
    tracking_number = db.Column(db.String(100), nullable=False)
    shipment_status = db.Column(db.String(50), default='Label_Created')
    estimated_delivery = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'carrier': self.carrier,
            'tracking_number': self.tracking_number,
            'shipment_status': self.shipment_status,
            'estimated_delivery': self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Communication(db.Model):
    __tablename__ = 'communications'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True, index=True)
    contract_id = db.Column(db.String(36), db.ForeignKey('contracts.id', ondelete='SET NULL'), nullable=True)

    direction = db.Column(db.String(10), nullable=False)
    channel = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    body = db.Column(db.Text, nullable=False)

    sent_at = db.Column(db.DateTime, default=utc_now)
    read_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.CheckConstraint("direction IN ('Inbound', 'Outbound')", name='check_communication_direction'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'contract_id': self.contract_id,
            'direction': self.direction,
            'channel': self.channel,
            'subject': self.subject,
            'body': self.body,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
