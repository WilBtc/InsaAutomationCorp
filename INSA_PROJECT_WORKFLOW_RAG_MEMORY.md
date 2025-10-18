# INSA Automation Corp - Project Management Workflow
# RAG Memory for AI Agents
# Updated: October 18, 2025

## 🎯 PURPOSE
This document serves as a **RAG (Retrieval-Augmented Generation) memory** for INSA Automation's AI agents to understand how projects are structured, executed, and managed within the company. All AI agents should reference this workflow when handling project-related tasks.

---

## 📋 EXECUTIVE SUMMARY

**Company**: INSA Automation Corp
**Specialization**: Industrial Automation - Oil & Gas Division
**Project Type**: Instrumentation & Control Systems for Petroleum Processing
**Standards**: ISA-5.1-2024, API RP 12J, API RP 14C, IEC 61131-3

**Core Competencies**:
- P&ID Design (Piping and Instrumentation Diagrams)
- PLC Programming (Allen-Bradley, Siemens)
- HMI/SCADA Development
- Instrumentation & Control Panel Design
- Electrical Engineering (Low Voltage Systems)
- Mechanical Integration (Isometric drawings, layouts)

---

## 🏗️ INSA PROJECT LIFECYCLE (4 PHASES)

### **Phase 1: QUALITY & PLANNING** 📊
**Purpose**: Establish project quality framework and engineering baseline

**Deliverables**:
1. **Quality Plan** (`*-DC01_Plan_de_calidad.pdf`)
   - Quality assurance procedures
   - Document control
   - Review and approval processes
   - Testing and validation protocols

2. **Engineering Dossier** (`*-LT01_Dossier_ingeniería.pdf`)
   - Complete document index
   - Project scope and requirements
   - Technical specifications
   - Compliance matrix

**Folder Structure**:
```
1. QUALITY/
├── 1.1. DOCUMENT/
│   └── [Project Code]-INS-DC01_Plan_de_calidad.pdf
└── 1.2. LIST OF DOCUMENTS/
    └── [Project Code]-GRL-LT01_Dossier_ingeniería.pdf
```

**Key AI Agent Actions**:
- Verify all documents follow naming convention: `[PROJECT_CODE]-[DISCIPLINE]-[DOC_TYPE][NUMBER]_[Description].pdf`
- Ensure quality plan is approved before engineering starts
- Track document revisions and approvals

---

### **Phase 2: INSTRUMENTATION & CONTROL DESIGN** 🎛️
**Purpose**: Complete instrumentation and control system engineering

**Sub-phases**:

#### 2.1 DOCUMENTS (Technical Specifications)
**Deliverables** (15+ documents):
1. **Control Philosophy** (`*-DC02_Control_Philosophy.pdf`)
   - Control strategies
   - Interlock logic
   - Shutdown sequences
   - Operating modes

2. **PLC Specification** (`*-DC03_Requisición_del_PLC.pdf`)
   - PLC model and manufacturer
   - I/O count and types
   - Communication protocols
   - Redundancy requirements

3. **Panel Specifications** (`*-DC04_*, *-DC05_*, *-DC06_*`)
   - Control panel (PLC panel)
   - Low voltage distribution
   - Junction boxes

4. **Instrument Datasheets** (`*-DC07_* through *-DC15_*`)
   - Level sensors (switches, transmitters)
   - Pressure instruments (transmitters, switches, gauges)
   - Temperature sensors (RTDs, thermocouples, glass thermometers)
   - Flow meters (differential pressure, vortex, turbine)

**Folder Structure**:
```
2.1. DOCUMENT/
├── [Project]-INS-DC02_Control_Philosophy.pdf
├── [Project]-INS-DC03_Requisición_del_PLC.pdf
├── [Project]-INS-DC04_Procedimiento_de_Especificaciones_Tablero.pdf
├── [Project]-INS-DC05_PLC_control_panel.pdf
├── [Project]-INS-DC06_Datasheet_TBT_Distribution.pdf
├── [Project]-INS-DC07_Level_Switch.pdf
├── [Project]-INS-DC08_Pressure_Switches.pdf
├── [Project]-INS-DC09_Pressure_Instruments.pdf
├── [Project]-INS-DC10_Level_Instruments.pdf
├── [Project]-INS-DC11_Resistance_Temperature_Sensors.pdf
├── [Project]-INS-DC12_Differential_Pressure_Instruments.pdf
├── [Project]-INS-DC13_Pressure_Gages.pdf
├── [Project]-INS-DC14_Glass_Thermometers.pdf
└── [Project]-INS-DC15_Temperature_Instruments.pdf
```

#### 2.2 LIST OF DOCUMENTS (Engineering Lists & Matrices)
**Deliverables** (7+ documents):
1. **Material List** (`*-LT02_Material_List_*.pdf`)
   - Bill of materials for complete system
   - Equipment tags and descriptions
   - Quantities and specifications

