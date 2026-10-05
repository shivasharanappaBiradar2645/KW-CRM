import os
from flask import Flask
from config import Config
from app.extensions import db

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    
    if isinstance(config_class, dict):
        app.config.from_object(Config)
        app.config.update(config_class)
    else:
        app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints/routes
    from app.routes.main import bp as main_bp
    from app.routes.api import api_bp
    from app.routes.woocommerce import woocommerce_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(woocommerce_bp)

    # Create database tables if they do not exist
    with app.app_context():
        db.create_all()

    # Initialize APScheduler background jobs (only run scheduler in main process to prevent duplicate runs)
    if not app.config.get('TESTING', False):
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from app.scheduler import init_scheduler
            init_scheduler(app)

    return app
