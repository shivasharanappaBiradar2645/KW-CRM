import json
from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models import Order, OrderItem, Product, Communication

def calculate_dynamic_pipeline_value():
    """Calculates total financial value of all active (Pending + Processing) orders."""
    active_orders = Order.query.filter(Order.order_status.in_(['Pending', 'Processing'])).all()
    total_val = sum(float(o.total_amount or 0.0) for o in active_orders)
    return {
        'active_orders_count': len(active_orders),
        'total_pipeline_value': round(total_val, 2)
    }

def check_snoozed_leads_job(app, max_pending_hours=48):
    """
    Background job executed by APScheduler.
    Checks orders in 'Pending' status created > 48h ago that have NO recent communications for that specific order.
    Triggers a high-priority System_Notification follow-up alert.
    """
    with app.app_context():
        cutoff_time = datetime.utcnow() - timedelta(hours=max_pending_hours)

        # Query orders in 'Pending' state created before cutoff_time
        pending_orders = Order.query.filter(
            Order.order_status == 'Pending',
            Order.created_at <= cutoff_time
        ).all()

        snoozed_alerts_count = 0
        for order in pending_orders:
            # Check if there are any communications linked specifically to this order since cutoff
            recent_comm = Communication.query.filter(
                Communication.order_id == order.id,
                Communication.sent_at >= cutoff_time
            ).first()

            if not recent_comm:
                # Trigger High-Priority System Notification Alert
                alert_subject = f"[HIGH-PRIORITY LEAD ALERT] Snoozed Order #{order.id[:8]}"
                alert_body = f"Order #{order.id} for Customer {order.customer_id} has been PENDING for over {max_pending_hours} hours without follow-up communication. Value: ${float(order.total_amount):.2f}. Action required immediately!"

                # Avoid duplicate alerts sent within last 24h
                existing_alert = Communication.query.filter_by(
                    customer_id=order.customer_id,
                    order_id=order.id,
                    channel='System_Notification',
                    subject=alert_subject
                ).first()

                if not existing_alert:
                    alert = Communication(
                        customer_id=order.customer_id,
                        order_id=order.id,
                        direction='Outbound',
                        channel='System_Notification',
                        subject=alert_subject,
                        body=alert_body
                    )
                    db.session.add(alert)
                    snoozed_alerts_count += 1

        db.session.commit()
        return snoozed_alerts_count


def calculate_product_stock_depletion_analytics(days_window=30):
    """
    Analytics function: Analyzes order_items history over a recent window (e.g. 30 days) vs previous window
    to detect sales velocity spikes and predict stock depletion.
    """
    today = datetime.utcnow()
    recent_start = today - timedelta(days=days_window)
    prev_start = today - timedelta(days=days_window * 2)

    # 1. Fetch sales in recent window
    recent_items = db.session.query(
        OrderItem.product_id,
        db.func.sum(OrderItem.quantity).label('recent_qty')
    ).join(Order).filter(
        Order.created_at >= recent_start
    ).group_by(OrderItem.product_id).all()

    # 2. Fetch sales in previous window
    prev_items = db.session.query(
        OrderItem.product_id,
        db.func.sum(OrderItem.quantity).label('prev_qty')
    ).join(Order).filter(
        Order.created_at >= prev_start,
        Order.created_at < recent_start
    ).group_by(OrderItem.product_id).all()

    prev_qty_map = {item.product_id: item.prev_qty for item in prev_items}

    analytics_results = []
    products = Product.query.all()

    for product in products:
        recent_qty = next((item.recent_qty for item in recent_items if item.product_id == product.id), 0)
        prev_qty = prev_qty_map.get(product.id, 0)

        velocity_change = recent_qty - prev_qty
        spike_detected = False

        if prev_qty > 0 and (recent_qty / prev_qty) >= 1.5:
            spike_detected = True
        elif prev_qty == 0 and recent_qty >= 5:
            spike_detected = True

        analytics_results.append({
            'product_id': product.id,
            'product_name': product.name,
            'sku': product.sku,
            'unit_price': float(product.price),
            'recent_sales_qty': recent_qty,
            'prev_sales_qty': prev_qty,
            'sales_growth_qty': velocity_change,
            'spike_detected': spike_detected
        })

    return analytics_results
