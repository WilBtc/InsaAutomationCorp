# INSA Automation Corp - Autonomous Industrial Platform

[![CodeQL](https://github.com/WilBtc/InsaAutomationCorp/workflows/CodeQL%20Security%20Scan/badge.svg)](https://github.com/WilBtc/InsaAutomationCorp/actions?query=workflow%3A%22CodeQL+Security+Scan%22)
[![Security Scanning](https://img.shields.io/badge/security-scanning-green.svg)](https://github.com/WilBtc/InsaAutomationCorp/security)
[![IEC 62443](https://img.shields.io/badge/compliance-IEC%2062443-blue.svg)](./SECURITY.md)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

A comprehensive autonomous platform for industrial automation, CRM, and DevSecOps with AI-powered agents.

## Overview

INSA Automation Corp provides an integrated platform for Oil & Gas and industrial automation companies, combining:
- AI-powered CRM with Bitrix24 integration
- IEC 62443 compliance automation
- Autonomous agent orchestration
- Industrial cybersecurity monitoring
- Multi-platform MCP server architecture

---

## HackyPi Control Script

A comprehensive Python script for managing and interacting with the HackyPi USB device.

## Overview

HackyPi is a compact USB device powered by the RP2040 microcontroller that can simulate keyboard and mouse inputs, display graphics, and perform various automation tasks. This control script provides an easy way to manage your HackyPi device.

## Features

- **Device Detection**: Automatically detect when HackyPi is connected
- **Script Management**: Upload and manage scripts on the device
- **Custom Script Creation**: Generate scripts for keyboard, mouse, display, and automation tasks
- **Backup & Restore**: Backup device contents and restore from backup
- **Library Management**: Automatically copy required libraries to the device

## Prerequisites

- Python 3.6+
- HackyPi device with CircuitPython firmware
- HackyPi-Software repository cloned locally

## Installation

1. Clone the HackyPi-Software repository:
```bash
git clone https://github.com/sbcshop/HackyPi-Software.git
```

2. Make the control script executable:
```bash
chmod +x hackypi_control_script.py
```

## Usage

### Basic Commands

**Detect HackyPi device:**
```bash
python3 hackypi_control_script.py --detect
```

**List available example scripts:**
```bash
python3 hackypi_control_script.py --list-scripts
```

**Upload a script to HackyPi:**
```bash
python3 hackypi_control_script.py --upload path/to/script.py
```

**Create custom scripts:**
```bash
# Create keyboard automation script
python3 hackypi_control_script.py --create keyboard --output my_keyboard_script.py

# Create mouse automation script
python3 hackypi_control_script.py --create mouse --output my_mouse_script.py

# Create display script
python3 hackypi_control_script.py --create display --output my_display_script.py

# Create automation script
python3 hackypi_control_script.py --create automation --output my_automation_script.py
```

**Backup and restore device:**
```bash
# Backup device contents
python3 hackypi_control_script.py --backup

# Restore device from backup
python3 hackypi_control_script.py --restore
```

### Example Workflow

1. **Connect HackyPi device** to your computer via USB
2. **Detect the device:**
   ```bash
   python3 hackypi_control_script.py --detect
   ```
3. **Create a custom script:**
   ```bash
   python3 hackypi_control_script.py --create keyboard --output my_script.py
   ```
4. **Upload the script:**
   ```bash
   python3 hackypi_control_script.py --upload my_script.py
   ```
5. **Disconnect and reconnect** HackyPi to execute the script

## Script Types

### Keyboard Scripts
- Simulate keyboard inputs
- Type text, press keys, key combinations
- Useful for automation and macros

### Mouse Scripts
- Control mouse movement
- Click, drag, scroll
- Random movement patterns

### Display Scripts
- Show text and graphics on HackyPi's display
- Custom messages and animations

### Automation Scripts
- Complex multi-step automation
- Combine keyboard and mouse actions
- System automation tasks

## Device Setup

If your HackyPi doesn't have CircuitPython installed:

1. Press and hold the BOOT button
2. Connect to USB while holding the button
3. Copy `firmware.uf2` from HackyPi-Software to the RPI-RP2 drive
4. Wait for installation to complete

## Important Notes

- Scripts must be saved as `code.py` on the device to run automatically
- Always test scripts in a safe environment first
- Some actions may require administrator privileges
- The device needs to be reconnected after uploading scripts

## Troubleshooting

**Device not detected:**
- Ensure HackyPi is properly connected
- Check if CircuitPython is installed
- Try different USB ports

**Script not running:**
- Verify script is saved as `code.py`
- Check for syntax errors in the script
- Ensure required libraries are copied to device

**Permission errors:**
- Run script with appropriate permissions
- Check USB device permissions

## Security Considerations

- Only use HackyPi on systems you own or have permission to test
- Be aware that some actions may trigger security software
- Use responsibly and ethically

## License

This script is provided as-is for educational and testing purposes.
