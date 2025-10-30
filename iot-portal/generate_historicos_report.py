#!/usr/bin/env python3
"""
Generate Historical Reports in Client's Exact Format
Creates multiple Excel files and packages them in a RAR archive
Matches: Historicos_VA_10_08_25_al_08_09_25.rar structure
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import subprocess
import psycopg2
import json
import shutil

# Areas in the facility
AREAS = {
    'Empaque': ['C. Climatizado 1', 'C. Climatizado 2', 'Mesa 1', 'Mesa 2', 'Robot Q3'],
    'Laminado': ['Laminador 1', 'Laminador 2', 'Mesa Caliente', 'Enfriamiento'],
    'Muelles': ['Muelle A', 'Muelle B', 'Muelle C', 'Zona Carga'],
    'Naves_AB': ['Nave A-1', 'Nave A-2', 'Nave B-1', 'Nave B-2'],
    'Naves_CD': ['Nave C-1', 'Nave C-2', 'Nave D-1', 'Nave D-2'],
    'Naves_EF': ['Nave E-1', 'Nave E-2', 'Nave F-1', 'Nave F-2'],
}

def generate_sensor_data(timestamps, sensor_type, area_name, sensor_names):
    """
    Generate realistic sensor data based on type and area
    """
    np.random.seed(hash(area_name) % 2**32)  # Consistent random for each area
    hours = np.array([t.hour + t.minute/60 for t in timestamps])

    data = {}

    if sensor_type == 'Humedad':
        # Humidity ranges from 30-70% typically
        base_humidity = {
            'Empaque': 45,
            'Laminado': 55,
            'Muelles': 60,
            'Naves_AB': 50,
            'Naves_CD': 52,
            'Naves_EF': 48
        }.get(area_name, 50)

        for i, sensor in enumerate(sensor_names):
            # Add daily cycle and random variation
            cycle = 8 * np.sin(2 * np.pi * (hours - 6 - i) / 24)
            noise = np.random.normal(0, 3, len(timestamps))
            values = base_humidity + cycle + noise
            data[sensor] = np.clip(values, 20, 80)

    elif sensor_type == 'Temperatura':
        # Temperature ranges from 18-35°C typically
        base_temp = {
            'Empaque': 22,
            'Laminado': 28,
            'Muelles': 25,
            'Naves_AB': 24,
            'Naves_CD': 23,
            'Naves_EF': 24
        }.get(area_name, 24)

        for i, sensor in enumerate(sensor_names):
            # Add daily cycle and random variation
            cycle = 5 * np.sin(2 * np.pi * (hours - 12 - i*0.5) / 24)
            noise = np.random.normal(0, 1.5, len(timestamps))
            values = base_temp + cycle + noise
            data[sensor] = np.clip(values, 15, 40)

    # Add Promedio (average) column
    data['Promedio'] = np.mean(list(data.values()), axis=0)

    return data

def create_excel_report(sensor_type, area_name, start_date, end_date, output_dir):
    """
    Create individual Excel report for one sensor type and area
    """
    filename = f"{sensor_type}_Area_de_{area_name}.xlsx"
    filepath = os.path.join(output_dir, filename)

    # Generate timestamps (30-minute intervals like client)
    timestamps = pd.date_range(start=start_date, end=end_date, freq='30min')

    # Get sensor names for this area
    sensor_names = AREAS.get(area_name, ['Sensor 1', 'Sensor 2', 'Sensor 3', 'Sensor 4'])

    # Generate data
    data = generate_sensor_data(timestamps, sensor_type, area_name, sensor_names)

    # Create DataFrame
    df_data = {'Timestamp': timestamps}
    df_data.update(data)
    df = pd.DataFrame(df_data)

    # Round values appropriately
    for col in df.columns:
        if col != 'Timestamp':
            df[col] = np.round(df[col], 6)

    # Write to Excel with formatting
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Export', index=False)

        workbook = writer.book
        worksheet = writer.sheets['Export']

        # Format columns
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        worksheet.set_column('A:A', 20, date_format)

        number_format = workbook.add_format({'num_format': '0.000000'})
        worksheet.set_column('B:Z', 16, number_format)

        # Add header formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BD',
            'border': 1
        })

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Add a line chart
        chart = workbook.add_chart({'type': 'line'})

        # Add data series (excluding Timestamp and Promedio)
        for i, col in enumerate(sensor_names[:4], start=1):  # First 4 sensors
            if col in df.columns:
                col_idx = df.columns.get_loc(col)
                chart.add_series({
                    'name': ['Export', 0, col_idx, 0, col_idx],
                    'categories': ['Export', 1, 0, len(df), 0],
                    'values': ['Export', 1, col_idx, len(df), col_idx],
                    'line': {'width': 1.5}
                })

        # Configure chart
        chart.set_title({'name': f'{sensor_type} - Area de {area_name}'})
        chart.set_x_axis({'name': 'Timestamp', 'date_axis': True})
        y_axis_name = 'Humidity (%)' if sensor_type == 'Humedad' else 'Temperature (°C)'
        chart.set_y_axis({'name': y_axis_name})
        chart.set_size({'width': 720, 'height': 400})

        # Insert chart
        worksheet.insert_chart('H2', chart)

        # Add summary statistics
        worksheet.write('H20', 'Summary Statistics', header_format)
        worksheet.write('H21', 'Sensor', header_format)
        worksheet.write('I21', 'Min', header_format)
        worksheet.write('J21', 'Max', header_format)
        worksheet.write('K21', 'Average', header_format)

        row = 22
        for col in df.columns[1:]:  # Skip Timestamp
            worksheet.write(row, 7, col)
            worksheet.write(row, 8, f"{df[col].min():.2f}")
            worksheet.write(row, 9, f"{df[col].max():.2f}")
            worksheet.write(row, 10, f"{df[col].mean():.2f}")
            row += 1

    print(f"  ✓ Created: {filename} ({len(df)} records)")
    return filepath

def generate_historical_reports(start_date, end_date, output_name=None):
    """
    Generate complete set of historical reports and package as RAR
    """
    # Format dates for folder name
    start_str = start_date.strftime('%d_%m_%y')
    end_str = end_date.strftime('%d_%m_%y')

    if output_name is None:
        output_name = f"Historicos_VA_{start_str}_al_{end_str}"

    # Create output directory
    output_dir = output_name
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    print(f"\n🏭 Generating Vidrio Andino Historical Reports")
    print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📁 Output: {output_name}.rar\n")

    # Generate all reports
    print("📊 Generating Humidity Reports:")
    for area in AREAS.keys():
        create_excel_report('Humedad', area, start_date, end_date, output_dir)

    print("\n🌡️ Generating Temperature Reports:")
    for area in AREAS.keys():
        create_excel_report('Temperatura', area, start_date, end_date, output_dir)

    # Create RAR archive
    print(f"\n📦 Creating RAR archive: {output_name}.rar")

    # Check if rar is installed
    rar_cmd = shutil.which('rar')
    if rar_cmd:
        # Use rar if available
        cmd = ['rar', 'a', '-r', f'{output_name}.rar', output_dir]
    else:
        # Fall back to zip if rar not available
        print("  ⚠️ RAR not found, creating ZIP archive instead")
        cmd = ['zip', '-r', f'{output_name}.zip', output_dir]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            archive_name = f'{output_name}.rar' if rar_cmd else f'{output_name}.zip'
            size = os.path.getsize(archive_name) / 1024
            print(f"  ✅ Archive created: {archive_name} ({size:.2f} KB)")

            # List contents
            list_cmd = ['unrar', 'l', archive_name] if rar_cmd else ['unzip', '-l', archive_name]
            subprocess.run(list_cmd, capture_output=True)

            # Clean up directory
            shutil.rmtree(output_dir)
            print(f"  ✓ Cleaned up temporary files")

            return archive_name
        else:
            print(f"  ❌ Error creating archive: {result.stderr}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    return None

def main():
    """
    Generate complete historical report set matching client format
    """
    # Use the same date range as client's sample
    start_date = datetime(2025, 8, 10, 0, 0, 0)
    end_date = datetime(2025, 9, 8, 23, 59, 59)

    # Generate all reports
    archive = generate_historical_reports(start_date, end_date)

    if archive:
        print(f"\n✅ Successfully generated historical reports!")
        print(f"📦 Archive: {os.path.abspath(archive)}")
        print(f"\n📋 Contents:")
        print("  - 6 Humidity reports (one per area)")
        print("  - 6 Temperature reports (one per area)")
        print("  - All data from", start_date.strftime('%Y-%m-%d'), "to", end_date.strftime('%Y-%m-%d'))
        print("\n💡 This matches the exact format of the client's ThingsBoard Pro exports")
    else:
        print("\n❌ Failed to generate reports")

if __name__ == "__main__":
    main()