2. **Instrument Index** (`*-LT03_Instrument_Index.pdf`)
   - Complete list of all instruments
   - Tag numbers (ISA-5.1 format)
   - Service descriptions
   - Instrument types and ranges

3. **Cause-Effect Matrix** (`*-LT04_Matrix_Causa_Efecto.pdf`)
   - Interlock logic matrix
   - Input conditions vs. output actions
   - Safety shutdown sequences

4. **I/O Allocation** (`*-LT05_I-O_Allocation.pdf`)
   - PLC I/O module assignments
   - Channel allocations
   - Signal types (DI, AI, DO, AO)
   - Address mapping

5. **Electrical Channels** (`*-LT06_Electrical_channels_*.pdf`)
   - Cable schedules
   - Terminal assignments
   - Signal routing

6. **Process Lines** (`*-LT07_Instrument_process_lines_*.pdf`)
   - Tubing and piping for instruments
   - Material specifications
   - Connection details

**Folder Structure**:
```
2.2. LIST OF DOCUMENTS/
├── [Project]-INS-LT02_Material_List_General_Assembly_Skid.pdf
├── [Project]-INS-LT03_Instrument_Index.pdf
├── [Project]-INS-LT04_Matrix_Causa_Efecto.pdf
├── [Project]-INS-LT05_I-O_Allocation.pdf
├── [Project]-INS-LT06_Electrical_channels_*.pdf
└── [Project]-INS-LT07_Instrument_process_lines_*.pdf
```

#### 2.3 DRAWINGS (Engineering Diagrams)
**Deliverables** (15+ drawings):
1. **P&ID** (`*-PL01_Plano_Tubería_E_Instrumentación_P&ID.pdf`)
   - **MOST CRITICAL DOCUMENT**
   - Piping and Instrumentation Diagram
   - ISA-5.1-2024 compliant symbols
   - Process flow and control loops
   - Safety systems and interlocks

2. **P&ID Symbology** (`*-PL02_Simbologia_P&ID_*.pdf`)
   - Symbol legend
   - Tag numbering system
   - Line identification

3. **Control Architecture** (`*-PL03_Arquitectura_Control_*.pdf`)
   - Network topology
   - PLC/HMI connectivity
   - Communication protocols

4. **Panel Electromechanical Drawings** (`*-PL04_Plano_electromecánico_TC.pdf`)
   - Panel layout
   - Equipment mounting
   - Internal wiring

5. **Connection Diagrams** (`*-PL05-1_* through *-PL05-9_*`)
   - Module-by-module wiring diagrams:
     - DC power distribution
     - Digital Input modules (DI)
     - Analog Input modules (AI)
     - Digital Output modules (DO)
     - Analog Output modules (AO)
     - Communication modules (Modbus, Ethernet)
     - Auxiliary services

6. **Junction Box Diagrams** (`*-PL06_Diagrama_de_conexiones_juction_box.pdf`)

**Folder Structure**:
```
2.3. DRAWINGS/
├── [Project]-INS-PL01_Plano_Tubería_E_Instrumentación_P&ID.pdf ⭐ CRITICAL
├── [Project]-INS-PL02_Simbologia_P&ID.pdf
├── [Project]-INS-PL03_Arquitectura_Control_*.pdf
├── [Project]-INS-PL04_Plano_electromecánico_TC.pdf
├── [Project]-INS-PL05-1_DC-TC_Terminales_alimentación_de_24VDC.pdf
├── [Project]-INS-PL05-2_DC-TC_Alimentación_de_equipos.pdf
├── [Project]-INS-PL05-3_DC-TC_Módulo_01_16_DI.pdf
├── [Project]-INS-PL05-4_DC-TC_Módulo_02_8AI.pdf
├── [Project]-INS-PL05-5_DC-TC_Módulo_02_8AI.pdf
├── [Project]-INS-PL05-6_DC-TC_Módulo_03_8_DO.pdf
├── [Project]-INS-PL05-7_DC-TC_Módulo_04_4AO.pdf
├── [Project]-INS-PL05-8_DC-TC_Módulo_05_Comunicaciones_modbus.pdf
├── [Project]-INS-PL05-9_DC-TC_MÓDULO_SERVICIOS_AUXILIARES.pdf
└── [Project]-INS-PL06_Diagrama_de_conexiones_juction_box.pdf
```

#### 2.4 PROGRAM BACKUP (PLC/HMI Software)
**Deliverables** (2 critical files):

1. **PLC Program Backup** (`*.ACD` for Allen-Bradley, `*.s7p` for Siemens)
   - Complete PLC logic
   - Ladder logic, function blocks, structured text
   - Tag database
   - I/O configuration
   - Communication settings
   - **Example**: `PAD2_SEP.ACD` (3.85 MB - Allen-Bradley RSLogix/Studio 5000)

