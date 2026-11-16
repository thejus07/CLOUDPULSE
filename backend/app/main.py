"""
CloudPulse Application Entrypoint
Initializes Flask app, registers API blueprints, enables CORS, and manages database schema lifecycle.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from backend.app.config import config
from backend.app.models.database import init_db
from backend.app.api.routes import api_bp


def create_app():
    """Application factory for CloudPulse backend."""
    app = Flask(__name__)
    app.config.from_object(config)

    # Initialize CORS for frontend dashboard
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"]
    )

    # Initialize database tables
    init_db()

    # Register API routes
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return jsonify({
            "platform": "CloudPulse: Intelligent Infrastructure Monitoring & Incident Response",
            "version": "1.0.0",
            "api_prefix": "/api",
            "docs": "/docs",
            "status": "OPERATIONAL"
        }), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "ResourceNotFound", "message": "The requested API endpoint was not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "InternalServerError", "message": "An unexpected error occurred"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
