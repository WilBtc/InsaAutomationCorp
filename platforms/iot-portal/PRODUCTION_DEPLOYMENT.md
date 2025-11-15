# INSA IoT Platform - Production Deployment Guide

Complete guide for deploying the INSA IoT Platform API to production using Docker, Kubernetes, or Helm.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development (SQLite)](#local-development-sqlite)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Helm Deployment](#helm-deployment)
6. [Database Migration](#database-migration)
7. [Authentication Setup](#authentication-setup)
8. [Monitoring & Observability](#monitoring--observability)
9. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### Required Software

- **Python 3.11+** (for local development)
- **Docker 24+** and **Docker Compose 2.0+** (for containerized deployment)
- **Kubernetes 1.27+** and **kubectl** (for K8s deployment)
- **Helm 3.12+** (for Helm deployment)
- **PostgreSQL 15+** (for production database)

### Required Credentials

Generate secure secrets for:
- `JWT_SECRET_KEY` (min 32 characters)
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`

```bash
# Generate secure random keys
openssl rand -base64 32  # For JWT_SECRET_KEY
openssl rand -base64 24  # For database passwords
```

---

## 1. Local Development (SQLite)

Perfect for testing and development without Docker.

### Step 1: Install Dependencies

```bash
cd iot-platform/backend
pip install -r requirements.txt
```

### Step 2: Set Environment Variables

```bash
# Use SQLite (default)
export DATABASE_URL="sqlite+aiosqlite:///./iot_platform.db"
export JWT_SECRET_KEY="your-dev-secret-key"
export ENVIRONMENT="development"
```

### Step 3: Run the Application

```bash
python app_production.py
```

Visit:
- API Docs: http://localhost:8000/api/docs
- Settings Page: http://localhost:8000/settings

### Demo Login

Email: `demo@insa-iot.com`
Password: `demo123`

---

## 2. Docker Deployment

Deploy the full stack with PostgreSQL, Redis, and the API using Docker Compose.

### Step 1: Configure Environment

Create `.env` file in project root:

```env
# Database
POSTGRES_USER=iot_user
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=iot_platform

# Redis
REDIS_PASSWORD=your-redis-password

# JWT
JWT_SECRET_KEY=your-secure-32-char-key-minimum

# Application
ENVIRONMENT=production
LOG_LEVEL=info
CORS_ORIGINS=https://your-domain.com

# Ports
API_PORT=8001
```

### Step 2: Build and Run

Using the API-specific compose file:

```bash
# Create network (if using existing postgres/redis)
docker network create insa-iot-network

# Start API stack
docker compose -f docker-compose.api.yml up -d

# View logs
docker compose -f docker-compose.api.yml logs -f api
```

Using full stack (includes Prometheus, Grafana, MQTT):

```bash
docker compose up -d
```

### Step 3: Run Database Migration

```bash
# Copy migration SQL into running postgres container
docker exec -i insa-iot-db psql -U iot_user -d iot_platform < iot-platform/migrations/002_user_settings_and_sessions.sql
```

### Step 4: Verify Deployment

```bash
curl http://localhost:8001/health
```

---

## 3. Kubernetes Deployment

Deploy to Kubernetes cluster using raw manifests.

### Step 1: Update Secrets

Edit `kubernetes/base/secret.yaml` with production credentials:

```yaml
stringData:
  POSTGRES_PASSWORD: "YOUR-PRODUCTION-PASSWORD"
  REDIS_PASSWORD: "YOUR-PRODUCTION-PASSWORD"
  JWT_SECRET_KEY: "YOUR-PRODUCTION-JWT-SECRET-32-CHARS"
```

**IMPORTANT**: In production, use external secret management:
- **AWS**: AWS Secrets Manager + External Secrets Operator
- **Azure**: Azure Key Vault + CSI Driver
- **GCP**: Google Secret Manager
- **HashiCorp**: Vault

### Step 2: Update Ingress Hostname

Edit `kubernetes/base/ingress.yaml`:

```yaml
spec:
  tls:
  - hosts:
    - api.your-domain.com  # <-- Change this
    secretName: insa-iot-api-tls
  rules:
  - host: api.your-domain.com  # <-- Change this
```

### Step 3: Deploy with Kustomize

```bash
# Deploy to cluster
kubectl apply -k kubernetes/base/

# Watch deployment
kubectl get pods -n insa-iot -w

# Check status
kubectl get all -n insa-iot
```

### Step 4: Verify Deployment

```bash
# Check pods
kubectl get pods -n insa-iot

# View logs
kubectl logs -n insa-iot deployment/insa-iot-api -f

# Test health endpoint
kubectl port-forward -n insa-iot svc/insa-iot-api-service 8000:80
curl http://localhost:8000/health
```

### Step 5: Access via Ingress

```bash
# Get ingress IP
kubectl get ingress -n insa-iot

# Access API
curl https://api.your-domain.com/health
```

---

## 4. Helm Deployment

Deploy using Helm chart (recommended for production).

### Step 1: Create Production Values

Create `values-production.yaml`:

```yaml
image:
  repository: your-registry.com/insa-iot/api
  tag: "3.0.0"

replicaCount: 5

ingress:
  enabled: true
  hosts:
    - host: api.your-domain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: insa-iot-api-tls
      hosts:
        - api.your-domain.com

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 50

config:
  environment: production
  logLevel: warning
  corsOrigins: "https://your-domain.com"

secrets:
  postgresPassword: "YOUR-SECURE-PASSWORD"
  redisPassword: "YOUR-SECURE-PASSWORD"
  jwtSecretKey: "YOUR-SECURE-32-CHAR-KEY"
  databaseUrl: "postgresql+asyncpg://iot_user:PASSWORD@postgres-service:5432/iot_platform"
  redisUrl: "redis://:PASSWORD@redis-service:6379/1"
```

### Step 2: Install Chart

```bash
# Add Helm repository (if published)
helm repo add insa-iot https://charts.insa-iot.com
helm repo update

# Install from repository
helm install insa-iot-api insa-iot/insa-iot-api \
  -f values-production.yaml \
  --namespace insa-iot \
  --create-namespace

# OR install from local chart
helm install insa-iot-api ./helm/insa-iot-api \
  -f values-production.yaml \
  --namespace insa-iot \
  --create-namespace
```

### Step 3: Upgrade Deployment

```bash
# Upgrade with new values
helm upgrade insa-iot-api ./helm/insa-iot-api \
  -f values-production.yaml \
  --namespace insa-iot

# Rollback if needed
helm rollback insa-iot-api --namespace insa-iot
```

### Step 4: Verify Helm Release

```bash
# List releases
helm list -n insa-iot

# Get status
helm status insa-iot-api -n insa-iot

# Get values
helm get values insa-iot-api -n insa-iot
```

---

## 5. Database Migration

### PostgreSQL Setup

#### Option A: Using psql

```bash
# Connect to PostgreSQL
psql -h localhost -U iot_user -d iot_platform

# Run migration
\i iot-platform/migrations/002_user_settings_and_sessions.sql

# Verify tables
\dt
```

#### Option B: Using Docker

```bash
docker exec -i insa-iot-db psql -U iot_user -d iot_platform < iot-platform/migrations/002_user_settings_and_sessions.sql
```

#### Option C: Using Kubernetes

```bash
kubectl cp iot-platform/migrations/002_user_settings_and_sessions.sql \
  insa-iot/postgres-pod:/tmp/migration.sql

kubectl exec -it -n insa-iot postgres-pod -- \
  psql -U iot_user -d iot_platform -f /tmp/migration.sql
```

### Verify Migration

```sql
-- Check tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Should see:
-- - user_preferences
-- - user_sessions
-- - data_exports
-- - notification_preferences
-- - api_keys
-- - user_activity_log
```

---

## 6. Authentication Setup

### JWT (Default)

Simple JWT-based authentication with user/password.

**Configuration:**

```yaml
config:
  jwtAlgorithm: HS256
  accessTokenExpireMinutes: 30
secrets:
  jwtSecretKey: "YOUR-SECURE-KEY"
```

**Usage:**

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@insa-iot.com", "password": "demo123"}'

# Returns:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer"
# }

# Use token
curl -H "Authorization: Bearer eyJ..." \
  http://localhost:8000/auth/me
```

### Keycloak Integration (Optional)

For enterprise SSO and OAuth2/OIDC.

#### Step 1: Deploy Keycloak

```bash
# Using Docker Compose profile
docker compose -f docker-compose.api.yml --profile with-keycloak up -d keycloak
```

#### Step 2: Configure Keycloak

1. Access Keycloak: http://localhost:8080
2. Login with admin credentials
3. Create realm: `insa-iot`
4. Create client: `iot-platform`
   - Client authentication: ON
   - Valid redirect URIs: `https://api.your-domain.com/*`
5. Copy client secret

#### Step 3: Enable in API

```yaml
config:
  keycloakEnabled: true
secrets:
  keycloakServerUrl: "http://keycloak:8080"
  keycloakRealm: "insa-iot"
  keycloakClientId: "iot-platform"
  keycloakClientSecret: "YOUR-CLIENT-SECRET"
```

---

## 7. Monitoring & Observability

### Health Checks

```bash
# Liveness probe (is app alive?)
curl http://localhost:8000/health

# Readiness probe (can accept traffic?)
curl http://localhost:8000/ready
```

### Metrics (Prometheus)

API exposes Prometheus metrics at `/metrics` (if configured).

### Logging

**Structured JSON logging:**

```json
{
  "timestamp": "2025-11-15T21:30:00Z",
  "level": "INFO",
  "message": "Request completed",
  "path": "/api/v1/user/preferences/",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 45
}
```

**View logs:**

```bash
# Docker
docker compose logs -f api

# Kubernetes
kubectl logs -f deployment/insa-iot-api -n insa-iot

# Follow last 100 lines
kubectl logs --tail=100 -f deployment/insa-iot-api -n insa-iot
```

---

## 8. Security Best Practices

### 1. Secrets Management

**Never commit secrets to Git!**

Use:
- Kubernetes Secrets with encryption at rest
- External Secrets Operator
- HashiCorp Vault
- Cloud provider secret managers

### 2. Network Security

```yaml
# Network Policies (Kubernetes)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: insa-iot-api-netpol
spec:
  podSelector:
    matchLabels:
      app: insa-iot-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### 3. HTTPS/TLS

**cert-manager for automatic TLS:**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 4. Container Security

- Run as non-root user ✅ (already configured)
- Use minimal base images ✅ (python:3.11-slim)
- Scan images for vulnerabilities
- Implement pod security policies/admission controllers

### 5. Rate Limiting

Configured in Ingress:

```yaml
annotations:
  nginx.ingress.kubernetes.io/limit-rps: "100"
  nginx.ingress.kubernetes.io/limit-connections: "50"
```

---

## Quick Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite+aiosqlite:///./iot_platform.db` |
| `REDIS_URL` | Redis connection string | - |
| `JWT_SECRET_KEY` | Secret for JWT signing | - |
| `ENVIRONMENT` | Environment (dev/staging/prod) | `development` |
| `LOG_LEVEL` | Logging level | `info` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Ports

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| Keycloak | 8080 | Identity server |

### Useful Commands

```bash
# Docker: Restart API
docker compose restart api

# Docker: View database logs
docker compose logs -f postgres

# K8s: Scale deployment
kubectl scale deployment insa-iot-api --replicas=10 -n insa-iot

# K8s: Execute command in pod
kubectl exec -it -n insa-iot deployment/insa-iot-api -- bash

# Helm: Get all values
helm get values insa-iot-api -n insa-iot --all

# Check API version
curl http://localhost:8000/ | jq '.version'
```

---

## Troubleshooting

### API won't start

1. Check logs: `docker compose logs api` or `kubectl logs -f deployment/insa-iot-api`
2. Verify database connection: Check `DATABASE_URL`
3. Ensure migrations ran: Connect to DB and check tables exist

### Database connection fails

1. Check database is running: `docker ps | grep postgres`
2. Verify credentials in secrets
3. Test connection: `psql -h localhost -U iot_user -d iot_platform`

### 502 Bad Gateway

1. Check API is healthy: `curl http://localhost:8000/health`
2. Verify service endpoints: `kubectl get endpoints -n insa-iot`
3. Check readiness probe: Might be failing

### Authentication fails

1. Verify JWT_SECRET_KEY is set and consistent
2. Check token hasn't expired
3. Ensure Authorization header format: `Bearer <token>`

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/insa-iot/platform/issues
- Documentation: https://docs.insa-iot.com
- Email: support@insa-iot.com

---

**Congratulations! Your INSA IoT Platform API is now running in production!** 🎉
