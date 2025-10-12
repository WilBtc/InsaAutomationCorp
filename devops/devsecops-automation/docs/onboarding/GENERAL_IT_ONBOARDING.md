# General IT Infrastructure - Client Onboarding Playbook
**Insa Automation Corp | Enterprise IT Security**
Version: 1.0 | Date: October 11, 2025

---

## Executive Summary

General IT infrastructure encompasses traditional enterprise networks, cloud workloads, containerized applications, and modern DevOps environments. This playbook addresses onboarding for organizations without specialized OT/ICS requirements.

### Sector Characteristics
- **Critical Priority**: Business continuity, data protection, compliance
- **Key Assets**: Servers, databases, applications, cloud workloads, endpoints
- **Common Technologies**: Linux, Windows, Kubernetes, Docker, AWS/Azure/GCP, CI/CD pipelines
- **Risk Profile**: Ransomware, data breach, insider threats, supply chain attacks
- **Compliance**: SOC 2, ISO 27001, PCI-DSS, GDPR, HIPAA, FedRAMP
- **Modern Challenge**: Hybrid cloud, container orchestration, DevSecOps integration

---

## Phase 1: Pre-Sales Discovery

### Discovery Questionnaire

#### Organization Profile
```yaml
Company Type:
  [ ] SaaS/Software Company
  [ ] Financial Services
  [ ] Healthcare/Pharma
  [ ] Retail/E-commerce
  [ ] Professional Services
  [ ] Managed Service Provider (MSP)
  [ ] Government/Public Sector
  [ ] Education
  [ ] Other: _______

Organization Size:
  - Employees: _______
  - IT team size: _______
  - Annual revenue: $_______ million
  - Geographic presence: [ ] Single location [ ] Multi-site [ ] Global

Business Model:
  [ ] B2B (Business-to-Business)
  [ ] B2C (Business-to-Consumer)
  [ ] B2B2C (Platform)
  [ ] Internal IT (non-customer facing)
```

#### IT Infrastructure Inventory
```yaml
On-Premises Data Center:
  [ ] Owned data center
  [ ] Colocation facility (colo)
  [ ] None (cloud-only)

  If present:
    - Server count: _____ (physical), _____ (virtual)
    - Hypervisor: [ ] VMware vSphere [ ] Microsoft Hyper-V [ ] Proxmox [ ] KVM [ ] Nutanix
    - Storage: _____ TB (SAN, NAS)
    - Network: [ ] Cisco [ ] Juniper [ ] Arista [ ] Ubiquiti [ ] Other: _______

Cloud Infrastructure:
  [ ] Amazon Web Services (AWS)
      - Regions: _______
      - VPCs: _____
      - EC2 instances: _____
      - Services: [ ] RDS [ ] S3 [ ] Lambda [ ] EKS [ ] Other: _______

  [ ] Microsoft Azure
      - Subscriptions: _____
      - Resource Groups: _____
      - VMs: _____
      - Services: [ ] SQL DB [ ] Blob Storage [ ] Functions [ ] AKS [ ] Other: _______

  [ ] Google Cloud Platform (GCP)
      - Projects: _____
      - Compute Engine: _____
      - Services: [ ] Cloud SQL [ ] Cloud Storage [ ] Cloud Functions [ ] GKE [ ] Other: _______

  [ ] Private Cloud (OpenStack, CloudStack)
  [ ] Hybrid Cloud (mix of on-prem + public cloud)

Multi-Cloud:
  [ ] Single cloud provider (e.g., AWS only)
  [ ] Multi-cloud (e.g., AWS + Azure)
  - Primary: _______
  - Secondary: _______
  - Rationale: [ ] Redundancy [ ] Cost [ ] Vendor lock-in avoidance [ ] Compliance
```

#### Application Portfolio
```yaml
Enterprise Applications:
  [ ] ERP: [ ] SAP [ ] Oracle [ ] Microsoft Dynamics [ ] NetSuite [ ] Custom
  [ ] CRM: [ ] Salesforce [ ] HubSpot [ ] Microsoft Dynamics [ ] Custom
  [ ] Email: [ ] Microsoft 365 [ ] Google Workspace [ ] On-prem Exchange [ ] Other
  [ ] Collaboration: [ ] Slack [ ] Microsoft Teams [ ] Zoom [ ] Other

Custom Applications:
  - Web applications: _____ (production)
  - APIs/Microservices: _____
  - Mobile apps: [ ] iOS [ ] Android [ ] Both
  - Tech stack:
      - Frontend: [ ] React [ ] Angular [ ] Vue [ ] Other: _______
      - Backend: [ ] Node.js [ ] Python [ ] Java [ ] .NET [ ] Go [ ] Ruby [ ] PHP
      - Databases: [ ] PostgreSQL [ ] MySQL [ ] MongoDB [ ] Oracle [ ] SQL Server [ ] Redis

DevOps/CI-CD:
  [ ] GitLab (self-hosted or SaaS)
  [ ] GitHub (Enterprise or Cloud)
  [ ] Jenkins
  [ ] CircleCI
  [ ] Travis CI
  [ ] Argo CD (GitOps)
  [ ] Spinnaker

  Build frequency: [ ] Continuous [ ] Daily [ ] Weekly [ ] Ad-hoc
  Deployment strategy: [ ] Blue-green [ ] Canary [ ] Rolling [ ] Recreate
```

