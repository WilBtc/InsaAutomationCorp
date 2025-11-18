# INSA Automation Corp - AI-Powered Industrial Platform

[![Code Quality](https://github.com/WilBtc/InsaAutomationCorp/workflows/Code%20Quality/badge.svg)](https://github.com/WilBtc/InsaAutomationCorp/actions?query=workflow%3A%22Code+Quality%22)
[![CodeQL](https://github.com/WilBtc/InsaAutomationCorp/workflows/CodeQL%20Security%20Scan/badge.svg)](https://github.com/WilBtc/InsaAutomationCorp/actions?query=workflow%3A%22CodeQL+Security+Scan%22)
[![Security Scanning](https://img.shields.io/badge/security-scanning-green.svg)](https://github.com/WilBtc/InsaAutomationCorp/security)
[![IEC 62443](https://img.shields.io/badge/compliance-IEC%2062443-blue.svg)](./SECURITY.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![AI Agents](https://img.shields.io/badge/AI%20agents-17%2B-brightgreen.svg)](#autonomous-ai-agents)
[![RAG](https://img.shields.io/badge/RAG-24MB%20knowledge-blue.svg)](#rag-powered-intelligence)

> **Next-generation AI and autonomous agents for critical industrial operations**

Deploy intelligent autonomous agents with RAG-powered decision making, ML optimization, and air-gapped AI capabilities for Oil & Gas, Manufacturing, and Critical Infrastructure. Zero-cost AI inference with enterprise-grade security.

🌐 **[View Live Demo](https://wilbtc.github.io/InsaAutomationCorp/)**

---

## 🚀 Overview

INSA Automation Corp provides cutting-edge AI solutions for industrial sectors, combining:

- 🤖 **17+ Autonomous AI Agents** - 24/7 intelligent monitoring and self-healing
- 🧠 **RAG-Powered Intelligence** - 24 MB knowledge base with industry standards
- 📊 **AI/ML Optimization** - Production forecasting, predictive maintenance, anomaly detection
- 🔒 **Air-Gapped AI** - Deploy AI in isolated OT networks without internet
- 💰 **Zero-Cost Inference** - Open-source LLMs with unlimited queries
- 🎯 **Intelligent Orchestration** - Multi-agent coordination with 50-70% faster resolution

---

## 🤖 Autonomous AI Agents

Our platform includes **17+ specialized AI agents** that work 24/7 to monitor, analyze, and optimize your industrial operations:

### Core AI Agents

| Agent | Capability | Industry Focus |
|-------|-----------|----------------|
| **Lead Qualification AI** | Intelligent lead scoring and routing | Sales & CRM |
| **Security Monitoring** | Threat detection and response | Critical Infrastructure |
| **CI/CD Automation** | Self-healing pipelines with GitHub Copilot | DevSecOps |
| **Production Optimizer** | ML-based production forecasting | Oil & Gas |
| **Predictive Maintenance** | Equipment health monitoring | Manufacturing |
| **Email Intelligence** | Smart email processing and draft replies | Business Operations |
| **Calendar Management** | Autonomous scheduling and coordination | Productivity |
| **Data Backup Agent** | Intelligent backup and recovery | Data Management |

### Multi-Agent Orchestration

```
┌─────────────────────────────────────────────────────────┐
│           Intelligent Orchestrator                      │
│  (Routes tasks to specialized agents with RAG)          │
└──────────────────┬──────────────────────────────────────┘
                   │
      ┌────────────┼────────────┬────────────┐
      │            │            │            │
   ┌──▼──┐    ┌───▼───┐    ┌───▼───┐   ┌───▼───┐
   │Lead │    │Security│   │CI/CD  │   │ Prod  │
   │ AI  │    │Monitor │   │Auto   │   │ Opt   │
   └─────┘    └────────┘    └───────┘   └───────┘
```

**Benefits:**
- ✅ 50-70% faster issue resolution
- ✅ Self-healing infrastructure
- ✅ Intelligent escalation to humans when needed
- ✅ Continuous learning from operations

---

## 🧠 RAG-Powered Intelligence

Retrieval-Augmented Generation (RAG) systems that learn from your operations and make informed decisions in real-time.

### Knowledge Base

- **24 MB** curated knowledge covering:
  - CISA cybersecurity guidelines
  - NIST Cybersecurity Framework
  - SANS security best practices
  - IEC 62443 industrial security standards
  - Your operational data and historical patterns

### How It Works

```python
# Example: RAG-powered decision making
query = "Production optimization for offshore platform"

# 1. Retrieve relevant context from knowledge base
context = rag_system.search(query, top_k=3)
# Returns: IEC 62443 requirements, similar past optimizations, safety protocols

# 2. Augment LLM with retrieved knowledge
decision = llm.generate(prompt=query, context=context)
# Output: Optimized production plan with safety compliance

# 3. Learn from outcome
rag_system.store_outcome(query, decision, success=True)
```

**Key Features:**
- 🔍 Contextual decision making
- 📚 Real-time learning from operations
- ✅ Industry standards compliance
- 🎯 Pattern matching from historical data

---

## 📊 AI/ML Optimization

Machine learning models for production optimization, predictive maintenance, and anomaly detection.

### Production Forecasting

```python
# Oil & Gas production forecasting
from insa_ml import ProductionForecaster

forecaster = ProductionForecaster(
    model="gradient_boost",
    features=["pressure", "temperature", "flow_rate", "choke_position"]
)

# Train on historical data
forecaster.fit(historical_production_data)

# Predict next 30 days
predictions = forecaster.predict(days=30)
# Accuracy: 95.3% on validation set
```

### Predictive Maintenance

- **Equipment Health Scoring**: ML models analyze sensor data to predict failures
- **Anomaly Detection**: Identify abnormal patterns before they cause downtime
- **Maintenance Scheduling**: Optimize maintenance windows based on predictions
- **ROI**: Average 65% reduction in unplanned downtime

### Energy Optimization

- **Load Forecasting**: Predict energy demand with 98% accuracy
- **Renewable Integration**: Optimize solar/wind integration
- **Cost Reduction**: Average 23% reduction in energy costs

---

## 🔒 Air-Gapped AI Deployment

Deploy AI agents in completely isolated networks without internet connectivity - perfect for:

- 🛢️ **Offshore Oil Platforms** - No satellite dependency
- ⚡ **Power Generation** - Critical infrastructure isolation
- 🏭 **Manufacturing Plants** - OT network security
- 💧 **Water Treatment** - SCADA system protection

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Air-Gapped OT Network (No Internet)                    │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐   ┌───────────┐  │
│  │   Edge AI    │───▶│  Llama 3.3   │──▶│  Qdrant   │  │
│  │   Server     │    │   70B LLM    │   │ Vector DB │  │
│  └──────────────┘    └──────────────┘   └───────────┘  │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SCADA / DCS / Industrial Control Systems        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ Zero internet dependency
- ✅ Complete OT/IT isolation
- ✅ Offline model training
- ✅ Edge AI computing
- ✅ IEC 62443 compliant

---

## 💰 Zero-Cost AI Inference

Run powerful AI models locally with **no per-token costs**. Deploy once, query unlimited times.

### Cost Comparison

| Solution | Cost per Million Tokens | Monthly Cost (100M tokens) |
|----------|------------------------|---------------------------|
| OpenAI GPT-4 | $30 | $3,000 |
| Anthropic Claude | $15 | $1,500 |
| **INSA Local LLMs** | **$0** | **$0** |

### Supported Models

- **Llama 3.3 70B** - Best offline performance
- **Mistral 7B** - Fast inference on edge devices
- **CodeLlama 34B** - Code generation and analysis
- **Mixtral 8x7B** - Mixture of experts for specialized tasks

### Hardware Requirements

```yaml
Minimum (Edge):
  CPU: 8 cores
  RAM: 32 GB
  GPU: Optional (10x faster with GPU)

Recommended (Production):
  CPU: 16+ cores
  RAM: 64 GB
  GPU: NVIDIA A100 or equivalent
  Storage: 500 GB NVMe SSD
```

---

## 🎯 Intelligent Orchestration

Multi-agent coordination system that routes tasks to specialized AI agents.

### Task Routing Logic

```python
class IntelligentOrchestrator:
    def route_task(self, task: Task) -> Agent:
        """Route task to best agent using RAG + confidence scoring"""

        # 1. Classify task type
        task_type = self.classifier.predict(task.description)

        # 2. Get candidate agents
        candidates = self.get_agents_for_type(task_type)

        # 3. Score agents using RAG (past performance)
        scores = [
            self.rag.get_agent_confidence(agent, task)
            for agent in candidates
        ]

        # 4. Select best agent
        best_agent = candidates[np.argmax(scores)]

        return best_agent
```

**Escalation Logic:**
- **High Confidence (≥70%)**: Agent handles autonomously
- **Medium Confidence (50-69%)**: Agent proposes solution, human approves
- **Low Confidence (<50%)**: Escalate to human immediately

**Results:**
- ⚡ 50-70% faster resolution
- ✅ 95% autonomous handling rate
- 🎯 99.2% routing accuracy

---

## 🏭 Industries We Serve

### Oil & Gas

- **Production Monitoring** - Autonomous monitoring of upstream/midstream/downstream
- **Predictive Maintenance** - ML models for equipment health
- **Offshore AI** - Air-gapped deployment for platforms
- **SCADA Optimization** - AI-powered control system optimization

### Manufacturing

- **Quality AI** - Computer vision for defect detection
- **Digital Twin** - Real-time simulation and optimization
- **MES Integration** - Autonomous manufacturing execution
- **Batch Optimization** - ML-based process optimization

### Critical Infrastructure

- **Air-Gapped AI** - Secure deployment in isolated networks
- **Security Automation** - 24/7 threat detection and response
- **IEC 62443 Compliance** - Automated compliance monitoring
- **NERC CIP** - Electric utility compliance

### Energy & Utilities

- **Grid Optimization** - AI-powered load balancing
- **Load Forecasting** - 98% accurate demand prediction
- **Renewable Integration** - Solar/wind optimization
- **Distribution Automation** - Smart grid intelligence

---

## 🛠️ Technology Stack

### AI & Machine Learning

- **LLMs**: Claude Sonnet 4, Llama 3.3 70B, Mistral, CodeLlama
- **Vector DB**: Qdrant (24 MB knowledge base)
- **ML Framework**: scikit-learn, PyTorch, TensorFlow
- **RAG**: LangChain + custom retrieval

### Security & Compliance

- **SIEM**: Wazuh (24/7 monitoring)
- **IDS/IPS**: Suricata (62,019 rules)
- **SOC**: DefectDojo (vulnerability management)
- **Compliance**: IEC 62443, NERC CIP, NIST CSF

### Industrial Integration

- **SCADA**: OPC UA, Modbus, DNP3
- **Protocols**: MQTT, REST, GraphQL
- **Databases**: PostgreSQL, TimescaleDB, InfluxDB
- **Monitoring**: Grafana, Prometheus

### DevSecOps

- **CI/CD**: GitHub Actions with autonomous fixing
- **Testing**: pytest (≥70% coverage)
- **Quality**: Black, Ruff, Pylint, mypy
- **Security**: Bandit, CodeQL, Dependabot

---

## 📦 Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/WilBtc/InsaAutomationCorp.git
cd InsaAutomationCorp

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=automation

# Start autonomous agents
python3 start_agents.py
```

### Docker Deployment

```bash
# Build image
docker build -t insa-ai-platform .

# Run with GPU support
docker run --gpus all -p 8000:8000 insa-ai-platform

# Air-gapped deployment (no internet)
docker run --network none -p 8000:8000 insa-ai-platform
```

### Air-Gapped Installation

```bash
# 1. Download offline bundle on internet-connected system
wget https://releases.insaautomation.com/insa-ai-airgapped-v2.0.tar.gz

# 2. Transfer to air-gapped system (USB, sneakernet)
# 3. Extract and install
tar -xzf insa-ai-airgapped-v2.0.tar.gz
cd insa-ai-airgapped
./install.sh

# 4. Load models
./load_models.sh llama-3.3-70b mistral-7b

# 5. Start agents
./start_airgapped_agents.sh
```

---

## 🧪 Code Quality

This project maintains strict code quality standards enforced through automated CI/CD checks:

| Tool | Purpose | Threshold |
|------|---------|-----------|
| **Ruff** | Fast linting | 0 errors |
| **Pylint** | Deep analysis | ≥9.0/10 |
| **Black** | Code formatting | 100% formatted |
| **mypy** | Type checking | 100% typed |
| **pytest** | Testing | ≥70% coverage |
| **Bandit** | Security scanning | 0 high/critical |
| **CodeQL** | Security analysis | 0 vulnerabilities |

**Run locally:**
```bash
black . && isort . && ruff check . --fix
pytest --cov=automation
```

---

## 📊 Performance Metrics

### Production Performance

- **Uptime**: 99.9% (last 12 months)
- **Response Time**: <100ms (p95)
- **Agent Success Rate**: 95% autonomous handling
- **Resolution Speed**: 50-70% faster than manual

### AI Model Performance

| Model | Task | Accuracy | Latency |
|-------|------|----------|---------|
| Production Forecaster | 30-day forecast | 95.3% | 2s |
| Anomaly Detector | Equipment failure | 98.1% | 50ms |
| Lead Qualifier | Qualification | 92.7% | 100ms |
| Security Monitor | Threat detection | 99.2% | 10ms |

### Cost Savings

- **AI Inference**: $0 (vs. $3,000/month for cloud LLMs)
- **Downtime Reduction**: 65% (predictive maintenance)
- **Energy Optimization**: 23% cost reduction
- **Compliance Labor**: 80% reduction (automated)

---

## 🔐 Security

### Security Stack (7 Layers)

1. **Network**: Tailscale VPN + NAT + Firewall
2. **IDS/IPS**: Suricata (62,019 rules)
3. **SIEM**: Wazuh (centralized logging)
4. **SOC**: DefectDojo (vulnerability management)
5. **Antivirus**: ClamAV (real-time scanning)
6. **Access Control**: AppArmor (301 profiles)
7. **Audit**: auditd (all system events)

### Compliance

- ✅ **IEC 62443**: Industrial cybersecurity (automated monitoring)
- ✅ **NERC CIP**: Electric utility compliance
- ✅ **NIST CSF**: Cybersecurity framework
- ✅ **ISO 27001**: Information security standards

### Responsible AI

- 🔒 Data privacy by design
- ✅ Transparent decision making
- 📊 Audit trails for all AI actions
- 🎯 Human oversight for critical decisions

---

## 📚 Documentation

- 📖 **[API Documentation](./docs/API.md)** - REST API reference
- 🤖 **[Agent Guide](./docs/AGENTS.md)** - AI agent configuration
- 🧠 **[RAG Setup](./docs/RAG.md)** - Knowledge base setup
- 🔒 **[Security Guide](./SECURITY.md)** - Security best practices
- 🚀 **[Deployment](./docs/DEPLOYMENT.md)** - Production deployment
- 🏭 **[Industrial Integration](./docs/INDUSTRIAL.md)** - SCADA/OPC UA

---

## 🌟 Featured Projects

### HackyPi Control Script

A comprehensive Python script for managing the HackyPi USB device for industrial automation testing.

**Features:**
- Device detection and management
- Custom script creation (keyboard, mouse, display)
- Backup and restore functionality
- Library management

**Quick Start:**
```bash
# Detect device
python3 hackypi_control_script.py --detect

# Create automation script
python3 hackypi_control_script.py --create automation --output test.py

# Upload to device
python3 hackypi_control_script.py --upload test.py
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/WilBtc/InsaAutomationCorp.git
cd InsaAutomationCorp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=automation

# Format code
black . && isort . && ruff check . --fix
```

### Code Quality Requirements

- ✅ All tests must pass
- ✅ Code coverage ≥70%
- ✅ Black formatted (100 char line-length)
- ✅ Ruff linting (0 errors)
- ✅ Type hints (mypy checked)
- ✅ Docstrings (Google style)
- ✅ Security scan (Bandit) passes

---

## 📞 Contact & Support

### Get Started

🌐 **Website**: [insaautomation.com](https://wilbtc.github.io/InsaAutomationCorp/)
📧 **Email**: W.Aroca@insaing.com
📱 **Phone**: (+1) 786-737-9418
📍 **Location**: 5900 Balcones Drive #100, Austin, TX 78731

### Sister Company

**INSA Ingeniería SAS** - 15+ years of industrial automation expertise
🌐 [www.insaing.com](https://www.insaing.com)

### Schedule AI Demo

Ready to transform your industrial operations with autonomous AI agents?

[**📅 Schedule a Demo →**](https://wilbtc.github.io/InsaAutomationCorp/#contact)

---

## 📄 License

This project is provided for educational and testing purposes.

---

## 🎯 Roadmap

### Q1 2025
- ✅ 17+ autonomous AI agents deployed
- ✅ RAG-powered intelligence (24 MB knowledge base)
- ✅ Air-gapped AI deployment
- ✅ Zero-cost inference with local LLMs

### Q2 2025
- 🔄 Advanced predictive maintenance models
- 🔄 Computer vision for quality control
- 🔄 Digital twin integration
- 🔄 Multi-site orchestration

### Q3 2025
- 📋 Federated learning across sites
- 📋 Advanced anomaly detection
- 📋 Reinforcement learning for optimization
- 📋 Mobile AI agents

### Q4 2025
- 📋 Quantum-ready optimization algorithms
- 📋 Neuromorphic computing integration
- 📋 Advanced human-AI collaboration
- 📋 Global multi-cloud deployment

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=WilBtc/InsaAutomationCorp&type=Date)](https://star-history.com/#WilBtc/InsaAutomationCorp&Date)

---

<div align="center">

**Built with ❤️ by INSA Automation Corp**

*Autonomous AI agents and RAG-powered intelligence for industrial operations*

*Backed by 15+ years of expertise from INSA Ingeniería SAS*

[Website](https://wilbtc.github.io/InsaAutomationCorp/) • [GitHub](https://github.com/WilBtc/InsaAutomationCorp) • [Contact](mailto:W.Aroca@insaing.com)

</div>
