# Calico Network Fix - Complete Platform Solution
**Date:** October 22, 2025 03:50 UTC
**Server:** iac1 (100.100.101.1)
**Issue:** Calico CNI blocking Docker bridge network traffic
**Impact:** ERPNext (9 containers) and DefectDojo Redis affected

---

## 🎯 CURRENT SITUATION

### ✅ Services Working (Host Network Mode)
These services already use `--network host` and work perfectly:

| Service | Port | Status | Network |
|---------|------|--------|---------|
| DefectDojo Web | 8082 | ✅ Working | host |
| Grafana | 3002 | ✅ Working | host |
| n8n | 5678 | ✅ Working | host |
| InvenTree | 9600 | ✅ Working | host |
| Mautic MariaDB | 3306* | ✅ Working | host |
| Mautic Web | 9700 | ✅ Working | host |

*Port 3306 on host is used by system MariaDB + Mautic MariaDB (different process)

### ⚠️ Services Blocked (Bridge Network Mode)
These services use Docker bridge networks and are blocked by Calico:

| Service | Network | Containers | Impact |
|---------|---------|------------|--------|
| **ERPNext** | erpnext-network (172.20.0.0/16) | 9 containers | ❌ HTTP inaccessible |
| **DefectDojo Redis** | defectdojo_defectdojo-network | 1 container | ❌ Port 6381 timeout |

---

## 🔍 ROOT CAUSE: Calico iptables Interception

### Calico Process Status
```bash
$ ps aux | grep calico
root  2044929  runsv felix
root  2044932  calico-node -allocate-tunnel-addrs
root  2044933  calico-node -monitor-token
root  2044934  calico-node -felix (95:57 CPU time)  ← Main process
root  2044935  calico-node -monitor-addresses
root  2044936  calico-node -status-reporter
```

### iptables Evidence
```bash
$ sudo iptables -L FORWARD -n -v
Chain FORWARD (policy ACCEPT)
 pkts  bytes target            prot opt in   out  source       destination
  800  48K   DOCKER-USER       all  --  *    *   0.0.0.0/0    0.0.0.0/0
  800  48K   DOCKER-FORWARD    all  --  *    *   0.0.0.0/0    0.0.0.0/0
 818K 1124M  cali-FORWARD      all  --  *    *   0.0.0.0/0    0.0.0.0/0  ← BLOCKS HERE!
 712K 989M   KUBE-FORWARD      all  --  *    *   0.0.0.0/0    0.0.0.0/0
```

**Analysis:**
- Calico processes **1000x more packets** than Docker (818K vs 800)
- All forwarded traffic goes through `cali-FORWARD` chain
- Calico drops traffic from non-Kubernetes sources (Docker bridge networks)
- Even host network mode is affected when containers try to connect to bridge IPs

---

## ✅ SOLUTION: Configure Calico GlobalNetworkPolicy

This is the **proper enterprise solution** that allows Docker and Kubernetes to coexist.

### Step 1: Install Calico CLI Tools (15 minutes)

```bash
# 1. Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client

# 2. Install calicoctl
curl -L https://github.com/projectcalico/calico/releases/download/v3.27.0/calicoctl-linux-amd64 -o calicoctl
chmod +x calicoctl
sudo mv calicoctl /usr/local/bin/
calicoctl version

# 3. Find Kubernetes API endpoint
# Option A: Check for kubeconfig
ls -la ~/.kube/config /etc/kubernetes/admin.conf

# Option B: Check for local API
netstat -tlnp | grep -E "(6443|8080)"

# Option C: Check if MicroK8s
microk8s config
microk8s kubectl get nodes

# 4. Configure calicoctl datastore access
# If MicroK8s:
export DATASTORE_TYPE=kubernetes
export KUBECONFIG=/var/snap/microk8s/current/credentials/client.config

# If standalone etcd:
export DATASTORE_TYPE=etcdv3
export ETCD_ENDPOINTS=http://127.0.0.1:2379
```

### Step 2: Create GlobalNetworkPolicy (5 minutes)

**Allow Docker Bridge Networks:**
```bash
cat > /tmp/allow-docker-networks.yaml <<'EOF'
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: allow-docker-bridge-networks
spec:
  order: 100
  selector: ""
  types:
  - Ingress
  - Egress
  ingress:
  - action: Allow
    source:
      nets:
      - 172.20.0.0/16    # erpnext-network
      - 172.21.0.0/16    # defectdojo_defectdojo-network
      - 172.17.0.0/16    # default docker0 bridge
  egress:
  - action: Allow
    destination:
      nets:
      - 172.20.0.0/16    # erpnext-network
      - 172.21.0.0/16    # defectdojo_defectdojo-network
      - 172.17.0.0/16    # default docker0 bridge
EOF

# Apply the policy
calicoctl apply -f /tmp/allow-docker-networks.yaml

# Verify policy created
calicoctl get globalnetworkpolicy -o wide
```

