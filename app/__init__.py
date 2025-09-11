import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///document_hub.db'
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey123')
    db_path = os.path.abspath(os.path.join(os.getcwd(), 'document_hub.db'))
    print('Flask DB URI:', app.config['SQLALCHEMY_DATABASE_URI'])
    print('Absolute DB path:', db_path)
    db.init_app(app)
    # Enable CORS for all routes
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        pass
    from app.routes import routes
    # Register blueprint with no url_prefix so routes are at root level
    app.register_blueprint(routes, url_prefix='')
    return app
