"""
API Documentation endpoints for the Alkhorayef ESP IoT Platform.

This module provides Swagger UI and ReDoc interactive documentation
for the OpenAPI 3.0 specification.
"""

import os
from flask import Blueprint, send_from_directory, render_template_string

from app.core import get_logger


logger = get_logger(__name__)
docs_bp = Blueprint("docs", __name__, url_prefix="/api/v1")


# OpenAPI spec endpoint
@docs_bp.route("/openapi.yaml", methods=["GET"])
def openapi_spec():
    """
    Serve the OpenAPI 3.0 specification YAML file.

    Returns:
        OpenAPI YAML specification file
    """
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'docs')
    return send_from_directory(docs_dir, 'openapi.yaml', mimetype='text/yaml')


# Swagger UI endpoint
@docs_bp.route("/docs", methods=["GET"])
@docs_bp.route("/docs/", methods=["GET"])
def swagger_ui():
    """
    Serve Swagger UI for interactive API documentation.

    Returns:
        HTML page with Swagger UI
    """
    swagger_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alkhorayef ESP IoT Platform - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/swagger-ui.css">
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .topbar {
            background-color: #1b5e20 !important;
        }
        .swagger-ui .topbar .download-url-wrapper input[type=text] {
            border: 2px solid #1b5e20;
        }
        .swagger-ui .btn.authorize {
            background-color: #2e7d32;
            border-color: #2e7d32;
        }
        .swagger-ui .btn.authorize:hover {
            background-color: #1b5e20;
            border-color: #1b5e20;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>

    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/api/v1/openapi.yaml",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 3,
                docExpansion: "list",
                filter: true,
                showRequestHeaders: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                validatorUrl: null,
                // Custom configuration
                persistAuthorization: true,
                displayOperationId: true,
                displayRequestDuration: true,
                tryItOutEnabled: true
            });

            window.ui = ui;
        };
    </script>
</body>
</html>
    """
    return render_template_string(swagger_html)


# ReDoc endpoint (alternative documentation view)
@docs_bp.route("/redoc", methods=["GET"])
@docs_bp.route("/redoc/", methods=["GET"])
def redoc():
    """
    Serve ReDoc for alternative interactive API documentation.

    ReDoc provides a cleaner, more readable documentation interface
    compared to Swagger UI.

    Returns:
        HTML page with ReDoc
    """
    redoc_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alkhorayef ESP IoT Platform - API Documentation (ReDoc)</title>
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <redoc spec-url="/api/v1/openapi.yaml"></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
</body>
</html>
    """
    return render_template_string(redoc_html)


# API documentation landing page
@docs_bp.route("/docs/landing", methods=["GET"])
def docs_landing():
    """
    Landing page for API documentation with links to different views.

    Returns:
        HTML landing page
    """
    landing_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alkhorayef ESP IoT Platform - API Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            width: 100%;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .content {
            padding: 40px;
        }

        .section {
            margin-bottom: 40px;
        }

        .section h2 {
            color: #1b5e20;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .card {
            background: #f5f5f5;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 2px solid transparent;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
            border-color: #2e7d32;
        }

        .card h3 {
            color: #1b5e20;
            margin-bottom: 15px;
            font-size: 1.4em;
        }

        .card p {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.5;
        }

        .btn {
            display: inline-block;
            background: #2e7d32;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            transition: background 0.3s;
        }

        .btn:hover {
            background: #1b5e20;
        }

        .btn-secondary {
            background: #666;
        }

        .btn-secondary:hover {
            background: #444;
        }

        .features {
            list-style: none;
            padding: 0;
        }

        .features li {
            padding: 10px 0;
            padding-left: 30px;
            position: relative;
        }

        .features li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #2e7d32;
            font-weight: bold;
            font-size: 1.2em;
        }

        .footer {
            background: #f5f5f5;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }

        .footer a {
            color: #2e7d32;
            text-decoration: none;
            font-weight: 600;
        }

        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Alkhorayef ESP IoT Platform</h1>
            <p>Intelligent ESP Pump Monitoring & Diagnostics API</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>Interactive Documentation</h2>
                <div class="cards">
                    <div class="card">
                        <h3>Swagger UI</h3>
                        <p>Full-featured interactive API documentation with try-it-out functionality</p>
                        <a href="/api/v1/docs" class="btn">Open Swagger UI</a>
                    </div>

                    <div class="card">
                        <h3>ReDoc</h3>
                        <p>Clean, readable API documentation with responsive three-panel design</p>
                        <a href="/api/v1/redoc" class="btn">Open ReDoc</a>
                    </div>

                    <div class="card">
                        <h3>OpenAPI Spec</h3>
                        <p>Download the raw OpenAPI 3.0 specification file</p>
                        <a href="/api/v1/openapi.yaml" class="btn btn-secondary">Download YAML</a>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>API Features</h2>
                <ul class="features">
                    <li>Real-time ESP telemetry data ingestion (single and batch)</li>
                    <li>AI-powered diagnostic analysis using decision trees</li>
                    <li>Historical data queries with TimescaleDB optimization</li>
                    <li>Well summary statistics and aggregations</li>
                    <li>Kubernetes-style health checks (liveness, readiness, startup)</li>
                    <li>Production-ready error handling and validation</li>
                    <li>RESTful design with JSON responses</li>
                    <li>Comprehensive monitoring and observability</li>
                </ul>
            </div>

            <div class="section">
                <h2>Quick Links</h2>
                <div class="cards">
                    <div class="card">
                        <h3>Code Examples</h3>
                        <p>Python, cURL, and JavaScript examples</p>
                        <a href="/api/v1/examples" class="btn btn-secondary">View Examples</a>
                    </div>

                    <div class="card">
                        <h3>Health Check</h3>
                        <p>Verify API status and dependencies</p>
                        <a href="/health" class="btn btn-secondary">Check Health</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>&copy; 2025 INSA Automation | <a href="https://insaautomation.com">Website</a> | <a href="mailto:contact@insaautomation.com">Contact</a></p>
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(landing_html)
