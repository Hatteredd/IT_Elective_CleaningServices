from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()

# Optional web dependencies — not needed for the Tkinter desktop GUI
try:
    from flask_login import LoginManager
    from flask_wtf.csrf import CSRFProtect
    login_manager = LoginManager()
    csrf = CSRFProtect()
    _has_web_deps = True
except ImportError:
    login_manager = None
    csrf = None
    _has_web_deps = False


def create_app(test_config=None):
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "..", "instance", "app.db")}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    
    if test_config:
        app.config.update(test_config)
    
    db.init_app(app)
    
    # Optional web blueprints and error handlers (used only when running web tests)
    if _has_web_deps and login_manager and csrf:
        try:
            from flask import render_template
            login_manager.init_app(app)
            csrf.init_app(app)
            login_manager.login_view = 'auth.login'
            login_manager.login_message = 'Please log in to access this page.'
            
            from app.models import User
            
            @login_manager.user_loader
            def load_user(user_id):
                return User.query.get(int(user_id))

            @app.context_processor
            def inject_unread_notifications():
                from flask_login import current_user
                count = 0
                if current_user.is_authenticated and current_user.role == 'customer':
                    from app.models import Notification
                    count = Notification.query.filter_by(
                        user_id=current_user.id, is_read=False
                    ).count()
                return {'unread_notifications': count}
            
            from app.routes import auth, public, customer, admin
            app.register_blueprint(auth.bp)
            app.register_blueprint(public.bp)
            app.register_blueprint(customer.bp)
            app.register_blueprint(admin.bp)

            @app.errorhandler(404)
            def not_found_error(error):
                return render_template('errors/404.html'), 404

            @app.errorhandler(500)
            def internal_error(error):
                db.session.rollback()
                return render_template('errors/500.html'), 500
        except Exception:
            pass
    
    with app.app_context():
        try:
            from sqlalchemy import event
            from sqlalchemy.engine import Engine

            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                try:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA busy_timeout=10000;")
                    cursor.close()
                except Exception:
                    pass
        except Exception:
            pass
        db.create_all()

    return app
