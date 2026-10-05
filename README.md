# KW CRM - Enterprise AI Customer Relationship Management

> Built for the **Kilowatt Hack AI Thon**

KW CRM is an enterprise-grade Customer Relationship Management (CRM) application built using Python Flask, SQLAlchemy, Google Gemini LLM, APScheduler, and WooCommerce REST APIs. It provides automated customer service, predictive analytics, revenue forecasting, contract management, and background task processing.

---

## 🌟 Key Features

### 🤖 1. Gemini AI Customer Support & Automated Replies
- **Inbound Complaint Auto-Processing**: When a customer reaches out via Email, SMS, or Call Log, the system automatically pulls their complete account background (past orders, active contracts, shipment status, and billing details).
- **Dual AI Output**:
  - **Automated Customer Reply**: Empathetic, data-driven email response generated for the customer.
  - **Management Issue Summary**: High-level summary sent to store managers outlining customer status and recommended resolution steps.

### 📜 2. AI-Powered Contract Expiration & Discount Engine
- **Automated Contract Scanner**: Background job scans active contracts expiring within 30 days.
- **Smart Discounting**: Gemini LLM analyzes customer purchasing volume to compute an optimal early renewal discount percentage (e.g., 5%, 10%, 15%).
- **Automated Pitch Generation**: Generates personalized renewal pitch emails and alerts management via system notifications.

### 📈 3. Dynamic Pipeline Financials & Snoozed Lead Alerts
- **Pipeline Value Calculation**: Aggregates total financial value across all active (`Pending` & `Processing`) orders.
- **Snoozed Lead 48-Hour Scanner**: APScheduler background job checks orders sitting in `Pending` state for over 48 hours without contact and triggers high-priority follow-up alerts to sales representatives.

### 📦 4. Predictive Stock Depletion Analytics
- **Sales Velocity Queries**: Analyzes sales trends in `order_items` over recent 30-day windows versus preceding periods.
- **Depletion Spike Detection**: Flags high velocity spikes (`⚡ HIGH DEPLETION SPIKE`) to alert managers before inventory runs out.

### ⏰ 5. Automated Background Jobs (`APScheduler`)
- **Daily Birthday & Anniversary Greetings**: Automatically sends personalized emails on contacts' birthdays and work anniversaries every morning at 09:00 AM.
- **Automated Timeline Logging**: All background notifications, emails, and alerts are stored in the customer engagement timeline.

### 🛒 6. WooCommerce E-Commerce Integration
- **Real-Time Webhooks**: Endpoint `/api/woocommerce/webhook/order-created` with HMAC SHA-256 signature verification.
- **REST Order & Catalog Sync**: Endpoint `/api/woocommerce/sync/orders` to import products, customers, and orders seamlessly.
- **Optional & Standalone**: Works 100% independently even if WooCommerce is not configured.

### 👥 7. People & Contact Management
- Separate tracking for customer managers and key personnel.
- Stores birthday dates, work anniversaries, job titles, direct contact numbers, and notes.

### 💻 8. Interactive Modern Frontend Dashboard
- Responsive dashboard UI with dynamic KPI stat cards.
- Interactive Modals for full CRUD operations:
  - Add Customer Companies
  - Add Contacts & Managers
  - Add Products & Catalog Items
  - Create Customer Contracts
  - Create Orders & Order Line Items
  - Simulate Customer Complaints (Interactive Gemini AI Test Launcher)

---

## 🗄️ Database Architecture (SQLAlchemy ORM)

Supported default database: **SQLite** (easily swappable to **PostgreSQL** or **MySQL** via `DATABASE_URL`).

| Table Name | Description |
| :--- | :--- |
| `users` | System users with password hashing (`werkzeug.security`) and role permissions |
| `customers` | Customer company accounts |
| `contacts` | People & manager details (birthdays, anniversaries, job titles) |
| `products` | Catalog items, SKUs, and prices |
| `contracts` | Customer legal agreements, start/end dates, and terms |
| `orders` | Central order processing engine |
| `order_items` | Junction table linking orders to products with check constraints |
| `billing` | Invoices, payment status (`Paid`, `Unpaid`, `Overdue`), and due dates |
| `shipment_tracking` | Order fulfillment, carrier tracking, and status |
| `communications` | Central engagement timeline capturing all inbound/outbound touchpoints |

---

## 🚀 Getting Started

### 1. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/your-repo/KW-CRM.git
cd KW-CRM

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration (`.env`)

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Set your configuration values:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///crm.db
GEMINI_API_KEY=your_google_gemini_api_key

# Optional: WooCommerce Credentials
WOOCOMMERCE_URL=https://your-store.com
WOOCOMMERCE_CONSUMER_KEY=ck_your_key
WOOCOMMERCE_CONSUMER_SECRET=cs_your_secret

# Optional: SMTP Email Settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=notifications@kwcrm.com
MAIL_PASSWORD=your_email_app_password
```

### 3. Seed Test Data

Populate the database with realistic sample companies, contacts, products, and orders:

```bash
python3 seed_data.py
```

### 4. Run the Application

Start the Flask development server:

```bash
python3 run.py
```

Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## 🧪 Running Unit Tests

Run the automated test suite covering authentication, API endpoints, background jobs, and analytics:

```bash
python3 -m unittest discover tests
```

---

## 📄 License

This project was created for the **Kilowatt Hack AI Thon**. All rights reserved.
