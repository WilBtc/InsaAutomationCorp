#!/bin/bash

# Alkhorayef ESP AI RAG System - Tailscale HTTPS Setup
# This script configures Tailscale for HTTPS access to the platform

set -e

echo "🔐 Alkhorayef ESP AI RAG - Tailscale HTTPS Setup"
echo "================================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script with sudo"
    exit 1
fi

# Variables
TAILSCALE_HOSTNAME="${TAILSCALE_HOSTNAME:-alkhorayef-esp}"
DOMAIN_SUFFIX="tail-scale.ts.net"
FULL_DOMAIN="${TAILSCALE_HOSTNAME}.${DOMAIN_SUFFIX}"
CERT_DIR="/etc/nginx/certs"
NGINX_DIR="./nginx/certs"

# Step 1: Install Tailscale if not already installed
echo "📦 Checking Tailscale installation..."
if ! command -v tailscale &> /dev/null; then
    echo "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
else
    echo "✅ Tailscale is already installed"
fi

# Step 2: Check Tailscale status
echo "🔍 Checking Tailscale connection..."
if ! tailscale status &> /dev/null; then
    echo "⚠️  Tailscale is not connected. Please authenticate first:"
    echo "Run: sudo tailscale up"
    echo "After authentication, run this script again."
    exit 1
fi

# Step 3: Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
if [ -z "$TAILSCALE_IP" ]; then
    echo "❌ Could not get Tailscale IP. Make sure Tailscale is connected."
    exit 1
fi

echo "✅ Tailscale IP: $TAILSCALE_IP"
echo "✅ Tailscale hostname: $FULL_DOMAIN"

# Step 4: Generate Tailscale certificates
echo "🔐 Generating Tailscale HTTPS certificates..."
mkdir -p "$CERT_DIR"
mkdir -p "$NGINX_DIR"

# Fetch certificates from Tailscale
tailscale cert \
    --cert-file="$CERT_DIR/cert.pem" \
    --key-file="$CERT_DIR/key.pem" \
    "$TAILSCALE_HOSTNAME" || {
    echo "❌ Failed to generate certificates"
    echo "Make sure MagicDNS and HTTPS certificates are enabled in your Tailscale admin console"
    exit 1
}

# Copy certificates to nginx directory
cp "$CERT_DIR/cert.pem" "$NGINX_DIR/cert.pem"
cp "$CERT_DIR/key.pem" "$NGINX_DIR/key.pem"

# Set proper permissions
chmod 644 "$NGINX_DIR/cert.pem"
chmod 600 "$NGINX_DIR/key.pem"

echo "✅ Certificates generated successfully"

# Step 5: Configure Tailscale Serve (optional, for direct access)
echo "🌐 Configuring Tailscale Serve..."
tailscale serve https / proxy 8000 || true
tailscale serve https /api proxy 8000 || true
tailscale serve https /grafana proxy 3000 || true
tailscale serve https /ws proxy 8000 || true

# Step 6: Update docker-compose environment
echo "📝 Updating environment configuration..."
cat > .env.tailscale << EOF
# Tailscale Configuration
TAILSCALE_IP=$TAILSCALE_IP
TAILSCALE_HOSTNAME=$TAILSCALE_HOSTNAME
TAILSCALE_DOMAIN=$FULL_DOMAIN
EOF

# Step 7: Display configuration
echo ""
echo "✅ Tailscale HTTPS setup complete!"
echo "===================================="
echo "Access URLs:"
echo "  - Platform: https://$FULL_DOMAIN"
echo "  - API: https://$FULL_DOMAIN/api"
echo "  - Grafana: https://$FULL_DOMAIN/grafana"
echo "  - WebSocket: wss://$FULL_DOMAIN/ws"
echo ""
echo "Internal Access:"
echo "  - Direct IP: https://$TAILSCALE_IP"
echo ""
echo "Next steps:"
echo "  1. Run: ./deploy-alkhorayef.sh"
echo "  2. Access the platform at https://$FULL_DOMAIN"
echo ""
echo "Note: Make sure your Tailscale network has:"
echo "  - MagicDNS enabled"
echo "  - HTTPS certificates enabled"
echo "  - Proper ACLs configured for access"