#### Container & Orchestration
```yaml
Containerization:
  [ ] Docker
  [ ] Podman
  [ ] containerd
  - Container registries:
      [ ] Docker Hub (public)
      [ ] Amazon ECR (private)
      [ ] Azure Container Registry
      [ ] Google Container Registry
      [ ] JFrog Artifactory
      [ ] Harbor (self-hosted)

Orchestration:
  [ ] Kubernetes
      - Distribution: [ ] Vanilla [ ] EKS (AWS) [ ] AKS (Azure) [ ] GKE (GCP) [ ] OpenShift [ ] Rancher
      - Clusters: _____ (production), _____ (staging), _____ (dev)
      - Nodes: _____ (per cluster average)
      - Namespaces: _____ (multi-tenancy)

  [ ] Docker Swarm
  [ ] HashiCorp Nomad
  [ ] Amazon ECS (Elastic Container Service)

Service Mesh:
  [ ] Istio
  [ ] Linkerd
  [ ] Consul Connect
  [ ] AWS App Mesh
  [ ] None

Container Security:
  - Image scanning: [ ] Trivy [ ] Clair [ ] Snyk [ ] Aqua [ ] Prisma Cloud [ ] None
  - Runtime security: [ ] Falco [ ] Sysdig [ ] Aqua [ ] Prisma Cloud [ ] None
  - Policy enforcement: [ ] OPA (Open Policy Agent) [ ] Kyverno [ ] None
```

#### Network Architecture
```yaml
Network Segmentation:
  [ ] Flat network (all systems same subnet) - HIGH RISK
  [ ] VLAN segmentation (by function: prod, staging, dev, DMZ)
  [ ] Zero Trust Network Access (ZTNA)
  [ ] Software-Defined Networking (SDN)

Firewall & Security:
  - Perimeter firewall: [ ] Palo Alto [ ] Fortinet [ ] Cisco [ ] pfSense [ ] Cloud-native (AWS SG/NACLs)
  - Internal segmentation firewall (ISFW): [ ] Yes [ ] No
  - WAF (Web Application Firewall): [ ] Cloudflare [ ] AWS WAF [ ] Azure Front Door [ ] F5 [ ] Imperva
  - IDS/IPS: [ ] Suricata [ ] Snort [ ] Zeek [ ] Commercial [ ] None

VPN & Remote Access:
  - VPN: [ ] IPsec [ ] WireGuard [ ] OpenVPN [ ] Cisco AnyConnect [ ] Tailscale
  - Remote desktop: [ ] RDP [ ] SSH [ ] VNC [ ] TeamViewer [ ] None
  - MFA (Multi-Factor Authentication): [ ] Yes (all users) [ ] Yes (admins only) [ ] No

Load Balancers:
  [ ] F5 BIG-IP
  [ ] HAProxy
  [ ] NGINX
  [ ] AWS ELB/ALB
  [ ] Azure Load Balancer
  [ ] Google Cloud Load Balancing
  [ ] Traefik (Kubernetes ingress)
```

#### Security Posture
```yaml
Endpoint Security:
  - Antivirus/EDR: [ ] CrowdStrike [ ] SentinelOne [ ] Microsoft Defender [ ] Carbon Black [ ] None
  - Patch management: [ ] WSUS [ ] SCCM [ ] Ansible [ ] SaltStack [ ] Manual
  - Mobile Device Management (MDM): [ ] Intune [ ] Jamf [ ] MobileIron [ ] None

Identity & Access Management (IAM):
  - Directory: [ ] Active Directory [ ] Azure AD [ ] Okta [ ] Auth0 [ ] Google Workspace
  - SSO (Single Sign-On): [ ] Okta [ ] Azure AD [ ] OneLogin [ ] Auth0 [ ] None
  - MFA: [ ] Microsoft Authenticator [ ] Google Authenticator [ ] Duo [ ] YubiKey [ ] None
  - Privileged Access Management (PAM): [ ] CyberArk [ ] BeyondTrust [ ] Teleport [ ] HashiCorp Vault [ ] None

Security Operations Center (SOC):
  [ ] In-house SOC (24/7)
  [ ] Managed SOC (outsourced)
  [ ] Business hours only
  [ ] None

  SIEM (Security Information & Event Management):
    [ ] Splunk
    [ ] Elastic Stack (ELK)
    [ ] Microsoft Sentinel
    [ ] Sumo Logic
    [ ] Chronicle (Google)
    [ ] QRadar (IBM)
    [ ] None

  SOAR (Security Orchestration & Automated Response):
    [ ] Palo Alto Cortex XSOAR
    [ ] Splunk Phantom
    [ ] IBM Resilient
    [ ] TheHive + Cortex
    [ ] Custom (StackStorm, n8n)
    [ ] None

Vulnerability Management:
  - Scanning: [ ] Nessus [ ] Qualys [ ] Rapid7 [ ] OpenVAS [ ] None
  - Frequency: [ ] Continuous [ ] Weekly [ ] Monthly [ ] Quarterly [ ] Ad-hoc
  - Penetration testing: [ ] Annual [ ] Biannual [ ] Ad-hoc [ ] Never

Backup & Disaster Recovery:
  - Backup solution: [ ] Veeam [ ] Commvault [ ] Acronis [ ] AWS Backup [ ] Azure Backup [ ] Restic [ ] Custom
  - Backup frequency: [ ] Continuous [ ] Hourly [ ] Daily [ ] Weekly
  - Offsite backup: [ ] Yes (cloud) [ ] Yes (tape, offsite vault) [ ] No
  - RTO (Recovery Time Objective): _____ hours
  - RPO (Recovery Point Objective): _____ hours
  - DR drill frequency: [ ] Quarterly [ ] Annual [ ] Never
```

