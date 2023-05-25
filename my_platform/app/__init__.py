from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object('config.Config')
    app.config['DEBUG'] = True

    db.init_app(app)  # Initialize the db object
    migrate.init_app(app, db)
    login_manager.init_app(app)

    global celery
    celery = create_celery(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