2. **HMI Program Backup** (`*.mer` for Weintek, `*.hmi` for Siemens)
   - SCADA screens
   - Graphics and animations
   - Alarm configurations
   - Historical data trending
   - **Example**: `Separator_PAD2_V10.mer` (4.29 MB - Weintek EasyBuilder Pro)

**Folder Structure**:
```
2.4. PROGRAM BACKUP/
├── 2.4.1. PLC/
│   └── [Project]_PLC.ACD (or .s7p)
└── 2.4.2. HMI/
    └── [Project]_HMI_V[Version].mer (or .hmi)
```

**Key AI Agent Actions**:
- **CRITICAL**: PLC/HMI backups are the most valuable project assets
- Store backups in multiple locations (CRM, cloud, local servers)
- Version control for all program changes
- Document program revision history
- Include README with:
  - Software version (RSLogix 5000 v32, Studio 5000 v33, etc.)
  - Hardware compatibility (PLC model, firmware version)
  - Special configuration notes

**Complete Phase 2 Folder Structure**:
```
2. INSTRUMENTATION AND CONTROL/
├── 2.1. DOCUMENT/          (15+ technical datasheets)
├── 2.2. LIST OF DOCUMENTS/ (7+ engineering lists)
├── 2.3. DRAWINGS/          (15+ P&IDs and wiring diagrams)
└── 2.4. PROGRAM BACKUP/    (2 critical program backups)
    ├── 2.4.1. PLC/
    └── 2.4.2. HMI/
```

---

### **Phase 3: ELECTRICAL DESIGN** ⚡
**Purpose**: Low voltage electrical system design and distribution

**Deliverables**:

#### 3.1 DOCUMENTS
1. **Low Voltage Panel Specifications** (`*-DC01_Low_Voltage_Panel_Specifications.pdf`)
   - Panel dimensions and enclosure type (NEMA/IP rating)
   - Breaker schedules
   - Cable routing
   - Grounding and bonding

**Folder Structure**:
```
3.1. DOCUMENT/
└── [Project]-ELE-DC01_Low_Voltage_Panel_Specifications.pdf
```

#### 3.2 DRAWINGS
1. **Single-Line Diagram** (`*-PL01_Diagrama_unifilar_*.pdf`)
   - Main power distribution
   - Breaker ratings
   - Transformer specifications
   - Load calculations

2. **Panel Electromechanical Drawing** (`*-PL02_Plano_electromecánico_TBT.pdf`)
   - Low voltage distribution panel (TBT = Tablero Baja Tensión)
   - Component layout
   - Internal wiring

3. **Junction Box Drawing** (`*-PL03_Plano_Electromecánico_Junction_Box.pdf`)
   - Field junction boxes
   - Terminal blocks
   - Cable entries

**Folder Structure**:
```
3.2. DRAWINGS/
├── [Project]-ELE-PL01_Diagrama_unifilar_*.pdf
├── [Project]-ELE-PL02_Plano_electromecánico_TBT.pdf
└── [Project]-ELE-PL03_Plano_Electromecánico_Junction_Box.pdf
```

**Complete Phase 3 Folder Structure**:
```
3. ELECTRICAL/
├── 3.1. DOCUMENT/
└── 3.2. DRAWINGS/
```

---

### **Phase 4: MECHANICAL DESIGN** 🔧
**Purpose**: Mechanical integration, layouts, and physical installation

**Deliverables**:

#### 4.1 DRAWINGS (21+ mechanical drawings)
1. **Layout Plans** (`*-PL01-1_*, *-PL01-2_*`)
   - Equipment location plans
   - General site layouts
   - Fiber optic cable routes
   - Zoom views of critical areas

2. **Isometric Drawings** (`*-PL02-*_*, *-PL03-*_*`)
   - 3D piping isometrics (15+ drawings)
   - Instrumentation hookups
   - Process lines
   - Multiple views per vessel/equipment

3. **Shelter/Enclosure Designs** (`*-PL04_*_*`)
   - Control shelter layout
   - Views: Isometric, Top, Front, Rear, Sides
   - Ventilation and HVAC
   - Access doors and windows

4. **Installation Proposals** (`*-PL05-*_*`)
   - Equipment mounting details
   - Flow meter installations
   - Support structures
   - Views: Isometric, Front, Top