#### Compliance Requirements
```yaml
Regulatory Compliance:
  [ ] SOC 2 Type II (Trust Service Criteria)
      - Audit frequency: Annual
      - Auditor: _______
      - Last report date: _______

  [ ] ISO 27001 (Information Security Management)
      - Certification date: _______
      - Certification body: _______
      - Next audit: _______

  [ ] PCI-DSS (Payment Card Industry Data Security Standard)
      - Level: [ ] 1 [ ] 2 [ ] 3 [ ] 4
      - QSA (Qualified Security Assessor): _______
      - AOC (Attestation of Compliance) date: _______

  [ ] HIPAA (Health Insurance Portability & Accountability Act)
      - BAA (Business Associate Agreement) required: [ ] Yes [ ] No
      - PHI (Protected Health Information) processed: [ ] Yes [ ] No

  [ ] GDPR (General Data Protection Regulation - EU)
      - Personal data of EU residents: [ ] Yes [ ] No
      - Data Protection Officer: _______

  [ ] CCPA (California Consumer Privacy Act)
      - California residents' data: [ ] Yes [ ] No

  [ ] FedRAMP (Federal Risk & Authorization Management Program)
      - Impact level: [ ] Low [ ] Moderate [ ] High
      - Authorization date: _______

  [ ] CMMC (Cybersecurity Maturity Model Certification - DoD)
      - Level: [ ] 1 [ ] 2 [ ] 3
      - Certification date: _______

Industry-Specific:
  [ ] FINRA (Financial Industry Regulatory Authority)
  [ ] GLBA (Gramm-Leach-Bliley Act - Financial)
  [ ] FERPA (Family Educational Rights & Privacy Act - Education)
  [ ] ITAR (International Traffic in Arms Regulations - Defense)
  [ ] State data breach notification laws (all 50 U.S. states)
```

---

## Phase 2: Site Assessment

### Pre-Deployment Checklist

#### Week 1: Remote Discovery & Documentation Review
```yaml
Documentation:
  [ ] Network topology diagram (logical, physical)
  [ ] System architecture diagram (applications, databases, integrations)
  [ ] Cloud architecture diagram (AWS/Azure/GCP)
  [ ] Kubernetes cluster architecture (if applicable)
  [ ] Data flow diagrams (for sensitive data: PII, PCI, PHI)
  [ ] Incident response plan
  [ ] Disaster recovery plan
  [ ] Change management process

Access Provisioning:
  [ ] VPN credentials (if remote assessment)
  [ ] Cloud console access (read-only):
      - AWS: IAM user with SecurityAudit policy
      - Azure: Reader role on subscriptions
      - GCP: Viewer role on projects
  [ ] Kubernetes cluster access (kubectl, read-only)
  [ ] SIEM access (for log review)
  [ ] Asset inventory system (CMDB)

Automated Discovery (if permitted):
  [ ] Nmap scan (authorized, documented)
  [ ] Cloud asset inventory:
      - AWS: aws ec2 describe-instances (all regions)
      - Azure: az vm list
      - GCP: gcloud compute instances list
  [ ] Kubernetes: kubectl get all --all-namespaces
  [ ] Container registry audit: List all images, check for vulnerabilities
```

#### Week 2: Technical Deep Dive (Virtual or On-Site)
```yaml
Infrastructure Review:
  [ ] Data center tour (if on-prem):
      - Server racks (physical layout)
      - Network closets (core switches, patch panels)
      - Storage arrays (SAN, NAS)
      - Environmental (HVAC, fire suppression, UPS)

  [ ] Cloud environment review (screen share):
      - VPC/VNet topology
      - Security groups / Network Security Groups (NSGs)
      - IAM roles and policies
      - S3/Blob Storage bucket permissions
      - CloudTrail/Activity Log configuration

  [ ] Kubernetes cluster inspection:
      - Node configuration (worker nodes, control plane)
      - Network policies (Calico, Cilium, etc.)
      - RBAC (Role-Based Access Control) audit
      - Admission controllers (OPA, Kyverno)
      - Secrets management (HashiCorp Vault, AWS Secrets Manager, Kubernetes Secrets)

Application Architecture:
  [ ] Monolith vs. microservices
  [ ] Service-to-service communication (REST, gRPC, message queues)
  [ ] API gateway (Kong, Apigee, AWS API Gateway)
  [ ] Authentication/Authorization (OAuth 2.0, JWT, SAML)
  [ ] Logging & monitoring (Prometheus, Grafana, ELK, Datadog, New Relic)

Interviews:
  [ ] CTO/CIO (business priorities, risk tolerance)
  [ ] CISO/Security Lead (compliance, threat landscape)
  [ ] DevOps Lead (CI/CD, deployment frequency, tooling)
  [ ] SRE/Operations (on-call, incident management)
  [ ] Compliance Officer (audit requirements, evidence collection)
```

---

## Phase 3: Deployment Architecture

### General IT Monitoring Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         INTERNET / PUBLIC                         │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  Edge Firewall    │
                   │  + WAF            │
                   └─────────┬─────────┘
                             │
┌─────────────────────────────┴──────────────────────────────────────┐
│                          DMZ (Perimeter)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Reverse     │  │  Jump Host   │  │  Insa Sensor │◄── SPAN    │
│  │  Proxy       │  │  (Bastion)   │  │  (DMZ)       │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────┬─────────────────────────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │  Internal Firewall  │ ◄── Segmentation
                   └──────────┬──────────┘
                              │
