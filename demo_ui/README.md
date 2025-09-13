# Demo UI Files

This directory contains demonstration HTML files for testing the Credit Approval API.

## Files

- `credit_approval_ui.html` - Simple UI for testing individual API endpoints
- `all_routes_demo.html` - Comprehensive demo showing all API routes and health checks

## Usage

1. Ensure the Django server is running: `docker compose up -d`
2. Start a simple HTTP server in this directory: `python -m http.server 8080`
3. Open `http://localhost:8080/demo_ui/` in your browser

These files are for development and testing purposes only and are not part of the production application.
