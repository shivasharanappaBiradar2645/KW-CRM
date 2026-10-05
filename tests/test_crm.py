import unittest
from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models import User, Customer, Contact, Product, Contract, Order, OrderItem, Communication
from app.services.pipeline_analytics_service import check_snoozed_leads_job

class CRMTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_registration_and_login(self):
        res = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@crm.com',
            'password': 'password123',
            'full_name': 'Test User',
            'role': 'Staff'
        })
        self.assertEqual(res.status_code, 201)

        login_res = self.client.post('/api/auth/login', json={
            'username_or_email': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(login_res.status_code, 200)

    def test_customer_and_contact_creation(self):
        cust_res = self.client.post('/api/customers', json={
            'company_name': 'Acme Corp',
            'email': 'info@acme.com'
        })
        self.assertEqual(cust_res.status_code, 201)
        cust_id = cust_res.get_json()['id']

        cont_res = self.client.post('/api/contacts', json={
            'customer_id': cust_id,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@acme.com',
            'birthday': '1990-05-15',
            'anniversary': '2015-08-20'
        })
        self.assertEqual(cont_res.status_code, 201)

    def test_pipeline_analytics_and_snoozed_leads(self):
        with self.app.app_context():
            c = Customer(company_name='Snooze Test Co', email='snooze@co.com')
            db.session.add(c)
            db.session.commit()

            # Create an order 50 hours ago
            old_time = datetime.utcnow() - timedelta(hours=50)
            order = Order(customer_id=c.id, total_amount=500.00, order_status='Pending', created_at=old_time)
            db.session.add(order)
            db.session.commit()

            # Run snoozed job
            alerts = check_snoozed_leads_job(self.app, max_pending_hours=48)
            self.assertGreaterEqual(alerts, 1)

            # Check Pipeline endpoint
            res = self.client.get('/api/analytics/pipeline')
            self.assertEqual(res.status_code, 200)
            self.assertGreaterEqual(res.get_json()['active_orders_count'], 1)

    def test_stock_depletion_analytics(self):
        res = self.client.get('/api/analytics/stock-depletion')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

if __name__ == '__main__':
    unittest.main()