┌──────────────────────────────┴──────────────────────────────────────┐
│                     INTERNAL CORPORATE NETWORK                       │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Application │  │  Database    │  │  Active      │             │
│  │  Servers     │  │  Servers     │  │  Directory   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           │                                         │
│                 ┌─────────▼─────────┐                               │
│                 │  Core Switch      │ ◄── MONITORING POINT         │
│                 │  (SPAN Port)      │     Insa Sensor: 10.1.1.250  │
│                 └─────────┬─────────┘                               │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┬─────────────────────┐
            │               │               │                     │
┌───────────▼────┐  ┌───────▼─────┐  ┌──────▼─────┐  ┌──────────▼──────┐
│ Production     │  │ Staging     │  │ Development│  │ Management      │
│ VLAN 100       │  │ VLAN 200    │  │ VLAN 300   │  │ VLAN 10         │
│ 10.100.0.0/16  │  │ 10.200.0.0/16│ │10.300.0.0/16│ │ 10.1.0.0/16     │
└───────────┬────┘  └───────┬─────┘  └──────┬─────┘  └──────────┬──────┘
            │               │               │                     │
            └───────────────┴───────────────┴─────────────────────┘
                                    │
┌────────────────────────────────────┴────────────────────────────────┐
│                      CLOUD INFRASTRUCTURE                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  AWS / AZURE / GCP                                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │ EC2/VMs  │  │ RDS/SQL  │  │ S3/Blob  │  │ Lambda/  │  │    │
│  │  │          │  │ Databases│  │ Storage  │  │ Functions│  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │    │
│  │                                                             │    │
│  │  Cloud Monitoring:                                         │    │
│  │  - CloudTrail / Activity Log (API audit)                   │    │
│  │  - VPC Flow Logs (network traffic)                         │    │
│  │  - GuardDuty / Security Center (threat detection)          │    │
│  │  - Insa Cloud Connector ◄── Ingests logs, anomaly detection│    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTERS                               │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  EKS / AKS / GKE                                           │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │     │
│  │  │ Control  │  │ Worker   │  │ Worker   │  │ Worker   │ │     │
│  │  │ Plane    │  │ Node 1   │  │ Node 2   │  │ Node 3   │ │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │     │
│  │                                                            │     │
│  │  Insa Kubernetes Agent (DaemonSet):                       │     │
│  │  - Monitors K8s API server audit logs                     │     │
│  │  - Network policies enforcement                           │     │
│  │  - Runtime security (Falco integration)                   │     │
│  │  - Image vulnerability scanning (admission controller)    │     │
│  └───────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘

LEGEND:
═══════  Critical production traffic
───────  Standard monitoring
◄── SPAN Network tap/mirror port
☁️      Cloud-native monitoring (API-based)
🐳      Container/Kubernetes monitoring (agent-based)
```

---

## Phase 4: Installation Procedure

### Deployment Model Selection

```yaml
Model A: On-Premises Network Sensor (Traditional)
  Use Case: Data center, corporate office
  Deployment:
    - Physical/virtual appliance in network rack
    - SPAN port on core switch
    - Monitors: East-west traffic (server-to-server), north-south (internet-facing)
  Pros: Full network visibility, no agent required
  Cons: Blind to encrypted traffic (TLS), limited cloud visibility

Model B: Cloud-Native Monitoring (API-Based)
  Use Case: AWS/Azure/GCP workloads, serverless applications
  Deployment:
    - Insa Cloud Connector (lightweight VM or Lambda function)
    - Ingests: CloudTrail, VPC Flow Logs, GuardDuty findings
    - API queries: EC2 metadata, S3 bucket policies, IAM roles
  Pros: Cloud-specific visibility (API calls, IAM), scalable
  Cons: Dependent on cloud provider logs (may be delayed, incomplete)

Model C: Kubernetes Agent (Container-Based)
  Use Case: Kubernetes clusters (EKS, AKS, GKE, on-prem)
  Deployment:
    - DaemonSet (runs on every node)
    - Monitors: K8s API audit logs, pod-to-pod traffic, container runtime
    - Integration: Falco (runtime security), OPA (policy enforcement)
  Pros: Container-aware (namespaces, labels), runtime protection
  Cons: Requires cluster admin access, resource overhead (CPU, memory)

Model D: Hybrid (Combination of A, B, C)
  Use Case: Hybrid cloud, multi-cloud, containers + VMs
  Deployment:
    - On-prem sensor (data center)
    - Cloud connector (AWS, Azure)
    - K8s agent (EKS, AKS clusters)
    - Central management: Insa dashboard aggregates all sources
  Pros: Complete visibility across hybrid environment
  Cons: Complex deployment, multiple components to manage
```

### Installation: On-Premises Network Sensor

#### Pre-Installation (1 week)
```yaml
Approvals:
  [ ] Change control ticket approved
  [ ] Network team coordination (SPAN port configuration)
  [ ] Security team approval (firewall rules)
  [ ] Management sign-off

Equipment:
  [ ] Insa sensor appliance (physical or VM)
      - If VM: vCPU: 4, RAM: 16GB, Disk: 500GB SSD
      - Hypervisor compatibility: VMware ESXi, Hyper-V, KVM
  [ ] Network cables (if physical)
  [ ] Rack space (if physical)
  [ ] IP address allocation (management network)
