# KW CRM - Testing Documentation & QA Guide

> **Project:** KW CRM (Kilowatt Hack AI Thon)  
> **Framework:** Python `unittest`, Flask Test Client, In-Memory SQLite  

---

## 📋 Overview

This document outlines the testing strategy, test suite architecture, automated test cases, and manual verification procedures for the **KW CRM** application.

---

## 🏗️ Test Suite Architecture

The test suite is built using Python's standard `unittest` framework and Flask's built-in `test_client()`. It uses an isolated in-memory SQLite database (`sqlite:///:memory:`) for each test run to ensure complete test isolation and zero side effects on production data.

- **Test Suite Location:** [`tests/test_crm.py`](file:///workspaces/KW-CRM/tests/test_crm.py)
- **Execution Command:**  
  ```bash
  python3 -m unittest discover tests
  ```

---

## 🧪 Automated Test Cases Summary

| Test Case Name | Target Component | Verifications Performed |
| :--- | :--- | :--- |
| `test_user_registration_and_login` | Auth API (`/api/auth/register`, `/api/auth/login`) | User registration, password hashing verification, session creation |
| `test_customer_and_contact_creation` | Core CRM API (`/api/customers`, `/api/contacts`) | Creating customer companies, attaching contacts with birthday/anniversary dates |
| `test_pipeline_analytics_and_snoozed_leads` | Analytics & APScheduler Job | Calculation of active pipeline financials, detection of pending orders >48h without comms, auto-triggering high-priority alerts |
| `test_stock_depletion_analytics` | Analytics API (`/api/analytics/stock-depletion`) | Query execution over order items history, sales velocity spike detection |

---

## 🛠️ Step-by-Step Manual QA & Verification Guide

### 1. Verification of User Registration & Login
1. Open terminal and run `python3 run.py`.
2. Send a `POST` request to `/api/auth/register`:
   ```json
   {
     "username": "sales_admin",
     "email": "admin@kwcrm.com",
     "password": "secretpassword",
     "role": "Admin"
   }
   ```
3. Expected Output: HTTP `201 Created` with sanitized user object (excluding `password_hash`).

---

### 2. Verification of Gemini AI Complaint Auto-Reply & Management Summarizer
1. Navigate to `http://127.0.0.1:5000/`.
2. Click **`+ Simulate Customer Complaint (AI Auto-Reply)`** in the top header.
3. Select a Customer Company (e.g. `Acme Industrial Corp`).
4. Enter Subject: `Urgent: Shipment Delay & Invoice Copy`.
5. Enter Body: `Our 1TB Cloud Storage Server is delayed. Please check shipping status.`
6. Click **Submit Complaint & Run Gemini AI**.
7. **Expected Result:**
   - Redirects to **Timeline & AI Auto-Reply** tab.
   - 3 entries displayed in timeline:
     - `Inbound` (Email/Call): Original customer complaint.
     - `Outbound` (`Email`): Gemini AI generated empathetic customer response.
     - `Outbound` (`System_Notification`): Gemini AI management issue summary.

---

### 3. Verification of 48-Hour Snoozed Lead Alerts
1. Open the **Pipeline & Analytics** tab in the sidebar.
2. Click **`Run Snoozed Lead Check (48h)`**.
3. **Expected Result:**
   - Scans all `Pending` orders created > 48 hours ago.
   - Generates a `[HIGH-PRIORITY LEAD ALERT] Snoozed Order #<id>` entry in the engagement timeline for any uncontacted order.

---

### 4. Verification of Birthday & Work Anniversary Background Jobs
1. Create a Contact with today's date set as their `Birthday` or `Work Anniversary`.
2. Execute the notification job manually or wait for the 09:00 AM APScheduler cron run:
   ```bash
   python3 -c "from app import create_app; from app.services.notification_service import check_and_send_birthday_notifications; app = create_app(); check_and_send_birthday_notifications(app)"
   ```
3. **Expected Result:** Outbound `Email` greeting logged into the customer timeline.

---

### 5. Verification of WooCommerce Webhooks & REST Sync
1. Post a test order webhook payload to `/api/woocommerce/webhook/order-created`.
2. Or trigger manual sync by clicking **`Sync WooCommerce`** on the top header bar.
3. **Expected Result:** Automatic creation of matching Customer, Product, Order, and Billing records in the CRM database.

---

## 📊 Sample Test Output Log

```text
/workspaces/KW-CRM/tests/test_crm.py
. . . .
----------------------------------------------------------------------
Ran 4 tests in 1.108s

OK
```
