import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask
from flask_migrate import Migrate
from config import Config
from models.database import db
from controllers.auth_controller import auth_bp
from controllers.product_controller import product_bp
from controllers.cart_controller import cart_bp
from controllers.feedback_controller import feedback_bp
from controllers.admin_controller import admin_bp
from controllers.order_controller import order_bp

import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(order_bp)

    # Set up the index route to point to the product index
    @app.route('/')
    def index():
                from flask import redirect, url_for
                return redirect(url_for('product.index'))

    return app

# Create app instance for production (Gunicorn)
app = create_app()

if __name__ == '__main__':
    # This is only for development - not used in production
    app.run(host="0.0.0.0", port=5000, debug=False)