```

#### Installation Day

```yaml
Hour 0-1: Physical/Virtual Deployment
  Physical Appliance:
    [ ] Mount in rack (1U or 2U)
    [ ] Connect to UPS
    [ ] Connect management port to corporate network
    [ ] Connect monitoring port to SPAN port (RX only, no TX)

  Virtual Appliance:
    [ ] Upload OVA/VHD to hypervisor
    [ ] Allocate resources (4 vCPU, 16GB RAM, 500GB disk)
    [ ] Create virtual network adapter for monitoring (promiscuous mode)
    [ ] Power on VM

Hour 1-2: Network Configuration
  SPAN Port Configuration:
    Example (Cisco):
      monitor session 1 source vlan 100,200 rx
      monitor session 1 destination interface Gi1/0/24
      ! Gi1/0/24 = Insa sensor monitoring port

    [ ] Verify traffic capture: tcpdump -i eth1 -n

  Management Network:
    [ ] Static IP: 10.1.1.250
    [ ] Subnet: 255.255.255.0
    [ ] Gateway: 10.1.1.1
    [ ] DNS: (corporate DNS)
    [ ] NTP: (corporate NTP)

Hour 2-3: Sensor Configuration
  Initial Setup:
    [ ] Web UI: https://10.1.1.250
    [ ] Set admin password (strong, 16+ chars)
    [ ] Enable SSH (key-based auth, disable password)
    [ ] Configure timezone
    [ ] Enable syslog forwarding to SIEM (if applicable)

  Traffic Analysis:
    [ ] Enable protocol parsers:
        - HTTP/HTTPS (detect web traffic anomalies)
        - DNS (detect C2, data exfiltration)
        - SSH/RDP (detect brute force, lateral movement)
        - SQL (detect SQL injection, database access)
        - SMB (detect ransomware lateral movement)

  Machine Learning Baseline:
    [ ] Enable 7-14 day learning mode
    [ ] Baseline normal traffic patterns
    [ ] Identify top talkers (servers, endpoints)
    [ ] Build user/entity behavior analytics (UEBA) models

Hour 3-4: Integration & Testing
  Alert Configuration:
    Critical Alerts:
      - Ransomware indicators (SMB enumeration, large file writes)
      - Lateral movement (RDP/SSH from workstation to server)
      - Data exfiltration (large outbound transfers to unknown IPs)
      - Credential dumping (LSASS access, Mimikatz signatures)

  SIEM Integration:
    [ ] Syslog forwarding to Splunk/ELK (CEF or JSON format)
    [ ] API integration (if Insa provides REST API)
    [ ] Test log ingestion, verify parsing rules

  Ticketing Integration:
    [ ] ServiceNow / Jira integration
    [ ] Auto-create incident tickets for HIGH/CRITICAL alerts
    [ ] Include: Alert details, affected assets, recommended actions

  Functional Testing:
    [ ] Generate test alert (safe method: curl to known-bad domain)
    [ ] Verify email delivery
    [ ] Verify SIEM log ingestion
    [ ] Verify ticket creation
    [ ] No production impact observed
```

### Installation: Cloud Monitoring (AWS Example)

```yaml
AWS Deployment (via CloudFormation / Terraform):
  Components:
    [ ] Insa Cloud Connector (Lambda function or EC2 instance)
    [ ] IAM role with read-only permissions:
        - CloudTrail: Describe*, Get*, List*
        - VPC: DescribeFlowLogs, DescribeVpcs
        - EC2: DescribeInstances, DescribeSecurityGroups
        - GuardDuty: GetFindings, ListFindings
        - S3: GetBucketPolicy (for public bucket detection)

  Installation:
    [ ] Deploy CloudFormation template (provided by Insa)
    [ ] Configure CloudTrail log ingestion (S3 bucket notifications)
    [ ] Enable VPC Flow Logs (if not already enabled)
    [ ] Configure GuardDuty findings forwarding (EventBridge rule)

  Configuration:
    [ ] Set alert thresholds:
        - IAM: Root account usage (CRITICAL)
        - EC2: Security group changes (HIGH)
        - S3: Public bucket detected (HIGH)
        - GuardDuty: Any HIGH/CRITICAL finding (escalate)

    [ ] Integration with Slack/PagerDuty (for real-time alerts)

  Testing:
    [ ] Simulate alert: aws s3api put-bucket-acl --acl public-read (safe test bucket)
    [ ] Verify Insa detects public S3 bucket within 5 minutes
    [ ] Verify alert notification received
```

### Installation: Kubernetes Monitoring

```yaml
Kubernetes Deployment (via Helm Chart):
  Prerequisites:
    [ ] Kubectl access to cluster (cluster-admin role)
    [ ] Helm 3.x installed
    [ ] Cluster requirements: K8s 1.20+, 2 vCPU per node (DaemonSet overhead)

  Installation:
    helm repo add insa https://charts.insa.com
    helm install insa-agent insa/kubernetes-agent \
      --namespace insa-system \
      --create-namespace \
      --set apiKey=<INSA_API_KEY> \
      --set cluster.name=production-eks \
      --set falco.enabled=true

  Configuration:
    [ ] Enable Falco runtime security rules:
        - Detect: Shell spawned in container (potential compromise)
        - Detect: Sensitive file access (/etc/shadow, /root/.ssh)
        - Detect: Outbound connection to known-bad IP

    [ ] Enable OPA policy enforcement:
        - Deny: Pods without resource limits
        - Deny: Privileged containers (unless whitelisted)
        - Deny: Containers running as root

    [ ] Kubernetes API audit log forwarding:
        - Capture: kubectl exec, kubectl cp (potential data exfiltration)
        - Capture: kubectl delete (accidental or malicious deletions)

  Testing:
    [ ] Deploy test pod: kubectl run test-pod --image=nginx
    [ ] Simulate alert: kubectl exec -it test-pod -- /bin/sh (shell spawn)
    [ ] Verify Insa Falco integration detects shell spawn
    [ ] Verify alert notification received