**Folder Structure**:
```
4.1. DRAWINGS/
├── [Project]-MEC-PL01-1_Layout_General.pdf
├── [Project]-MEC-PL01-2_Layout_Zoom.pdf
├── [Project]-MEC-PL02-1_Isométrico_1.pdf
├── [Project]-MEC-PL02-2_Isométrico_2.pdf
├── ... (15+ isometric drawings)
├── [Project]-MEC-PL04_1_Shelter_Isométrica.pdf
├── [Project]-MEC-PL04_2_Shelter_Vista_Superior.pdf
├── [Project]-MEC-PL04_3_Shelter_Vista_Frontal.pdf
├── [Project]-MEC-PL04_4_Shelter_Vista_Posterior.pdf
├── [Project]-MEC-PL04_5_Shelter_Vistas_Laterales.pdf
└── [Project]-MEC-PL05-*_Instalación_*.pdf
```

**Complete Phase 4 Folder Structure**:
```
4. MECHANIC/
└── 4.1. DRAWINGS/ (21+ isometrics, layouts, shelter plans)
```

---

## 📂 COMPLETE PROJECT FOLDER STRUCTURE

```
[PROJECT_CODE]-[PROJECT_NAME]/
│
├── 1. QUALITY/
│   ├── 1.1. DOCUMENT/
│   │   └── [Project]-INS-DC01_Plan_de_calidad.pdf
│   └── 1.2. LIST OF DOCUMENTS/
│       └── [Project]-GRL-LT01_Dossier_ingeniería.pdf
│
├── 2. INSTRUMENTATION AND CONTROL/
│   ├── 2.1. DOCUMENT/          (15+ datasheets & specs)
│   ├── 2.2. LIST OF DOCUMENTS/ (7+ engineering lists)
│   ├── 2.3. DRAWINGS/          (15+ P&IDs & diagrams)
│   └── 2.4. PROGRAM BACKUP/
│       ├── 2.4.1. PLC/         (PLC program backup)
│       └── 2.4.2. HMI/         (HMI program backup)
│
├── 3. ELECTRICAL/
│   ├── 3.1. DOCUMENT/
│   └── 3.2. DRAWINGS/
│
├── 4. MECHANIC/
│   └── 4.1. DRAWINGS/
│
└── project_metadata.json (AI-generated project metadata)
```

**Total Files**: 60-70 technical documents
**Total Size**: 50-100 MB per project
**Critical Assets**: PLC/HMI backups (2.4.1, 2.4.2)

---

## 🏷️ INSA DOCUMENT NAMING CONVENTION

**Format**:
```
[PROJECT_CODE]-[DISCIPLINE]-[DOC_TYPE][NUMBER]_[Description].[ext]
```

**Components**:
- **PROJECT_CODE**: Client/project identifier (e.g., `INSAGTEC-6598`)
- **DISCIPLINE**: Engineering discipline code
  - `GRL`: General
  - `INS`: Instrumentation & Control
  - `ELE`: Electrical
  - `MEC`: Mechanical
- **DOC_TYPE**: Document type
  - `DC`: Document (specifications, datasheets)
  - `LT`: List (indexes, matrices, schedules)
  - `PL`: Plano/Drawing (diagrams, schematics)
- **NUMBER**: Sequential document number (01, 02, 03...)
  - For multi-page drawings: `PL01-1`, `PL01-2`, etc.
- **Description**: Brief description in Spanish or English
- **ext**: File extension (`.pdf`, `.ACD`, `.mer`, etc.)

**Examples**:
```
INSAGTEC-6598-INS-DC01_Plan_de_calidad.pdf
INSAGTEC-6598-INS-LT03_Instrument_Index.pdf
INSAGTEC-6598-INS-PL01_Plano_Tubería_E_Instrumentación_P&ID.pdf
INSAGTEC-6598-ELE-PL01_Diagrama_unifilar_sep_2_a_scada.pdf
INSAGTEC-6598-MEC-PL04_1_Plano_Shelter_Pad_2_Vista_Isométrica.pdf
PAD2_SEP.ACD (PLC backup - simplified naming)
```

---

## 🎨 INSA P&ID DESIGN STANDARDS

### **Compliance Standards**:
1. **ISA-5.1-2024**: Instrumentation Symbols and Identification
2. **API RP 12J**: Specification for Oil and Gas Separators
3. **API RP 14C**: Analysis, Design, Installation, and Testing of Safety Systems for Offshore Production Facilities

### **P&ID Components** (Typical Three-Phase Separator):

#### **Vessels & Equipment**:
- **V-100**: Separator vessel (horizontal/vertical)
  - Typical: 1000 bbl capacity
  - Material: A516 Gr.70 Carbon Steel
  - Design pressure: 1440 psi

#### **Instrumentation** (ISA-5.1 Tag Format):
- **Flow Transmitters**: `FT-101`, `FT-102`, `FT-103`
  - Types: Coriolis, Vortex, Turbine, Magnetic
  - Output: 4-20mA to PLC

- **Pressure Transmitters**: `PT-100`, `PT-101`
  - Range: 0-2000 psi typical
  - Output: 4-20mA to PLC

