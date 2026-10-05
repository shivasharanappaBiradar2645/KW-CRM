from app import create_app, db
from app.models import User, Customer, Contact, Product, Contract, Order, OrderItem, Billing, ShipmentTracking, Communication

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Customer': Customer,
        'Contact': Contact,
        'Product': Product,
        'Contract': Contract,
        'Order': Order,
        'OrderItem': OrderItem,
        'Billing': Billing,
        'ShipmentTracking': ShipmentTracking,
        'Communication': Communication
    }

if __name__ == '__main__':
    app.run(debug=True)