```

---

## Phase 5: Sector-Specific Monitoring Templates

### General IT Detection Rules

#### Rule Set 1: Ransomware Detection
```yaml
Name: Ransomware Lateral Movement
Severity: CRITICAL
Trigger:
  - SMB: Workstation-to-workstation SMB traffic (anomalous, should be workstation-to-server)
  - Or: Rapid file creation (.encrypted, .locked extensions)
  - Or: Volume Shadow Copy deletion (vssadmin delete shadows /all)
Action:
  - Isolate affected workstation (EDR integration)
  - Alert SOC (immediate escalation)
  - Preserve forensic image (do NOT reboot)
  - Engage incident response team

Context:
  - Ransomware: WannaCry, Ryuk, LockBit
  - Kill chain: Initial access -> lateral movement -> encryption
  - Early detection: Stop at lateral movement (before encryption)
```

#### Rule Set 2: Cloud Misconfiguration
```yaml
Name: Public S3 Bucket Detected (AWS)
Severity: HIGH
Trigger:
  - S3 bucket ACL changed to "public-read" or "public-read-write"
  - Or: Bucket policy allows "Principal": "*"
Action:
  - Alert security team
  - Automatic remediation (if enabled): Remove public access
  - Audit: What data is in bucket? Sensitive?
  - Compliance: Report to CISO (SOC 2, GDPR breach risk)

Context:
  - Capital One breach (2019): Misconfigured S3 bucket, 100M+ records exposed
  - Common mistake: Developer testing, forgot to revert
  - Prevention: AWS S3 Block Public Access (enabled by default)
```

#### Rule Set 3: Insider Threat
```yaml
Name: Abnormal Data Download
Severity: HIGH
Trigger:
  - User downloads >10GB data from database/file server in 1 hour
  - User: NOT in data analyst role (should not need bulk downloads)
  - Time: Outside business hours (11 PM)
Action:
  - Alert HR + Security
  - Review: User's recent activity (termination notice? access to competitors?)
  - Immediate: Suspend user account, revoke access
  - Investigation: UEBA analysis (30-day behavior comparison)

Context:
  - Insider threat: Disgruntled employee, competitor espionage
  - Indicators: Mass downloads, USB drive usage, printing confidential docs
  - Prevention: DLP (Data Loss Prevention), least privilege access
```

#### Rule Set 4: Container Escape
```yaml
Name: Privileged Container Runtime Activity
Severity: CRITICAL (Kubernetes)
Trigger:
  - Falco alert: "Sensitive file opened for reading by non-trusted program"
  - Container: Privileged flag = true (should be rare)
  - Process: Access to /proc, /sys, /dev (host filesystem)
Action:
  - Terminate pod immediately (kubectl delete pod)
  - Alert DevOps + Security
  - Forensics: Analyze container image (scan for malware, backdoors)
  - Review: Why was privileged flag set? (developer mistake?)

Context:
  - Container escape: Attacker breaks out of container, gains host access
  - Privileged containers: Bypass namespace isolation (dangerous)
  - Prevention: OPA policy: Deny privileged unless whitelisted (e.g., CNI pods)
```

#### Rule Set 5: Supply Chain Attack
```yaml
Name: Malicious NPM Package Detected (CI/CD)
Severity: HIGH
Trigger:
  - CI/CD pipeline: npm install downloads package with known CVE
  - Or: Package communicates to unknown IP during install (C2 beacon)
  - Or: Package modifies .git/config (credential theft)
Action:
  - Block build pipeline
  - Alert DevOps
  - Review: package.json changes (who added this dependency?)
  - Alternative: Use vetted package from internal registry (Artifactory)

Context:
  - SolarWinds (2020): Malicious code in build pipeline
  - NPM: event-stream package (2018): Bitcoin wallet theft
  - Prevention: Software Bill of Materials (SBOM), dependency scanning
```

### General IT KPIs

```yaml
Infrastructure Metrics:
  - Server uptime: 99.9%+
  - Cloud service availability: 99.95%+ (SLA)
  - Kubernetes cluster health: All nodes ready, no CrashLoopBackOff pods
  - Backup success rate: 100%

Security Metrics:
  - Mean Time to Detect (MTTD): <15 minutes
  - Mean Time to Respond (MTTR): <1 hour
  - Vulnerability patching: 95%+ within 30 days (CVE publication to patch deployment)
  - False positive rate: <5% (alert accuracy)

Compliance Metrics:
  - SOC 2: 100% controls implemented, 0 exceptions
  - PCI-DSS: Quarterly ASV scans, 0 HIGH/CRITICAL findings
  - ISO 27001: Annual audit, 0 non-conformities
  - GDPR: Data breach notification <72 hours (if applicable)

DevOps Metrics:
  - Deployment frequency: (baseline, then improve)
  - Lead time for changes: (baseline, then improve)
  - Change failure rate: <5%
  - MTTR (Mean Time to Restore service): <1 hour
