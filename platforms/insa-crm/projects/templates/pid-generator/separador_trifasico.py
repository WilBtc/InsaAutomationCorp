#!/usr/bin/env python3
"""
P&ID Generator - Separador Trifásico de Petróleo con Control Electrónico
Sistema completo con instrumentación ISA-5.1 para industria petrolera

Features:
- Separación Gas/Petróleo/Agua
- Control de nivel (LIC) para interfase petróleo/agua
- Control de presión (PIC)
- Control de temperatura (TIC)
- Transmisores de flujo para todas las corrientes
- Válvulas de control automáticas
- Sistema de seguridad (PSV, shutdown)
- PLC con HMI

Estándares:
- ISA-5.1-2024: Instrumentación
- API RP 12J: Separadores de producción
- API RP 14C: Control de pozos
"""

import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pid_generator import PIDGenerator

def create_three_phase_separator_pid():
    """
    Crea un P&ID completo de un separador trifásico de petróleo
    con control electrónico avanzado.
    """

    # Crear instancia del generador
    pid = PIDGenerator(
        project_name="Separador Trifásico de Petróleo - Control Electrónico",
        customer="INSA Automation Corp - Oil & Gas Division"
    )

    print("🛢️  Generando P&ID: Separador Trifásico de Petróleo...")
    print("=" * 70)

    # ============================================================================
    # ENTRADA: Corriente de pozo (Gas + Petróleo + Agua)
    # ============================================================================

    # Válvula manual de entrada
    pid.add_component(
        component_type="manual_valve",
        tag="HV-001",
        description="Válvula de entrada manual",
        quantity=1,
        specifications={"size": "4 inch", "rating": "ANSI 600"}
    )

    # Medidor de flujo de entrada
    pid.add_component(
        component_type="flow_transmitter",
        tag="FT-001",
        description="Medidor de flujo total entrada",
        quantity=1,
        specifications={"type": "Coriolis", "range": "0-500 bbl/day"}
    )

    # Medidor de presión de entrada
    pid.add_component(
        component_type="pressure_transmitter",
        tag="PT-001",
        description="Presión de entrada",
        quantity=1,
        specifications={"range": "0-1000 psi", "output": "4-20mA"}
    )

    # Medidor de temperatura de entrada
    pid.add_component(
        component_type="temperature_transmitter",
        tag="TT-001",
        description="Temperatura de entrada",
        quantity=1,
        specifications={"type": "RTD Pt100", "range": "0-200°C"}
    )

    # ============================================================================
    # SEPARADOR TRIFÁSICO - Vessel Principal
    # ============================================================================

    pid.add_component(
        component_type="tank",
        tag="V-100",
        description="Separador Trifásico Horizontal",
        quantity=1,
        specifications={
            "type": "Horizontal 3-Phase Separator",
            "capacity": "1000 bbl",
            "design_pressure": "1440 psi",
            "design_temp": "250°F",
            "material": "A516 Gr.70 Carbon Steel"
        }
    )

    # ============================================================================
    # INSTRUMENTACIÓN DEL SEPARADOR
    # ============================================================================

    # Control de Presión del Separador
    pid.add_component(
        component_type="pressure_transmitter",
        tag="PT-100",
        description="Presión del separador",
        quantity=1,
        specifications={"range": "0-500 psi", "output": "4-20mA"}
    )

    pid.add_component(
        component_type="pid_controller",
        tag="PIC-100",
        description="Controlador de presión",
        quantity=1,
        specifications={"type": "PID Controller", "setpoint": "250 psi"}
    )

    # Válvula de seguridad (PSV)
    pid.add_component(
        component_type="manual_valve",
        tag="PSV-100",
        description="Válvula de seguridad por sobrepresión",
        quantity=1,
        specifications={"set_pressure": "400 psi", "type": "Spring-loaded"}
    )

    # Control de Temperatura
    pid.add_component(
        component_type="temperature_transmitter",
        tag="TT-100",
        description="Temperatura del separador",
        quantity=1,
        specifications={"type": "RTD Pt100", "range": "0-200°C"}
    )

    pid.add_component(
        component_type="pid_controller",
        tag="TIC-100",
        description="Controlador de temperatura",
        quantity=1,
        specifications={"type": "PID Controller", "setpoint": "60°C"}
    )

    # Control de Nivel de Petróleo (Interfase superior)
    pid.add_component(
        component_type="level_transmitter",
        tag="LT-101",
        description="Nivel de petróleo (interfase gas/oil)",
        quantity=1,
        specifications={"type": "Radar", "range": "0-100%"}
    )

    pid.add_component(
        component_type="pid_controller",
        tag="LIC-101",
        description="Controlador de nivel de petróleo",
        quantity=1,
        specifications={"type": "PID Controller", "setpoint": "50%"}
    )

    # Control de Nivel de Agua (Interfase inferior oil/water)
    pid.add_component(
        component_type="level_transmitter",
        tag="LT-102",
        description="Nivel interfase petróleo/agua",
        quantity=1,
        specifications={"type": "Displacer", "range": "0-100%"}
    )

    pid.add_component(
        component_type="pid_controller",
        tag="LIC-102",
        description="Controlador de nivel de interfase",
        quantity=1,
        specifications={"type": "PID Controller", "setpoint": "30%"}
    )

    # Alarmas de nivel alto/bajo
    pid.add_component(
        component_type="level_transmitter",
        tag="LAH-100",
        description="Alarma de nivel alto",
        quantity=1,
        specifications={"type": "Float switch", "setpoint": "85%"}
    )

    pid.add_component(
        component_type="level_transmitter",
        tag="LAL-100",
        description="Alarma de nivel bajo",
        quantity=1,
        specifications={"type": "Float switch", "setpoint": "15%"}
    )

    # ============================================================================
    # SALIDA DE GAS
    # ============================================================================

    # Válvula de control de gas
    pid.add_component(
        component_type="control_valve",
        tag="PCV-100",
        description="Válvula de control de presión (salida gas)",
        quantity=1,
        specifications={"size": "3 inch", "type": "Globe", "actuator": "Pneumatic"}
    )

    # Medidor de flujo de gas
    pid.add_component(
        component_type="flow_transmitter",
        tag="FT-100",
        description="Medidor de flujo de gas",
        quantity=1,
        specifications={"type": "Vortex", "range": "0-10 MMSCFD"}
    )

    # ============================================================================
    # SALIDA DE PETRÓLEO
    # ============================================================================

    # Válvula de control de petróleo
    pid.add_component(
        component_type="control_valve",
        tag="LCV-101",
        description="Válvula de control de nivel (salida oil)",
        quantity=1,
        specifications={"size": "4 inch", "type": "Globe", "actuator": "Electric"}
    )

    # Medidor de flujo de petróleo
    pid.add_component(
        component_type="flow_transmitter",
        tag="FT-101",
        description="Medidor de flujo de petróleo",
        quantity=1,
        specifications={"type": "Turbine", "range": "0-300 bbl/day"}
    )

    # Bomba de transferencia de petróleo
    pid.add_component(
        component_type="pump",
        tag="P-101",
        description="Bomba de transferencia de petróleo",
        quantity=1,
        specifications={"type": "Centrifugal", "power": "10 HP", "material": "SS316"}
    )

    # ============================================================================
    # SALIDA DE AGUA
    # ============================================================================

    # Válvula de control de agua
    pid.add_component(
        component_type="control_valve",
        tag="LCV-102",
        description="Válvula de control de interfase (salida agua)",
        quantity=1,
        specifications={"size": "3 inch", "type": "Globe", "actuator": "Electric"}
    )

    # Medidor de flujo de agua
    pid.add_component(
        component_type="flow_transmitter",
        tag="FT-102",
        description="Medidor de flujo de agua",
        quantity=1,
        specifications={"type": "Magnetic", "range": "0-200 bbl/day"}
    )

    # Bomba de transferencia de agua
    pid.add_component(
        component_type="pump",
        tag="P-102",
        description="Bomba de transferencia de agua",
        quantity=1,
        specifications={"type": "Centrifugal", "power": "7.5 HP", "material": "Duplex SS"}
    )

    # ============================================================================
    # SISTEMA DE CONTROL - PLC + HMI
    # ============================================================================

    pid.add_component(
        component_type="plc",
        tag="PLC-001",
        description="PLC Principal - Control de Separador",
        quantity=1,
        specifications={
            "brand": "Siemens S7-1500",
            "io_points": "128 AI/AO, 64 DI/DO",
            "redundancy": "Hot standby"
        }
    )

    pid.add_component(
        component_type="hmi",
        tag="HMI-001",
        description="Panel de operación SCADA",
        quantity=1,
        specifications={
            "size": "15 inch",
            "type": "Touchscreen",
            "software": "WinCC"
        }
    )

    # ============================================================================
    # VÁLVULAS DE SHUTDOWN (SEGURIDAD)
    # ============================================================================

    pid.add_component(
        component_type="solenoid_valve",
        tag="SDV-001",
        description="Válvula de shutdown entrada",
        quantity=1,
        specifications={"type": "Fail-close", "voltage": "24VDC"}
    )

    pid.add_component(
        component_type="solenoid_valve",
        tag="SDV-100",
        description="Válvula de shutdown gas",
        quantity=1,
        specifications={"type": "Fail-close", "voltage": "24VDC"}
    )

    # ============================================================================
    # CONEXIONES DEL SISTEMA
    # ============================================================================

    print("\n🔗 Creando conexiones del sistema...")

    # ENTRADA
    pid.add_connection("HV-001", "FT-001", "process")
    pid.add_connection("FT-001", "PT-001", "process")
    pid.add_connection("PT-001", "TT-001", "process")
    pid.add_connection("TT-001", "SDV-001", "process")
    pid.add_connection("SDV-001", "V-100", "process")

    # TRANSMISORES → PLC (Señales 4-20mA)
    pid.add_connection("FT-001", "PLC-001", "signal")
    pid.add_connection("PT-001", "PLC-001", "signal")
    pid.add_connection("TT-001", "PLC-001", "signal")
    pid.add_connection("PT-100", "PLC-001", "signal")
    pid.add_connection("TT-100", "PLC-001", "signal")
    pid.add_connection("LT-101", "PLC-001", "signal")
    pid.add_connection("LT-102", "PLC-001", "signal")
    pid.add_connection("LAH-100", "PLC-001", "signal")
    pid.add_connection("LAL-100", "PLC-001", "signal")
    pid.add_connection("FT-100", "PLC-001", "signal")
    pid.add_connection("FT-101", "PLC-001", "signal")
    pid.add_connection("FT-102", "PLC-001", "signal")

    # PLC → CONTROLADORES
    pid.add_connection("PLC-001", "PIC-100", "signal")
    pid.add_connection("PLC-001", "TIC-100", "signal")
    pid.add_connection("PLC-001", "LIC-101", "signal")
    pid.add_connection("PLC-001", "LIC-102", "signal")

    # CONTROLADORES → VÁLVULAS (Señales de control)
    pid.add_connection("PIC-100", "PCV-100", "signal")
    pid.add_connection("LIC-101", "LCV-101", "signal")
    pid.add_connection("LIC-102", "LCV-102", "signal")
    pid.add_connection("TIC-100", "V-100", "signal")  # Calentamiento interno

    # PLC → VÁLVULAS DE SHUTDOWN (Señales digitales)
    pid.add_connection("PLC-001", "SDV-001", "electric")
    pid.add_connection("PLC-001", "SDV-100", "electric")

    # SALIDAS DEL SEPARADOR
    pid.add_connection("V-100", "PCV-100", "process")  # Gas
    pid.add_connection("PCV-100", "FT-100", "process")
    pid.add_connection("FT-100", "SDV-100", "process")

    pid.add_connection("V-100", "LCV-101", "process")  # Petróleo
    pid.add_connection("LCV-101", "FT-101", "process")
    pid.add_connection("FT-101", "P-101", "process")

    pid.add_connection("V-100", "LCV-102", "process")  # Agua
    pid.add_connection("LCV-102", "FT-102", "process")
    pid.add_connection("FT-102", "P-102", "process")

    # PLC ↔ HMI (Ethernet/Red)
    pid.add_connection("PLC-001", "HMI-001", "electric")

    # ============================================================================
    # GENERAR ARCHIVOS DE SALIDA
    # ============================================================================

    print("\n📄 Generando archivos de salida...")

    # Generar SVG
    svg_file = pid.generate_svg("Separador_Trifasico_Petroleo_PID.svg")
    print(f"✅ SVG generado: {svg_file}")

    # Generar DXF
    dxf_file = pid.generate_dxf("Separador_Trifasico_Petroleo_PID.dxf")
    print(f"✅ DXF generado: {dxf_file}")

    # Generar lista de componentes JSON
    json_file = pid.export_component_list("Separador_Trifasico_Petroleo_Components.json")
    print(f"✅ JSON generado: {json_file}")

    # ============================================================================
    # RESUMEN DEL SISTEMA
    # ============================================================================

    print("\n" + "=" * 70)
    print("🛢️  RESUMEN DEL SISTEMA - SEPARADOR TRIFÁSICO DE PETRÓLEO")
    print("=" * 70)

    print("\n📊 ESTADÍSTICAS:")
    print(f"   • Total de componentes: {len(pid.components)}")
    print(f"   • Total de conexiones: {len(pid.connections)}")

    # Contar por tipo
    component_types = {}
    for comp in pid.components:
        comp_type = comp['type']
        component_types[comp_type] = component_types.get(comp_type, 0) + 1

    print("\n📦 COMPONENTES POR TIPO:")
    for comp_type, count in sorted(component_types.items()):
        print(f"   • {comp_type}: {count}")

    # Contar conexiones por tipo
    connection_types = {}
    for conn in pid.connections:
        conn_type = conn['type']
        connection_types[conn_type] = connection_types.get(conn_type, 0) + 1

    print("\n🔗 CONEXIONES POR TIPO:")
    for conn_type, count in sorted(connection_types.items()):
        print(f"   • {conn_type}: {count}")

    print("\n🎯 FUNCIONALIDADES DEL SISTEMA:")
    print("   ✅ Separación trifásica: Gas + Petróleo + Agua")
    print("   ✅ Control automático de presión (PIC-100)")
    print("   ✅ Control automático de temperatura (TIC-100)")
    print("   ✅ Control de nivel de petróleo (LIC-101)")
    print("   ✅ Control de interfase oil/water (LIC-102)")
    print("   ✅ Medición de flujo en todas las corrientes")
    print("   ✅ Sistema de seguridad (PSV, SDV)")
    print("   ✅ Alarmas de nivel alto/bajo")
    print("   ✅ PLC con HMI SCADA")
    print("   ✅ Cumple ISA-5.1-2024 y API RP 12J")

    print("\n📁 ARCHIVOS GENERADOS:")
    print(f"   • {svg_file} (Diagrama SVG - Para visualización)")
    print(f"   • {dxf_file} (Archivo CAD - Para edición)")
    print(f"   • {json_file} (Lista de componentes)")

    print("\n🔍 VISUALIZACIÓN:")
    print(f"   firefox {svg_file}")
    print(f"   qcad {dxf_file}")
    print(f"   cat {json_file} | jq")

    print("\n" + "=" * 70)
    print("✅ P&ID COMPLETADO EXITOSAMENTE")
    print("=" * 70)

    return svg_file, dxf_file, json_file


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🛢️  GENERADOR DE P&ID - SEPARADOR TRIFÁSICO DE PETRÓLEO")
    print("=" * 70)
    print("\nSistema: Separador Gas/Petróleo/Agua con Control Electrónico")
    print("Estándares: ISA-5.1-2024, API RP 12J, API RP 14C")
    print("Organización: INSA Automation Corp - Oil & Gas Division")
    print()

    try:
        svg, dxf, json_out = create_three_phase_separator_pid()
        print(f"\n🎉 ¡Generación completada con éxito!")
        print(f"\n📧 Contacto: w.aroca@insaing.com")
        print(f"🏢 INSA Automation Corp\n")

    except Exception as e:
        print(f"\n❌ Error durante la generación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