- **Temperature Transmitters**: `TT-100`, `TT-101`
  - RTD or Thermocouple
  - Output: 4-20mA to PLC

- **Level Transmitters**: `LT-100`, `LT-101`, `LT-102`
  - Types: Radar, Displacer, Ultrasonic
  - Output: 4-20mA to PLC

- **Level Switches** (Alarms): `LSH-100` (High), `LSL-101` (Low)
  - Discrete on/off signals to PLC

#### **Control Loops** (PID Controllers):
- **PIC-100**: Pressure Indicator Controller
  - Input: PT-100 (4-20mA)
  - Output: Control signal to PCV-100 (control valve)
  - Hosted in PLC

- **TIC-100**: Temperature Indicator Controller
- **LIC-100**: Level Indicator Controller
- **FIC-100**: Flow Indicator Controller

#### **Final Control Elements**:
- **Control Valves**: `PCV-100`, `TCV-100`, `LCV-100`, `FCV-100`
  - Pneumatic or electric actuators
  - Input: 4-20mA from PLC

- **Shutdown Valves**: `SDV-100`, `SDV-101`
  - Fail-safe (normally closed or normally open)
  - Emergency shutdown logic in PLC

- **Manual Valves**: `HV-100`, `HV-101`
  - Hand-operated (no automation)

#### **Pumps & Compressors**:
- **Pumps**: `P-100A`, `P-100B` (oil/water export pumps)
  - VFD (Variable Frequency Drive) control
  - Start/stop from PLC

#### **Control System**:
- **PLC**: `PLC-001` (Siemens S7-1500 or Allen-Bradley ControlLogix)
  - Redundant CPU for critical applications
  - I/O modules: DI, AI, DO, AO, Modbus
  - Communication: Ethernet/IP, Modbus TCP