```

---

## Phase 6: Compliance Requirements

### SOC 2 Type II

```yaml
Trust Service Criteria:
  CC6.1: Logical & Physical Access Controls
    - Insa provides: Network access monitoring, unauthorized access detection
    - Evidence: Audit logs (who accessed what, when), alerts for violations

  CC6.6: Unauthorized Software Detection
    - Insa provides: Software inventory, detect rogue applications
    - Evidence: Asset discovery reports, alerts for unapproved software

  CC7.2: System Monitoring
    - Insa provides: 24/7 network and system monitoring
    - Evidence: Alert logs, incident response records, uptime metrics

Auditor Requests (Annual):
  [ ] Provide 12 months of security alerts (HIGH/CRITICAL only)
  [ ] Demonstrate incident response (example: How was alert X handled?)
  [ ] System availability reports (99.9%+ uptime)
  [ ] Evidence of continuous monitoring (not just quarterly scans)
```

### ISO 27001

```yaml
Annex A Controls:
  A.12.4.1: Event Logging
    - Insa provides: Centralized logging (network, systems, applications)
    - Evidence: 90-day log retention, tamper-proof storage

  A.12.4.3: Administrator & Operator Logs
    - Insa provides: Privileged access monitoring (root, admin accounts)
    - Evidence: Audit trail of all admin actions

  A.16.1.4: Assessment of Security Events
    - Insa provides: Automated threat detection, SIEM correlation
    - Evidence: Threat intelligence integration, IOC matching

Annual Audit:
  [ ] Present: Information Security Management System (ISMS) documentation
  [ ] Demonstrate: Risk assessment process (how Insa reduces risk)
  [ ] Evidence: Corrective actions from previous audit (closure proof)
```

### PCI-DSS

```yaml
Requirement 10: Track & Monitor Network Access
  10.2: Audit trail for all cardholder data access
    - Insa provides: Network traffic analysis, detect access to CDE (Cardholder Data Environment)
    - Evidence: Logs showing who accessed payment systems, when

  10.6: Review logs daily
    - Insa provides: Automated log review, anomaly detection
    - Evidence: Daily alert summaries (manual review not required for all logs)

Requirement 11: Test Security Systems Regularly
  11.4: Intrusion detection/prevention
    - Insa provides: Network IDS (signature + anomaly-based)
    - Evidence: Weekly reports showing IDS alerts, tuning activities

QSA (Qualified Security Assessor) Audit:
  [ ] Demonstrate: CDE network segmentation (VLAN isolation)
  [ ] Demonstrate: Insa sensor monitors CDE boundary (in/out traffic)
  [ ] Evidence: Penetration test results (annual)
```

### HIPAA

```yaml
Security Rule:
  164.312(b): Audit Controls
    - Insa provides: Audit logs for ePHI (electronic Protected Health Information) access
    - Evidence: Who accessed patient records (via network traffic analysis)

  164.312(d): Integrity Controls
    - Insa provides: Detect unauthorized changes to ePHI (database writes)
    - Evidence: Alerts for database modifications from unauthorized sources

  164.308(a)(1)(ii)(D): Information System Activity Review
    - Insa provides: Daily security reports, anomaly alerts
    - Evidence: Weekly review meetings (documented)

HIPAA Breach Notification:
  If ePHI breach detected:
    [ ] Notify affected individuals: <60 days
    [ ] Notify HHS (Dept. of Health & Human Services): <60 days
    [ ] Notify media (if >500 individuals affected): Immediately
    [ ] Insa support: Forensic evidence (timeline, affected records count)
```

### GDPR

```yaml
Article 32: Security of Processing
  - Insa provides: Pseudonymization, encryption, integrity, availability monitoring
  - Evidence: Encryption at rest/transit, backup testing

Article 33: Breach Notification
  - Requirement: Notify supervisory authority <72 hours
  - Insa support: Rapid breach detection, forensic timeline
  - Evidence: Incident report (what, when, how many records, impact)

Article 35: Data Protection Impact Assessment (DPIA)
  - If processing high-risk personal data (e.g., health, biometric)
  - Insa contribution: Document security controls (network monitoring, encryption)
```

---

## Phase 7: Success Criteria

### 30-Day Milestones

```yaml
Week 1 (Baseline & Discovery):
  [ ] 95%+ of assets discovered (servers, VMs, containers, cloud resources)
  [ ] Network traffic baseline established (top talkers, protocols)
  [ ] User behavior baseline (UEBA): Normal login times, locations, access patterns
  [ ] Zero production impact from monitoring

Week 2 (Tuning & Integration):
  [ ] Alert rules customized (reduce false positives <5%)
  [ ] SIEM integration verified (logs flowing, parsing correctly)
  [ ] Ticketing integration verified (auto-create incidents)
  [ ] SOC team training completed (dashboard, alert triage)

Week 3 (Active Monitoring):
  [ ] Transition to enforcement mode (alerts enabled)
  [ ] First security finding detected and resolved (e.g., misconfigured S3 bucket)
  [ ] Incident response drill (tabletop exercise with IR team)
  [ ] No false positives reaching Tier 3 escalation

Week 4 (Optimization & Reporting):
  [ ] Monthly security report generated (executive summary + technical details)
  [ ] Compliance evidence package (SOC 2, ISO 27001, PCI-DSS)
  [ ] Quarterly business review scheduled (CISO, IT leadership)
  [ ] Continuous improvement plan (next 3 priorities documented)
