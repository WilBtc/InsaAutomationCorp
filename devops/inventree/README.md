# InvenTree Deployment for INSA Automation

**Deployed:** October 17, 2025
**Version:** InvenTree 0.16.6
**Purpose:** Inventory management and BOM tracking for industrial automation projects

---

## 🚀 Quick Start

```bash
# Deploy InvenTree
cd ~/devops/inventree
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f inventree-web

# Stop InvenTree
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

---

## 📊 Access Information

```yaml
Web UI: http://100.100.101.1:9600
API Endpoint: http://100.100.101.1:9600/api/
Admin User: admin
Admin Password: insaadmin2025
Admin Email: w.aroca@insaing.com

Database:
  Type: PostgreSQL 16
  Name: inventree
  User: inventree
  Password: inventree_secure_2025
  Host: inventree-db (internal)
  Port: 5432

Cache:
  Type: Redis 7
  Host: inventree-redis (internal)
  Port: 6379
```

---

## 🔧 API Authentication

InvenTree uses token-based authentication:

```bash
# Get API token
curl -X POST http://100.100.101.1:9600/api/user/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "insaadmin2025"}'

# Response
{
  "token": "YOUR_API_TOKEN_HERE"
}

# Use token in subsequent requests
curl http://100.100.101.1:9600/api/part/ \
  -H "Authorization: Token YOUR_API_TOKEN_HERE"
```

---

## 📦 Key API Endpoints

### Parts Management
- `GET /api/part/` - List all parts
- `GET /api/part/{id}/` - Get part details
- `POST /api/part/` - Create new part
- `PUT /api/part/{id}/` - Update part
- `DELETE /api/part/{id}/` - Delete part

### Bill of Materials (BOM)
- `GET /api/bom/` - List BOM items
- `GET /api/bom/{id}/` - Get BOM details
- `POST /api/bom/` - Create BOM item
- `PUT /api/bom/{id}/` - Update BOM item

### Stock Management
- `GET /api/stock/` - List stock items
- `GET /api/stock/location/` - List storage locations
- `POST /api/stock/` - Create stock item
- `POST /api/stock/transfer/` - Transfer stock

### Purchase Orders
- `GET /api/order/po/` - List purchase orders
- `POST /api/order/po/` - Create purchase order
- `GET /api/order/po/{id}/` - Get PO details

### Sales Orders
- `GET /api/order/so/` - List sales orders
- `POST /api/order/so/` - Create sales order
- `GET /api/order/so/{id}/` - Get SO details

### Manufacturers & Suppliers
- `GET /api/company/` - List companies
- `GET /api/company/manufacturer/` - List manufacturers
- `GET /api/company/supplier/` - List suppliers

---

## 🏭 INSA Use Cases

### 1. Industrial Control Panel BOM
Track all components for a control panel project:
- PLCs (Siemens S7-1200, Allen-Bradley)
- Relays, contactors, circuit breakers
- Sensors (pressure, temperature, flow)
- HMI displays
- Cables, terminals, enclosures

### 2. Customer Equipment Tracking
Associate equipment installations with customers:
- Link parts to ERPNext customers
- Track serial numbers and warranties
- Schedule maintenance based on installed equipment

### 3. Project Costing
Generate accurate project quotes:
- Pull parts from InvenTree inventory
- Get current pricing with supplier data
- Calculate total BOM cost + labor
- Export to ERPNext quotation

### 4. Stock Management
Monitor inventory levels:
- Set minimum stock levels for critical components
- Generate purchase orders when stock is low
- Track stock across multiple locations

---

## 🔄 Integration with ERPNext

InvenTree will integrate with ERPNext CRM via MCP server:

```python
# MCP Tools (to be implemented)
1. list_parts() - Query parts inventory
2. get_part_details(part_id) - Get specifications, stock, pricing
3. create_bom(project_data) - Create BOM for won opportunity
4. get_pricing(parts_list) - Calculate total cost for quotation
5. track_customer_equipment(customer_id) - List installed equipment
```

Integration Flow:
1. Sales team creates opportunity in ERPNext
2. Engineer designs solution, creates BOM in InvenTree
3. Quote generation agent calculates pricing from InvenTree
4. Sales team sends quote via ERPNext
5. Upon order, InvenTree tracks stock allocation

---

## 🛡️ Security Notes

**Current Configuration:**
- Default admin credentials (CHANGE IN PRODUCTION)
- Local network access only (100.100.101.1)
- No HTTPS (behind Tailscale VPN)

**Production Hardening (TODO):**
- [ ] Change admin password via UI
- [ ] Create individual user accounts for team
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Configure backup automation
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Enable audit logging

---

## 📈 Next Steps

1. **Deploy container:** `docker-compose up -d`
2. **Verify web UI:** http://100.100.101.1:9600
3. **Initialize database:** Auto-migrates on first start
4. **Create sample parts:** Add test components via UI
5. **Build MCP server:** ~/mcp-servers/inventree-crm/server.py
6. **Test API:** Verify token auth and endpoints
7. **Document integration:** Update CLAUDE.md

---

## 🐛 Troubleshooting

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs inventree-web
docker-compose logs inventree-db

# Restart services
docker-compose restart

# Access container shell
docker exec -it inventree_web /bin/bash

# Database connection test
docker exec -it inventree_postgres psql -U inventree -d inventree

# Redis connection test
docker exec -it inventree_redis redis-cli ping
```

---

**Deployed by:** Claude Code (INSA Automation DevSecOps)
**Maintained by:** w.aroca@insaing.com
**Documentation:** https://docs.inventree.org/
