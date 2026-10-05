from datetime import date
from app import create_app, db
from app.models import User, Customer, Contact, Product, Contract, Order, OrderItem, Billing, ShipmentTracking, Communication

app = create_app()

def seed_test_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        print("Seeding test data...")

        # 1. System Users
        admin = User(username='admin', email='admin@kwcrm.com', full_name='System Admin', role='Admin')
        admin.set_password('admin123')
        
        manager = User(username='sales_mgr', email='sales@kwcrm.com', full_name='Alex Rivera', role='Manager')
        manager.set_password('sales123')

        db.session.add_all([admin, manager])
        db.session.commit()

        # 2. Customers (Companies)
        c1 = Customer(company_name='Acme Industrial Corp', email='purchasing@acmeind.com')
        c2 = Customer(company_name='Stark Tech Solutions', email='procurement@starktech.io')

        db.session.add_all([c1, c2])
        db.session.commit()

        # 3. Contacts (People, Managers, Personal Dates)
        cnt1 = Contact(
            customer_id=c1.id,
            first_name='Robert',
            last_name='Vance',
            job_title='Chief Executive Officer',
            email='rvance@acmeind.com',
            phone='+1-555-0144',
            birthday=date(1975, 4, 12),
            anniversary=date(2010, 8, 25),
            notes='Prefers quarterly in-person syncs.'
        )

        cnt2 = Contact(
            customer_id=c2.id,
            first_name='Pepper',
            last_name='Potts',
            job_title='Operations Director',
            email='pepper@starktech.io',
            phone='+1-555-0199',
            birthday=date(1988, 11, 2),
            notes='Key decision maker for hardware contracts.'
        )

        db.session.add_all([cnt1, cnt2])

        # 4. Products Catalog
        p1 = Product(name='Enterprise CRM Module', sku='SW-CRM-ENT', price=1200.00)
        p2 = Product(name='Cloud Storage Server 1TB', sku='HW-SRV-1TB', price=450.00)
        p3 = Product(name='Annual SLA Support Package', sku='SVC-SLA-1YR', price=800.00)

        db.session.add_all([p1, p2, p3])
        db.session.commit()

        # 5. Contracts
        contract1 = Contract(
            customer_id=c1.id,
            terms_text='Standard Annual Enterprise Software & Support Agreement',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status='Active'
        )
        db.session.add(contract1)
        db.session.commit()

        # 6. Orders & Order Items
        order1 = Order(customer_id=c1.id, contract_id=contract1.id, total_amount=1650.00, order_status='Processing')
        db.session.add(order1)
        db.session.commit()

        item1 = OrderItem(order_id=order1.id, product_id=p1.id, quantity=1, unit_price=1200.00)
        item2 = OrderItem(order_id=order1.id, product_id=p2.id, quantity=1, unit_price=450.00)
        db.session.add_all([item1, item2])

        # 7. Billing Record
        bill1 = Billing(
            order_id=order1.id,
            invoice_number='INV-2026-001',
            payment_status='Paid',
            due_date=date(2026, 2, 1),
            amount_due=0.00
        )
        db.session.add(bill1)

        # 8. Shipment Tracking
        shipment1 = ShipmentTracking(
            order_id=order1.id,
            carrier='FedEx',
            tracking_number='FEX-992014881',
            shipment_status='In_Transit'
        )
        db.session.add(shipment1)

        # 9. Communications Timeline
        comm1 = Communication(
            customer_id=c1.id,
            order_id=order1.id,
            contract_id=contract1.id,
            direction='Outbound',
            channel='Email',
            subject='Order Confirmation & License Keys',
            body='Dear Robert, your order #INV-2026-001 has been processed and licenses activated.'
        )
        comm2 = Communication(
            customer_id=c1.id,
            order_id=order1.id,
            direction='Inbound',
            channel='Call_Log',
            subject='Hardware Installation Query',
            body='Robert called inquiring about server delivery timeline.'
        )
        db.session.add_all([comm1, comm2])

        db.session.commit()
        print("Test data seeded successfully!")

if __name__ == '__main__':
    seed_test_data()