```

### Long-Term Success Indicators

```yaml
Security Posture:
  - Ransomware: Zero successful encryptions (detection before impact)
  - Data breaches: Zero (early detection, containment before exfiltration)
  - Cloud misconfigurations: Detected <1 hour (auto-remediated if enabled)
  - Insider threats: 100% detection (abnormal behavior flagged)

Operational Efficiency:
  - MTTD: Reduced by 80% (from hours/days to <15 minutes)
  - MTTR: Reduced by 60% (from hours to <1 hour)
  - SOC analyst time: 70% reduction (automated triage, false positive filtering)
  - Incident response cost: $0 (prevention vs. $500K+ average breach cost)

Compliance Excellence:
  - SOC 2 audit: ZERO exceptions/findings (clean report)
  - PCI-DSS: Quarterly scans with 0 HIGH/CRITICAL findings
  - ISO 27001: Surveillance audit passed with 0 non-conformities
  - GDPR: Zero data breach notifications (proactive protection)

Business Value:
  - Cyber insurance premium: Reduced by 20-40%
  - Audit preparation time: Reduced by 60% (automated evidence)
  - Customer trust: Security questionnaire responses faster (evidence readily available)
  - Revenue protection: Avoided downtime, breach costs, regulatory fines
```

---

## Appendix A: Integration Examples

### SIEM Integration (Splunk Example)

```yaml
Syslog Forwarding (CEF Format):
  Insa Sensor Configuration:
    - Syslog server: splunk.company.com:514
    - Protocol: TCP (reliable delivery)
    - Format: CEF (Common Event Format)

  Splunk Configuration:
    - Data input: TCP 514 (listening)
    - Source type: cef
    - Index: insa_security

  Example CEF Log:
    CEF:0|Insa|SecureOps|1.0|100|Ransomware Detected|10|
    src=10.100.50.25 dst=10.100.50.30 spt=445 dpt=445
    msg=SMB enumeration from workstation (potential ransomware)

Splunk Search (Alert Correlation):
  index=insa_security severity>=8
  | stats count by src_ip, alert_name
  | where count > 5
  | alert "Multiple HIGH alerts from same host - investigate"
```

### Ticketing Integration (ServiceNow Example)

```yaml
REST API Integration:
  Insa Sensor Configuration:
    - ServiceNow instance: company.service-now.com
    - API endpoint: /api/now/table/incident
    - Authentication: OAuth 2.0 (client_id, client_secret)

  Incident Auto-Creation:
    - Trigger: HIGH or CRITICAL alert
    - Incident fields:
        - short_description: Alert name (e.g., "Public S3 Bucket Detected")
        - description: Full alert details, affected assets, recommendations
        - urgency: HIGH (2) or CRITICAL (1)
        - assigned_to: SOC team queue
        - cmdb_ci: Affected asset (if in CMDB)

  Example API Call:
    POST /api/now/table/incident
    {
      "short_description": "Ransomware Lateral Movement Detected",
      "description": "SMB enumeration from 10.100.50.25 to 10.100.50.30. Possible ransomware. Isolate immediately.",
      "urgency": "1",
      "assigned_to": "SOC Team"
    }
```

---

## Appendix B: Contact & Escalation

```yaml
Insa Automation Corp:
  Sales Engineering: w.aroca@insaing.com
  Technical Support: support@insaing.com
  24/7 SOC (if contracted): soc@insaing.com

Client Escalation Path:
  Tier 1: SOC Analyst (24/7)
    - Response: <15 minutes (for alerts)
    - Actions: Triage, investigate, escalate if needed

  Tier 2: Security Engineer / Incident Responder
    - Response: <30 minutes (for HIGH alerts)
    - Actions: Deep investigation, containment, remediation

  Tier 3: CISO / Security Director
    - Response: <1 hour (for CRITICAL incidents)
    - Actions: Business decisions, executive notification, PR coordination

  Tier 4: CEO / Board (if catastrophic breach)
    - Response: <2 hours
    - Actions: Legal counsel, regulatory notification, public disclosure

External Coordination:
  FBI Cyber Division: (for nation-state, ransomware >$100K demand)
  CISA: (for critical infrastructure, federal systems)
  Cyber Insurance: (activate IR retainer, legal, forensics)
  Legal Counsel: (data breach notification, regulatory reporting)
  PR Firm: (if public disclosure required)
```

### Incident Severity Matrix

```yaml
CRITICAL (Response: <15 min, Notify: CISO + Executives):
  - Ransomware encryption in progress
  - Active data breach (exfiltration detected)
  - Business-critical system down (e.g., payment processing)
  - Nation-state APT activity

HIGH (Response: <30 min, Notify: Security Team):
  - Attempted ransomware (stopped before encryption)
  - Malware detected (contained)
  - Privilege escalation attempt
  - Cloud misconfiguration (sensitive data exposed)

MEDIUM (Response: <1 hour, Notify: SOC):
  - Failed access attempts (brute force)
  - Vulnerability scan detected (reconnaissance)
  - Policy violation (unapproved software)
  - Certificate expiration warning

LOW (Response: Next business day, Notify: Weekly report):
  - Informational alerts
  - Asset inventory changes
  - Low-severity vulnerability detected
```

---

**Document Control**
Version: 1.0
Author: Insa Automation Corp
Date: October 11, 2025
Classification: Client Confidential
Review Cycle: Annual

**Made by Insa Automation Corp for OpSec**