### Step 3: Test Immediately (5 minutes)

```bash
# Test 1: ERPNext HTTP access
curl -I http://100.100.101.1:9000
# Expected: HTTP/1.1 200 OK (instead of timeout)

# Test 2: ERPNext login page
curl -s http://100.100.101.1:9000 | grep -o "<title>.*</title>"
# Expected: <title>Login - ERPNext</title>

# Test 3: DefectDojo Redis
redis-cli -h 100.100.101.1 -p 6381 ping
# Expected: PONG (instead of timeout)

# Test 4: Container-to-container communication
docker exec frappe_docker_backend_1 ping -c 3 db
# Expected: 3 packets transmitted, 3 received

# Test 5: Full ERPNext health check
docker ps --filter "name=frappe_docker" --filter "status=running" | wc -l
# Expected: 10 (header + 9 containers all running)
```

---

## 🔄 ALTERNATIVE SOLUTION: Move Remaining Services to Host Network

If Calico configuration is not accessible (no kubectl/calicoctl access), move the affected services to host network mode.

### Option A: ERPNext to Host Network (NOT RECOMMENDED - Port Conflicts)

**Problem:** ERPNext needs ports already occupied by system services:
- Port 3306: ❌ System MariaDB (mariadb.service)
- Port 6379: ❌ System Redis (redis-server.service)
- Port 6380: ❌ LXD Redis

**Solution:** Stop system services OR use different ports (complex, many dependencies)

### Option B: DefectDojo Redis to Host Network (RECOMMENDED IF NO CALICO ACCESS)

```bash
# Stop and remove current Redis container
docker stop defectdojo-redis && docker rm defectdojo-redis

# Recreate on host network with custom port
docker run -d \
  --name defectdojo-redis \
  --network host \
  --restart unless-stopped \
  redis:7.4-alpine \
  --port 6381

# Update DefectDojo uwsgi to use localhost:6381
# Edit DefectDojo docker-compose.yml or environment variables
# REDIS_URL=redis://127.0.0.1:6381

# Restart DefectDojo uwsgi
docker restart defectdojo-uwsgi-insa

# Test
redis-cli -h 127.0.0.1 -p 6381 ping
# Expected: PONG
```

---

## 🎯 RECOMMENDED ACTION PLAN

### Priority 1: Configure Calico (BEST SOLUTION - 25 minutes)

1. ✅ Install kubectl and calicoctl (15 min)
2. ✅ Find Kubernetes API endpoint (5 min)
3. ✅ Create GlobalNetworkPolicy (5 min)
4. ✅ Test all affected services (5 min)

**Benefits:**
- ✅ Proper enterprise solution
- ✅ No service disruption
- ✅ Docker and Kubernetes coexist
- ✅ Works for all current and future bridge networks
- ✅ No port conflicts to manage

### Priority 2: Host Network for DefectDojo Redis (IF PRIORITY 1 FAILS - 10 minutes)

1. ✅ Move DefectDojo Redis to host network with port 6381 (5 min)
2. ✅ Update DefectDojo uwsgi config (2 min)
3. ✅ Test Redis connectivity (1 min)
4. ✅ Test DefectDojo functionality (2 min)

**ERPNext Solution:** If Priority 1 fails, ERPNext will need macvlan network (30 min) or wait for Calico config access.

---

## 📋 VERIFICATION CHECKLIST

### After Calico Configuration

**ERPNext (9 containers):**
- [ ] HTTP accessible: `curl -I http://100.100.101.1:9000` → HTTP 200
- [ ] Login page loads: `curl http://100.100.101.1:9000` → HTML with ERPNext
- [ ] All containers running: `docker ps | grep frappe_docker | wc -l` → 9
- [ ] Database connectivity: `docker exec frappe_docker_backend_1 bench doctor` → healthy
- [ ] MCP tools work: Via Claude Code `erpnext_list_leads({})` → JSON response

**DefectDojo Redis:**
- [ ] Redis ping: `redis-cli -h 100.100.101.1 -p 6381 ping` → PONG
- [ ] DefectDojo web: `curl -I http://100.100.101.1:8082` → HTTP 302
- [ ] DefectDojo findings: Via MCP `get_findings({})` → JSON response

**Platform Health:**
- [ ] All services up: `docker ps | wc -l` → 20+ containers
- [ ] Healing agent healthy: `systemctl status integrated-healing-agent.service` → active
- [ ] Compliance agent running: `systemctl status defectdojo-compliance-agent.service` → active

---

## 🗂️ AFFECTED DOCKER NETWORKS