- **HMI**: `HMI-001` (15" touchscreen SCADA)
  - Weintek, Siemens WinCC, Rockwell FactoryTalk
  - Real-time process visualization
  - Alarm management

### **P&ID Signal Types**:
- **4-20mA**: Analog signals (transmitters to PLC, PLC to valves)
- **Digital I/O**: On/off signals (switches, valve positions)
- **Modbus RTU/TCP**: Serial communication (flowmeters, analyzers)
- **Ethernet/IP**: PLC-HMI communication

### **P&ID Connections** (Typical):
```
Process Flow:
[Feed In] → [V-100 Separator] → [Oil Out], [Water Out], [Gas Out]

Control Loops:
PT-100 → PLC-001 → PIC-100 → PCV-100 (Pressure control)
TT-100 → PLC-001 → TIC-100 → TCV-100 (Temperature control)
LT-100 → PLC-001 → LIC-100 → LCV-100 (Level control)
FT-101 → PLC-001 → FIC-100 → FCV-100 (Flow control)

Safety Systems:
LSH-100 → PLC-001 → SDV-100 (High level shutdown)
PSH-100 → PLC-001 → SDV-101 (High pressure shutdown)
```

---

## 🤖 AI AGENT INSTRUCTIONS

### **When Creating a New Project**:

1. **Create Folder Structure**:
```bash
mkdir -p "[PROJECT_CODE]-[PROJECT_NAME]"/{1. QUALITY/{1.1. DOCUMENT,1.2. LIST OF DOCUMENTS},2. INSTRUMENTATION AND CONTROL/{2.1. DOCUMENT,2.2. LIST OF DOCUMENTS,2.3. DRAWINGS,2.4. PROGRAM BACKUP/{2.4.1. PLC,2.4.2. HMI}},3. ELECTRICAL/{3.1. DOCUMENT,3.2. DRAWINGS},4. MECHANIC/4.1. DRAWINGS}
```

2. **Generate P&ID** (if requested):
```bash
cd /home/wil/pid-generator
python3 separador_trifasico.py  # or custom P&ID script
```

3. **Create project_metadata.json**:
```json
{
  "project_info": {
    "project_code": "[CODE]",
    "project_name": "[NAME]",
    "customer": "[CUSTOMER]",
    "project_type": "Industrial Automation - [TYPE]",
    "date_imported": "[ISO 8601 timestamp]",
    "source": "[Google Drive / Windows Desktop / etc]"
  },
  "project_statistics": { ... },
  "project_structure": { ... },
  "technical_details": { ... }
}
```

4. **Email Deliverables** (if requested):
```bash
cd /home/wil/pid-generator
python3 send_pid_email.py  # or custom email script
# SMTP: localhost:25 (Postfix)
# From: w.aroca@insaing.com
# Attachments: SVG, DXF, PDF, JSON
```

5. **Store in CRM**:
```bash
cp -r [SOURCE]/* /home/wil/crm-files/[PROJECT_CODE]/
```

### **When Importing an Existing Project**:

1. **Verify Folder Structure**:
   - Ensure 4 main phases are present
   - Check for critical documents (P&ID, PLC/HMI backups)
   - Validate file naming convention

2. **Create Metadata**:
   - Extract project code from filenames
   - Count files by category
   - Calculate total size
   - Identify customer from folder name or documents

3. **Store in CRM**:
   - `/home/wil/crm-files/[PROJECT_CODE]/`
   - Create `project_metadata.json`
   - Link to ERPNext CRM (if applicable)

4. **Document in RAG**:
   - Update this file with any new patterns
   - Note unique project requirements
   - Record lessons learned

### **CRM Integration (ERPNext)**:

Use these ERPNext MCP tools to register projects:

1. **Check if Customer Exists**:
```
erpnext_list_customers (search for customer name)
```

2. **Create Customer** (if not exists):
```
erpnext_create_customer(
  customer_name="[Customer Name]",
  customer_type="Company",
  territory="[Country]"
)
```

3. **Create Project**:
```
erpnext_create_project(
  project_name="[PROJECT_CODE] - [Description]",
  customer="[Customer Name]",
  project_type="External",
  status="Open"
)
```

4. **Attach Documents**:
- Upload files from `/home/wil/crm-files/[PROJECT_CODE]/`
- Link to customer and project records
- Categorize by phase (Quality, Instrumentation, Electrical, Mechanical)

---

## 📊 PROJECT METADATA SCHEMA

AI agents should always create a `project_metadata.json` file with this structure:

```json
{
  "project_info": {
    "project_code": "string",
    "project_name": "string",
    "customer": "string",
    "project_type": "string",
    "status": "Completed | In Progress | On Hold",
    "date_imported": "ISO 8601 timestamp",
    "source": "Google Drive | Windows Desktop | Git | Email",
    "source_url": "string (optional)",
    "imported_by": "Claude Code - INSA Automation DevSecOps",
    "storage_path": "/home/wil/crm-files/[PROJECT_CODE]"
  },
  "project_statistics": {
    "total_files": 0,
    "total_size": "string (e.g., '66 MB')",
    "file_categories": {
      "quality": 0,
      "instrumentation_control": 0,
      "electrical": 0,
      "mechanical": 0
    }
  },
  "project_structure": {
    "1_QUALITY": { ... },
    "2_INSTRUMENTATION_AND_CONTROL": { ... },
    "3_ELECTRICAL": { ... },
    "4_MECHANICAL": { ... }
  },
  "technical_details": {
    "control_system": { ... },
    "instrumentation": { ... },
    "process_equipment": { ... }
  },
  "compliance_standards": {
    "isa": "ISA-5.1-2024",
    "api": ["API RP 12J", "API RP 14C"],
    "electrical": "IEC 61131-3",
    "hmi": "ISA-101"
  },
  "project_phases": [
    {
      "phase": "1. Quality & Planning",
      "status": "Complete | In Progress | Pending",
      "deliverables": []
    }
  ],
  "related_projects": { ... },
  "next_steps": { ... },
  "notes": []
}
```

---

## 🔍 EXAMPLE PROJECT: INSAGTEC-6598

**Real-world example** of INSA project structure:

**Project**: INSAGTEC-6598 - PAD-2 Test Separator
**Customer**: Deilim Genesis Fertilizers
**Type**: Three-phase oil/water/gas separator automation
**Size**: 66 MB, 63 files
**PLC**: Allen-Bradley (PAD2_SEP.ACD - 3.85 MB)
**HMI**: Weintek (Separator_PAD2_V10.mer - 4.29 MB)

**File Breakdown**:
- Quality: 2 files
- Instrumentation & Control: 37 files (15 docs, 7 lists, 15 drawings, 2 backups)
- Electrical: 4 files
- Mechanical: 21 files

**Storage**: `/home/wil/crm-files/INSAGTEC-6598/`
**Metadata**: `/home/wil/crm-files/INSAGTEC-6598/project_metadata.json`

---

## 📧 EMAIL COMMUNICATION

### **Email Templates**:

#### **P&ID Delivery Email**:
```
From: w.aroca@insaing.com
To: [client email]
Subject: P&ID [Project Name] - [Equipment Description]

[HTML-formatted email with:]
- Project summary
- Component count
- Standards compliance (ISA-5.1, API RP 12J, API RP 14C)
- File attachments (SVG, DXF, JSON, PDF)
- Contact information
```

#### **Project Delivery Email**:
```
From: w.aroca@insaing.com
To: [client email]
Subject: [PROJECT_CODE] - Engineering Deliverables

[HTML-formatted email with:]
- Project completion notice
- Deliverable summary by phase
- File count and size
- PLC/HMI backup information
- Access instructions (if cloud storage)
```

**SMTP Configuration**:
- Server: `localhost:25` (Postfix)
- No authentication required
- Support for attachments up to 25 MB

---

## 🛠️ TOOLS & SOFTWARE

### **P&ID Generation**:
- **Python Libraries**: `svgwrite`, `ezdxf`, `numpy`
- **Output Formats**: SVG (vector graphics), DXF (AutoCAD), JSON (metadata)
- **Standards**: ISA-5.1-2024 symbols

### **PLC Programming**:
- **Allen-Bradley**: RSLogix 5000, Studio 5000 (*.ACD files)
- **Siemens**: TIA Portal (*.s7p files)
- **Languages**: Ladder Logic, Function Block, Structured Text

### **HMI Development**:
- **Weintek**: EasyBuilder Pro (*.mer files)
- **Siemens**: WinCC (*.hmi files)
- **Rockwell**: FactoryTalk View

### **CAD Software**:
- **AutoCAD**: For P&IDs, isometric drawings
- **SolidWorks**: For 3D mechanical designs

### **Document Management**:
- **ERPNext CRM**: Customer and project tracking
- **Git**: Version control for engineering files
- **Google Drive**: Cloud storage and sharing

---

## 📝 LESSONS LEARNED

### **Critical Success Factors**:
1. **P&ID is the master document** - all other documents reference it
2. **PLC/HMI backups are irreplaceable** - store in multiple locations
3. **Consistent naming convention** - enables automation and searchability
4. **Metadata is key** - AI agents need structured project information
5. **4-phase structure** - ensures completeness and traceability

### **Common Pitfalls**:
1. **Missing PLC/HMI backups** - renders project incomplete
2. **Inconsistent file naming** - breaks automation workflows
3. **Incomplete I/O allocation** - causes commissioning delays
4. **Missing cause-effect matrix** - safety system gaps
5. **No document revision control** - creates confusion

### **Best Practices**:
1. **Always create project_metadata.json** - enables AI agent understanding
2. **Store projects in `/home/wil/crm-files/[PROJECT_CODE]/`**
3. **Link projects to CRM** - customer relationship management
4. **Version control for programs** - Git for PLC/HMI code
5. **Email deliverables** - keep clients informed

---

## 🚀 FUTURE ENHANCEMENTS

### **Planned Features**:
1. **Automated P&ID Generation from BOM** (InvenTree integration)
2. **PLC Code Analysis** - extract I/O count from *.ACD files
3. **3D CAD Integration** - CadQuery MCP for vessel modeling
4. **Automated Quality Checks** - verify document completeness
5. **Project Dashboard** - Grafana analytics for project metrics

### **AI Agent Capabilities**:
1. **Auto-detect project type** from folder structure
2. **Auto-generate P&IDs** based on customer requirements
3. **Auto-populate ERPNext CRM** from project files
4. **Auto-send email notifications** on project milestones
5. **Auto-backup PLC/HMI programs** to Git

---

## 📚 REFERENCE PROJECTS

### **Completed Projects** (for AI training):

1. **INSAGTEC-6598** (PAD-2 Test Separator)
   - Path: `/home/wil/crm-files/INSAGTEC-6598/`
   - Size: 66 MB, 63 files
   - Customer: Deilim Genesis Fertilizers
   - Type: Three-phase separator automation

2. **Separador Trifásico Genérico** (Template P&ID)
   - Path: `/home/wil/pid-generator/`
   - Files: `separador_trifasico.py`, SVG, DXF, JSON
   - Use: Template for new separator projects

### **Templates**:

1. **P&ID Generator Script**: `/home/wil/pid-generator/separador_trifasico.py`
2. **Email Sender Script**: `/home/wil/pid-generator/send_pid_email.py`
3. **CRM Import Script**: `/home/wil/copy_windows_files_to_crm.sh`

---

## 🎓 TRAINING DATA FOR AI AGENTS

### **Key Patterns to Learn**:

1. **Project Code Detection**:
   - Regex: `[A-Z]{4,}-\d{4}` (e.g., INSAGTEC-6598)
   - Extract from filenames: `INSAGTEC-6598-INS-DC01_*.pdf`

2. **Discipline Detection**:
   - `-INS-`: Instrumentation
   - `-ELE-`: Electrical
   - `-MEC-`: Mechanical
   - `-GRL-`: General

3. **Document Type Detection**:
   - `-DC##_`: Document/Datasheet
   - `-LT##_`: List/Table
   - `-PL##_`: Plano/Drawing

4. **Critical File Detection**:
   - `*.ACD`: Allen-Bradley PLC backup
   - `*.s7p`: Siemens PLC backup
   - `*.mer`: Weintek HMI backup
   - `*P&ID*.pdf`: Piping and Instrumentation Diagram

5. **Customer Extraction**:
   - From folder name: `[PROJECT_CODE]-[CUSTOMER_NAME]/`
   - From file content: Search for "Cliente:" or "Customer:"

### **AI Agent Prompts** (examples):

```
"Import project INSAGTEC-6598 from Google Drive to CRM"
→ Download files, create folder structure, generate metadata, link to ERPNext

"Generate P&ID for three-phase separator with 1000 bbl capacity"
→ Run separador_trifasico.py, generate SVG/DXF/JSON, email to client

"Show me all projects for customer Deilim Genesis Fertilizers"
→ Query /home/wil/crm-files/, filter by customer in metadata.json

"What PLC model is used in INSAGTEC-6598?"
→ Read project_metadata.json → technical_details → control_system → plc

"Backup PLC program for project INSAGTEC-6598"
→ Copy /home/wil/crm-files/INSAGTEC-6598/2. INSTRUMENTATION AND CONTROL/2.4. PROGRAM BACKUP/2.4.1. PLC/*.ACD to backup location
```

---

## ✅ CHECKLIST FOR AI AGENTS

### **Before Importing a Project**:
- [ ] Verify source access (Google Drive, Windows SMB, SSH, etc.)
- [ ] Check available disk space
- [ ] Identify project code and customer name
- [ ] Estimate file count and size

### **During Import**:
- [ ] Create folder structure: `/home/wil/crm-files/[PROJECT_CODE]/`
- [ ] Copy all files preserving directory structure
- [ ] Verify file integrity (checksums if available)
- [ ] Identify critical files (PLC/HMI backups, P&ID)

### **After Import**:
- [ ] Generate `project_metadata.json`
- [ ] Count files by category (Quality, Instrumentation, Electrical, Mechanical)
- [ ] Verify PLC/HMI backups are present
- [ ] Create customer in ERPNext CRM (if not exists)
- [ ] Create project record in ERPNext CRM
- [ ] Link documents to CRM records
- [ ] Update this RAG memory file if new patterns discovered

### **Quality Checks**:
- [ ] All 4 phases present (Quality, Instrumentation, Electrical, Mechanical)?
- [ ] P&ID exists (`*-PL01_Plano_Tubería_E_Instrumentación_P&ID.pdf`)?
- [ ] PLC backup exists (`2.4.1. PLC/*.ACD or *.s7p`)?
- [ ] HMI backup exists (`2.4.2. HMI/*.mer or *.hmi`)?
- [ ] File naming follows convention (`[CODE]-[DISC]-[TYPE]##_[Desc].ext`)?
- [ ] Metadata JSON is complete and valid?

---

## 🔗 INTEGRATION POINTS

### **ERPNext CRM**:
- **Web UI**: http://100.100.101.1:9000
- **MCP Tools**: 33 tools available
- **Use Cases**:
  - Customer management
  - Project tracking
  - Document attachment
  - Quotation generation
  - Sales order management

### **InvenTree Inventory**:
- **Web UI**: http://100.100.101.1:9600
- **MCP Tools**: 5 tools available
- **Use Cases**:
  - BOM (Bill of Materials) creation
  - Part tracking
  - Pricing calculation
  - Equipment tracking per customer

### **Mautic Marketing**:
- **Web UI**: http://100.100.101.1:9700
- **MCP Tools**: 27 tools available
- **Use Cases**:
  - Contact management
  - Email campaigns
  - Lead nurturing

### **n8n Workflow Automation**:
- **Web UI**: http://100.100.101.1:5678
- **MCP Tools**: 23 tools available (NEW - Phase 6)
- **Use Cases**:
  - ERPNext ↔ Mautic sync
  - Automated project notifications
  - Document processing workflows

---

## 📞 CONTACTS

**Primary Contact**: w.aroca@insaing.com
**Technical Contact**: j.casas@insaing.com
**Company**: INSA Automation Corp
**Division**: Oil & Gas Industrial Automation
**Server**: iac1 (100.100.101.1)

---

## 📝 VERSION HISTORY

- **v1.0** - October 18, 2025 - Initial RAG memory document created
  - Based on INSAGTEC-6598 project analysis
  - Documented 4-phase INSA project lifecycle
  - Created AI agent instructions and checklists

---

**END OF INSA PROJECT WORKFLOW RAG MEMORY**

This document should be referenced by all INSA AI agents when handling project-related tasks. Always keep this file updated with new patterns, lessons learned, and best practices.

**Storage**: `/home/wil/INSA_PROJECT_WORKFLOW_RAG_MEMORY.md`
**Purpose**: RAG (Retrieval-Augmented Generation) memory for AI agents
**Audience**: Claude Code, ERPNext agents, CRM agents, automation agents
**Maintenance**: Update whenever new project patterns are discovered
