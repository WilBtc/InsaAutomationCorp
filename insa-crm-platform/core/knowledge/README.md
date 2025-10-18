# Industrial Instrumentation RAG System

**Knowledge-Augmented CRM Agents for Industrial Automation**

Date: October 18, 2025
Status: ✅ PRODUCTION READY
Knowledge Base: 794 pages, 2,304 chunks, 11 chapters

---

## 🎯 Overview

This RAG (Retrieval-Augmented Generation) system provides CRM AI agents with access to comprehensive industrial instrumentation knowledge from:

**Reference Book:**
"Instrumentación Industrial, 8va Edición" by Antonio Creus Solé

**Content:**
- 794 pages of industrial automation knowledge
- 50,817 lines of extracted text
- 2,304 indexed chunks across 11 chapters
- Standards: ISA, ISO 9000, ANSI/ASME

---

## 📚 Knowledge Base Content

### Chapter 1: Generalidades (Fundamentals)
- ISA/ISO instrument identification norms
- Measurement uncertainty and accuracy
- Basic instrumentation concepts

### Chapter 2: Transmitters & Communications
- Industrial transmitters
- Communication protocols
- Signal types (4-20mA, digital)

### Chapters 3-7: Measurement Variables
- **Chapter 3:** Pressure measurement
- **Chapter 4:** Pressure transmitters
- **Chapter 5:** Level measurement
- **Chapter 6:** Temperature measurement
- **Chapter 7:** Flow measurement

### Chapter 8: Final Control Elements
- Control valves
- Valve sizing and selection
- Actuators and positioners

### Chapter 9: Automatic Control (CRITICAL)
- PID control strategies
- Advanced control methods
- Control tuning and optimization

### Chapter 10: Calibration
- Calibration procedures
- ISO 9000 compliance
- Error analysis

### Chapter 11: Industrial Applications
- Real-world case studies
- Industry-specific solutions

---

## 🚀 Quick Start

### Basic Usage

```python
from knowledge.instrumentation_rag import instrumentation_rag

# Search for relevant information
results = instrumentation_rag.query("pressure transmitter", top_k=5)

for chunk in results:
    print(f"Chapter {chunk.chapter}, Score: {chunk.relevance_score}")
    print(chunk.content)
```

### Get Context for AI Agents

```python
from knowledge.instrumentation_rag import instrumentation_rag

# Get formatted context for agent prompts
context = instrumentation_rag.get_context_for_agent(
    query="control valve sizing",
    max_tokens=2000
)

# Inject into agent prompt
agent_prompt = f"""
You are an industrial automation expert.

Use this reference knowledge:
{context}

Customer question: How do I size a control valve for steam application?
"""
```

### Helper Functions

```python
from knowledge.instrumentation_rag import (
    get_sensor_recommendation,
    get_control_strategy,
    get_calibration_procedure
)

# Get sensor recommendations
sensors = get_sensor_recommendation("high pressure application")

# Get control strategies
strategy = get_control_strategy("temperature control reactor")

# Get calibration procedures
procedure = get_calibration_procedure("pressure transmitter")
```

---

## 🤖 CRM Agent Use Cases

### 1. Equipment Recommendation Agent
**Query:** "pressure sensor high temperature"
**Output:** Recommends differential pressure transmitters with diaphragm seals

### 2. Quote Generation Agent
**Query:** "PID control loop components"
**Output:** Complete bill of materials with ISA-compliant equipment

### 3. Proposal Writing Agent
**Query:** "ISA standards communication protocols"
**Output:** Technical sections referencing industry standards

### 4. Lead Qualification Agent
**Query:** "viscous fluid flow measurement"
**Output:** Technical complexity assessment (Coriolis, PD meters)

### 5. Customer Support Agent
**Query:** "calibration frequency pressure transmitter"
**Output:** ISO 9000-compliant calibration recommendations

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Total Pages | 794 |
| Text Size | 1.5 MB |
| Total Lines | 50,817 |
| Indexed Chunks | 2,304 |
| Chapters | 11 |
| Language | Spanish |
| Edition | 8th (2012) |
| Standards | ISA, ISO 9000, ANSI/ASME |

---

## 🔧 Technical Architecture

### Current Implementation (v1.0)
- **Search Method:** TF-IDF + keyword matching
- **Storage:** In-memory Python dictionaries
- **Chunking:** 10-line paragraphs per chapter
- **Indexing:** Chapter-based + keyword extraction

### Future Enhancements (v2.0)
- **Vector Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB:** Qdrant (already deployed on port 6333)
- **Semantic Search:** Cosine similarity on embeddings
- **Multi-language:** Spanish-to-English translation layer

---

## 🎓 Example: Complete Agent Integration

```python
from knowledge.instrumentation_rag import instrumentation_rag

def equipment_recommendation_agent(customer_requirements):
    """
    AI agent that recommends equipment using RAG knowledge
    """
    # Extract key requirements
    application = customer_requirements.get("application")
    budget = customer_requirements.get("budget")

    # Query RAG system
    context = instrumentation_rag.get_context_for_agent(
        query=application,
        max_tokens=1500
    )

    # Build agent prompt with RAG context
    prompt = f"""
    You are an industrial automation sales engineer.

    CUSTOMER REQUIREMENTS:
    - Application: {application}
    - Budget: {budget}

    TECHNICAL REFERENCE KNOWLEDGE:
    {context}

    Based on the technical reference above, provide:
    1. Recommended equipment (with part numbers)
    2. Technical justification
    3. Cost estimate
    4. Installation timeline

    Keep recommendations within budget and cite the reference book.
    """

    # Call Claude Code or other LLM with the enriched prompt
    # recommendation = call_llm(prompt)

    return prompt  # Returns enriched prompt for LLM

# Usage
customer_req = {
    "application": "pressure measurement high temperature reactor",
    "budget": "$50,000"
}

enriched_prompt = equipment_recommendation_agent(customer_req)
```

---

## 📁 File Structure

```
knowledge/
├── README.md                           # This file
├── instrumentation_rag.py              # Main RAG module
└── __init__.py                         # Package init

examples/
└── rag_agent_integration.py            # 5 complete examples

Source Data:
├── /home/wil/instrumentacion-industrial-antonio-creus.pdf (26 MB)
└── /home/wil/instrumentacion-industrial-antonio-creus.txt (1.5 MB)
```

---

## 🧪 Running Examples

```bash
# Test RAG system
cd ~/insa-crm-system
python3 knowledge/instrumentation_rag.py

# Run full integration examples
python3 examples/rag_agent_integration.py
```

---

## 🔐 Production Deployment

### Qdrant Vector Database
```bash
# Already deployed on port 6333
curl http://localhost:6333

# Dashboard available at:
http://localhost:6333/dashboard
```

### Future: Vector Embeddings
```bash
# Install dependencies (not yet required)
pip install qdrant-client sentence-transformers

# Load embeddings into Qdrant
python3 scripts/load_embeddings.py
```

---

## 📞 Support

**Project:** INSA CRM System
**Owner:** INSA Automation Corp
**Email:** w.aroca@insaing.com
**Server:** iac1 (100.100.101.1)

---

## 📜 License

Proprietary - INSA Automation Corp © 2025

---

**Status:** ✅ PRODUCTION READY
**Version:** 1.0
**Last Updated:** October 18, 2025

Made with Claude Code for Industrial Automation Engineering