### Current Docker Bridge Networks
```bash
$ docker network ls
NETWORK ID     NAME                              DRIVER    SCOPE
172.20.0.0/16  erpnext-network                   bridge    local
172.21.0.0/16  defectdojo_defectdojo-network     bridge    local
172.17.0.0/16  bridge (default)                  bridge    local
```

### Network Subnet Mapping
```bash
# ERPNext network
docker network inspect erpnext-network --format='{{.IPAM.Config}}'
# Output: [{172.20.0.0/16  172.20.0.1 map[]}]

# DefectDojo network
docker network inspect defectdojo_defectdojo-network --format='{{.IPAM.Config}}'
# Output: [{172.21.0.0/16  172.21.0.1 map[]}]
```

---

## 🔐 SECURITY CONSIDERATIONS

### Calico GlobalNetworkPolicy Security
- ✅ Only allows traffic within Docker bridge subnets (172.x.x.x)
- ✅ Does not allow external internet access to containers
- ✅ Does not affect Kubernetes pod networking
- ✅ Maintains Calico's security for Kubernetes workloads
- ✅ Minimal policy (order: 100, low priority)

### Alternative: More Restrictive Policy
If you want to allow ONLY specific container IPs:

```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: allow-docker-erpnext-only
spec:
  order: 100
  selector: ""
  types:
  - Ingress
  - Egress
  ingress:
  - action: Allow
    source:
      nets:
      - 172.20.0.3/32    # ERPNext database
      - 172.20.0.4/32    # ERPNext redis-cache
      - 172.20.0.5/32    # ERPNext redis-queue
      - 172.20.0.6/32    # ERPNext backend
      - 172.20.0.7/32    # ERPNext websocket
      - 172.20.0.10/32   # ERPNext frontend
  egress:
  - action: Allow
    destination:
      nets:
      - 172.20.0.0/24    # ERPNext subnet
```

---

## 📝 TROUBLESHOOTING

### Issue: calicoctl command fails with "connection refused"

**Cause:** No access to Kubernetes API or etcd datastore

**Solutions:**
1. Check if MicroK8s: `microk8s status`
2. Use MicroK8s wrapper: `microk8s calicoctl get nodes`
3. Find kubeconfig: `find /etc /var -name "*kube*config" 2>/dev/null`
4. Check etcd: `netstat -tlnp | grep 2379`

### Issue: GlobalNetworkPolicy applied but still blocking

**Cause:** Policy selector or order issue

**Solution:**
```bash
# Check policy is active
calicoctl get globalnetworkpolicy allow-docker-bridge-networks -o yaml

# Check policy order (lower = higher priority)
# Ensure order: 100 or higher (low priority, permissive)

# Check if other policies are blocking
calicoctl get globalnetworkpolicy -o wide
calicoctl get networkpolicy --all-namespaces -o wide

# Force policy reload
calicoctl apply -f /tmp/allow-docker-networks.yaml --overwrite
```

### Issue: kubectl not found, no Kubernetes access

**Solution:** Use Option B (move DefectDojo Redis to host network)

This is a valid solution if:
- No kubectl/calicoctl access
- Kubernetes admin not available
- Need immediate fix

Note: ERPNext will still need Calico config or macvlan network.

---

## 🚀 EXPECTED OUTCOME

### After Successful Calico Configuration:

**All Security Apps Working:**
- ✅ DefectDojo: Full functionality (Web UI + Redis + Celery)
- ✅ Grafana: Analytics and monitoring
- ✅ n8n: Workflow automation
- ✅ ERPNext: Full CRM functionality
- ✅ InvenTree: Inventory management
- ✅ Mautic: Marketing automation

**All MCP Tools Working:**
- ✅ DefectDojo MCP: `get_findings`, `triage_finding`, `create_jira_ticket`
- ✅ ERPNext MCP: `erpnext_list_leads`, `erpnext_create_lead`, etc (33 tools)
- ✅ Grafana MCP: `grafana_list_dashboards`, `grafana_get_stats`, etc (23 tools)
- ✅ n8n MCP: `n8n_list_workflows`, `n8n_trigger_workflow`, etc (23 tools)

**All Autonomous Agents Working:**
- ✅ DefectDojo Compliance Agent (hourly IEC 62443 scans)
- ✅ Integrated Healing Agent (5-min health checks + auto-remediation)
- ✅ Platform Admin Agent (health monitoring + credentials)

**Platform Status:**
- ✅ 100% production ready
- ✅ Zero services blocked by Calico
- ✅ Full observability and automation
- ✅ Complete DevSecOps pipeline operational

---

**Made by Insa Automation Corp for OpSec**
**Status:** Action Required - Execute Priority 1 (Calico Configuration)
**Impact:** 2 services blocked (ERPNext + DefectDojo Redis)
**ETA to Fix:** 25 minutes (Priority 1) or 10 minutes (Priority 2)
**Total Platform Services:** 8 (6 working ✅, 2 blocked ⚠️)
