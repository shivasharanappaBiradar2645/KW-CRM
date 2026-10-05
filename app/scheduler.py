from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def init_scheduler(app):
    from app.services.notification_service import check_and_send_birthday_notifications
    from app.services.contract_ai_service import check_expiring_contracts_job
    from app.services.pipeline_analytics_service import check_snoozed_leads_job

    # 1. Daily birthday notifications at 09:00 AM
    scheduler.add_job(
        func=check_and_send_birthday_notifications,
        args=[app],
        trigger='cron',
        hour=9,
        minute=0,
        id='birthday_notifications_job',
        replace_existing=True
    )

    # 2. Daily AI contract expiry check at 08:00 AM
    scheduler.add_job(
        func=check_expiring_contracts_job,
        args=[app, 30],
        trigger='cron',
        hour=8,
        minute=0,
        id='contract_expiry_ai_job',
        replace_existing=True
    )

    # 3. Snoozed leads check job (Pending > 48h without comms) every 4 hours
    scheduler.add_job(
        func=check_snoozed_leads_job,
        args=[app, 48],
        trigger='interval',
        hours=4,
        id='snoozed_leads_check_job',
        replace_existing=True
    )

    scheduler.start()
    app.logger.info("APScheduler initialized with Birthday, AI Contract, and Snoozed Lead jobs.")
