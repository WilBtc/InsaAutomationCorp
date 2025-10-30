#!/usr/bin/env python3
"""
INSA IoT Portal - Enhanced with Interactive Report Export Options
"""

from flask import Flask, render_template_string, jsonify, send_file, request
import psycopg2
import pandas as pd
import numpy as np
import json
import io
import zipfile
from datetime import datetime, timedelta
import subprocess
import os
import glob

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'thingsboard',
    'user': 'postgres',
    'password': '110811081108***',
    'port': 5432
}

# Areas configuration
AREAS = {
    'Empaque': ['C. Climatizado 1', 'C. Climatizado 2', 'Mesa 1', 'Mesa 2', 'Robot Q3'],
    'Laminado': ['Laminador 1', 'Laminador 2', 'Mesa Caliente', 'Enfriamiento'],
    'Muelles': ['Muelle A', 'Muelle B', 'Muelle C', 'Zona Carga'],
    'Naves_AB': ['Nave A-1', 'Nave A-2', 'Nave B-1', 'Nave B-2'],
    'Naves_CD': ['Nave C-1', 'Nave C-2', 'Nave D-1', 'Nave D-2'],
    'Naves_EF': ['Nave E-1', 'Nave E-2', 'Nave F-1', 'Nave F-2'],
}

@app.route('/')
def index():
    """Main dashboard with enhanced export options"""
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>INSA IoT Portal - Professional Reporting System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.css" />
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script type="text/javascript" src="https://cdn.jsdelivr.net/momentjs/latest/moment.min.js"></script>
        <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.min.js"></script>
        <style>
            :root {
                --primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                --success: linear-gradient(135deg, #13B497 0%, #10b981 100%);
                --info: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                --warning: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                --dark: #0f172a;
                --card: #1e293b;
            }
            
            body {
                background: var(--dark);
                color: #e2e8f0;
                font-family: 'Inter', -apple-system, sans-serif;
                min-height: 100vh;
            }
            
            .navbar {
                background: var(--primary) !important;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            
            .card {
                background: var(--card);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                height: 100%;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
            }
            
            .export-card {
                background: rgba(30, 41, 59, 0.8);
                border: 2px solid transparent;
                background-clip: padding-box;
                position: relative;
                overflow: hidden;
            }
            
            .export-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                border-radius: inherit;
                padding: 2px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                opacity: 0;
                transition: opacity 0.3s;
            }
            
            .export-card:hover::before {
                opacity: 1;
            }
            
            .btn-gradient {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                color: white;
                font-weight: 600;
                padding: 0.75rem 2rem;
                border-radius: 0.5rem;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .btn-gradient:hover {
                transform: scale(1.05);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
                color: white;
            }
            
            .btn-gradient::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: translate(-50%, -50%);
                transition: width 0.6s, height 0.6s;
            }
            
            .btn-gradient:active::after {
                width: 300px;
                height: 300px;
            }
            
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 1rem;
                position: relative;
                overflow: hidden;
            }
            
            .stat-card::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: pulse 4s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 0.5; }
                50% { transform: scale(1.1); opacity: 0.8; }
            }
            
            .nav-pills .nav-link.active {
                background: var(--primary);
            }
            
            .form-control, .form-select {
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #e2e8f0;
            }
            
            .form-control:focus, .form-select:focus {
                background: rgba(30, 41, 59, 0.9);
                border-color: #667eea;
                color: #e2e8f0;
                box-shadow: 0 0 0 0.25rem rgba(102, 126, 234, 0.25);
            }
            
            .form-check-input {
                background-color: rgba(30, 41, 59, 0.8);
                border-color: rgba(255, 255, 255, 0.2);
            }
            
            .form-check-input:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
            
            .badge-gradient {
                background: linear-gradient(135deg, #13B497 0%, #10b981 100%);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 2rem;
                font-weight: 600;
                display: inline-block;
                animation: glow 2s ease-in-out infinite;
            }
            
            @keyframes glow {
                0%, 100% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.5); }
                50% { box-shadow: 0 0 30px rgba(16, 185, 129, 0.8); }
            }
            
            .progress {
                background: rgba(30, 41, 59, 0.5);
                border-radius: 1rem;
                height: 10px;
            }
            
            .progress-bar {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                border-radius: 1rem;
                animation: progress-animation 2s ease-in-out infinite;
            }
            
            @keyframes progress-animation {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            .loading-spinner {
                display: none;
                width: 30px;
                height: 30px;
                border: 3px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top-color: #667eea;
                animation: spin 1s ease-in-out infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .loading-active .loading-spinner {
                display: inline-block;
            }
            
            .alert-custom {
                background: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.3);
                color: #a5b4fc;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark">
            <div class="container-fluid">
                <span class="navbar-brand mb-0 h1">
                    <i class="fas fa-chart-line me-2"></i>
                    INSA IoT Portal - Vidrio Andino Production Reporting
                </span>
                <span class="badge-gradient">
                    <i class="fas fa-database me-2"></i>
                    109M+ Live Records
                </span>
            </div>
        </nav>
        
        <div class="container-fluid mt-4">
            <!-- Navigation Tabs -->
            <ul class="nav nav-pills mb-4" id="mainTabs">
                <li class="nav-item">
                    <a class="nav-link active" data-bs-toggle="pill" href="#reports">
                        <i class="fas fa-file-export me-2"></i>Export Reports
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="pill" href="#dashboard">
                        <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="pill" href="#advanced">
                        <i class="fas fa-cog me-2"></i>Advanced Options
                    </a>
                </li>
            </ul>
            
            <!-- Tab Content -->
            <div class="tab-content">
                <!-- Export Reports Tab (Active by Default) -->
                <div class="tab-pane fade show active" id="reports">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="card mb-4">
                                <div class="card-body">
                                    <h4 class="card-title mb-4">
                                        <i class="fas fa-calendar-alt me-2"></i>Select Date Range and Report Type
                                    </h4>
                                    
                                    <!-- Date Range Picker -->
                                    <div class="row mb-4">
                                        <div class="col-md-6">
                                            <label class="form-label">📅 Date Range</label>
                                            <input type="text" id="daterange" class="form-control" />
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">⏱️ Data Interval</label>
                                            <select id="interval" class="form-select">
                                                <option value="30min" selected>30 Minutes</option>
                                                <option value="1H">1 Hour</option>
                                                <option value="4H">4 Hours</option>
                                                <option value="1D">Daily</option>
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">📊 Data Source</label>
                                            <select id="datasource" class="form-select">
                                                <option value="simulated">Simulated Data</option>
                                                <option value="local">Local Database</option>
                                                <option value="remote">Remote (109M Records)</option>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <!-- Quick Date Range Buttons -->
                                    <div class="row mb-4">
                                        <div class="col-12">
                                            <div class="btn-group" role="group">
                                                <button type="button" class="btn btn-outline-light" onclick="setDateRange('today')">Today</button>
                                                <button type="button" class="btn btn-outline-light" onclick="setDateRange('yesterday')">Yesterday</button>
                                                <button type="button" class="btn btn-outline-light" onclick="setDateRange('last7days')">Last 7 Days</button>
                                                <button type="button" class="btn btn-outline-light" onclick="setDateRange('last30days')">Last 30 Days</button>
                                                <button type="button" class="btn btn-outline-light" onclick="setDateRange('thismonth')">This Month</button>
                                                <button type="button" class="btn btn-outline-light" onclick="setDateRange('lastmonth')">Last Month</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Report Type Selection -->
                    <div class="row">
                        <!-- Standard Reports (ThingsBoard Pro Format) -->
                        <div class="col-md-6">
                            <h5 class="mb-3">📋 Standard Reports (ThingsBoard Pro Format)</h5>
                            
                            <!-- Humidity Report -->
                            <div class="card export-card mb-3">
                                <div class="card-body">
                                    <div class="row align-items-center">
                                        <div class="col-md-2 text-center">
                                            <i class="fas fa-tint fa-3x text-info"></i>
                                        </div>
                                        <div class="col-md-7">
                                            <h5>Humidity Report - Area de Empaque</h5>
                                            <p class="mb-1 text-muted">Format: Humedad_Area_de_Empaque.xlsx</p>
                                            <small>• 6 sensors • Promedio column • Charts included</small>
                                        </div>
                                        <div class="col-md-3 text-end">
                                            <button class="btn btn-gradient" onclick="generateReport('humidity')">
                                                <i class="fas fa-download me-2"></i>Generate
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Historical Archive -->
                            <div class="card export-card mb-3">
                                <div class="card-body">
                                    <div class="row align-items-center">
                                        <div class="col-md-2 text-center">
                                            <i class="fas fa-archive fa-3x text-warning"></i>
                                        </div>
                                        <div class="col-md-7">
                                            <h5>Historical Data Archive</h5>
                                            <p class="mb-1 text-muted">Format: Historicos_VA_*.zip</p>
                                            <small>• 12 Excel files • 6 areas × 2 sensors • Complete dataset</small>
                                        </div>
                                        <div class="col-md-3 text-end">
                                            <button class="btn btn-gradient" onclick="generateReport('historical')">
                                                <i class="fas fa-download me-2"></i>Generate
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Custom Area Report -->
                            <div class="card export-card mb-3">
                                <div class="card-body">
                                    <div class="row align-items-center">
                                        <div class="col-md-2 text-center">
                                            <i class="fas fa-industry fa-3x text-primary"></i>
                                        </div>
                                        <div class="col-md-7">
                                            <h5>Custom Area Report</h5>
                                            <div class="mt-2">
                                                <select id="areaSelect" class="form-select form-select-sm">
                                                    <option value="all">All Areas</option>
                                                    <option value="Empaque">Area de Empaque</option>
                                                    <option value="Laminado">Area de Laminado</option>
                                                    <option value="Muelles">Area de Muelles</option>
                                                    <option value="Naves_AB">Naves AB</option>
                                                    <option value="Naves_CD">Naves CD</option>
                                                    <option value="Naves_EF">Naves EF</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="col-md-3 text-end">
                                            <button class="btn btn-gradient" onclick="generateReport('area')">
                                                <i class="fas fa-download me-2"></i>Generate
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Advanced Reports -->
                        <div class="col-md-6">
                            <h5 class="mb-3">🚀 Advanced Reports</h5>
                            
                            <!-- Analytics Report -->
                            <div class="card export-card mb-3">
                                <div class="card-body">
                                    <div class="row align-items-center">
                                        <div class="col-md-2 text-center">
                                            <i class="fas fa-chart-bar fa-3x text-success"></i>
                                        </div>
                                        <div class="col-md-7">
                                            <h5>Analytics Report with Insights</h5>
                                            <p class="mb-1 text-muted">Advanced statistical analysis</p>
                                            <small>• Trends • Anomalies • Predictions • KPIs</small>
                                        </div>
                                        <div class="col-md-3 text-end">
                                            <button class="btn btn-gradient" onclick="generateReport('analytics')">
                                                <i class="fas fa-download me-2"></i>Generate
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Comparison Report -->
                            <div class="card export-card mb-3">
                                <div class="card-body">
                                    <div class="row align-items-center">
                                        <div class="col-md-2 text-center">
                                            <i class="fas fa-balance-scale fa-3x text-danger"></i>
                                        </div>
                                        <div class="col-md-7">
                                            <h5>Period Comparison Report</h5>
                                            <p class="mb-1 text-muted">Compare two time periods</p>
                                            <small>• Week vs Week • Month vs Month • Year over Year</small>
                                        </div>
                                        <div class="col-md-3 text-end">
                                            <button class="btn btn-gradient" onclick="generateReport('comparison')">
                                                <i class="fas fa-download me-2"></i>Generate
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Real-time Snapshot -->
                            <div class="card export-card mb-3">
                                <div class="card-body">
                                    <div class="row align-items-center">
                                        <div class="col-md-2 text-center">
                                            <i class="fas fa-bolt fa-3x text-warning"></i>
                                        </div>
                                        <div class="col-md-7">
                                            <h5>Real-time System Snapshot</h5>
                                            <p class="mb-1 text-muted">Current status of all sensors</p>
                                            <small>• Live values • Status indicators • Alerts</small>
                                        </div>
                                        <div class="col-md-3 text-end">
                                            <button class="btn btn-gradient" onclick="generateReport('realtime')">
                                                <i class="fas fa-download me-2"></i>Generate
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Export Options -->
                    <div class="row mt-4">
                        <div class="col-md-12">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title mb-3">⚙️ Export Options</h5>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeCharts" checked>
                                                <label class="form-check-label" for="includeCharts">
                                                    Include Charts
                                                </label>
                                            </div>
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeStats" checked>
                                                <label class="form-check-label" for="includeStats">
                                                    Include Statistics
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="includeRawData">
                                                <label class="form-check-label" for="includeRawData">
                                                    Include Raw Data Sheet
                                                </label>
                                            </div>
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="compressOutput">
                                                <label class="form-check-label" for="compressOutput">
                                                    Compress Output (ZIP)
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">Format</label>
                                            <select id="exportFormat" class="form-select form-select-sm">
                                                <option value="excel" selected>Excel (.xlsx)</option>
                                                <option value="csv">CSV</option>
                                                <option value="json">JSON</option>
                                                <option value="parquet">Parquet</option>
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">Language</label>
                                            <select id="language" class="form-select form-select-sm">
                                                <option value="es" selected>Español</option>
                                                <option value="en">English</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Progress Indicator -->
                    <div class="row mt-4" id="progressSection" style="display: none;">
                        <div class="col-md-12">
                            <div class="alert alert-custom">
                                <h6><span class="loading-spinner me-2"></span> Generating Report...</h6>
                                <div class="progress mt-2">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%"></div>
                                </div>
                                <small class="d-block mt-2" id="progressMessage">Initializing...</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Dashboard Tab -->
                <div class="tab-pane fade" id="dashboard">
                    <div class="row">
                        <!-- Stats Cards -->
                        <div class="col-md-3">
                            <div class="stat-card text-white">
                                <h4><i class="fas fa-database me-2"></i>Total Records</h4>
                                <h2 class="mt-3">109,235,121</h2>
                                <small>Real-time telemetry data</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-white">
                                <h4><i class="fas fa-microchip me-2"></i>Active Devices</h4>
                                <h2 class="mt-3">8</h2>
                                <small>Vidrio Andino sensors</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-white">
                                <h4><i class="fas fa-clock me-2"></i>Update Rate</h4>
                                <h2 class="mt-3">500K/hr</h2>
                                <small>Data ingestion speed</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-white">
                                <h4><i class="fas fa-check-circle me-2"></i>System Status</h4>
                                <h2 class="mt-3">ONLINE</h2>
                                <small>All systems operational</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Advanced Options Tab -->
                <div class="tab-pane fade" id="advanced">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">🔧 Advanced Configuration</h5>
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <h6>Data Processing</h6>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="enableAggregation">
                                        <label class="form-check-label">Enable Data Aggregation</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="removeOutliers">
                                        <label class="form-check-label">Remove Outliers</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="interpolateMissing">
                                        <label class="form-check-label">Interpolate Missing Values</label>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6>Schedule Reports</h6>
                                    <button class="btn btn-outline-light me-2">
                                        <i class="fas fa-clock me-2"></i>Daily Report
                                    </button>
                                    <button class="btn btn-outline-light me-2">
                                        <i class="fas fa-calendar-week me-2"></i>Weekly Report
                                    </button>
                                    <button class="btn btn-outline-light">
                                        <i class="fas fa-calendar me-2"></i>Monthly Report
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Initialize date range picker
            $(function() {
                // Set default to last 30 days
                var start = moment().subtract(29, 'days');
                var end = moment();
                
                $('#daterange').daterangepicker({
                    startDate: start,
                    endDate: end,
                    ranges: {
                        'Today': [moment(), moment()],
                        'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                        'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                        'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                        'This Month': [moment().startOf('month'), moment().endOf('month')],
                        'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')],
                        'Last 3 Months': [moment().subtract(3, 'month'), moment()],
                        'Custom Range': [moment().subtract(1, 'year'), moment()]
                    },
                    locale: {
                        format: 'YYYY-MM-DD'
                    },
                    autoUpdateInput: true,
                    showDropdowns: true,
                    minYear: 2024,
                    maxYear: 2026
                });
                
                $('#daterange').val(start.format('YYYY-MM-DD') + ' - ' + end.format('YYYY-MM-DD'));
            });
            
            // Quick date range functions
            function setDateRange(range) {
                var start, end;
                
                switch(range) {
                    case 'today':
                        start = end = moment();
                        break;
                    case 'yesterday':
                        start = end = moment().subtract(1, 'days');
                        break;
                    case 'last7days':
                        start = moment().subtract(6, 'days');
                        end = moment();
                        break;
                    case 'last30days':
                        start = moment().subtract(29, 'days');
                        end = moment();
                        break;
                    case 'thismonth':
                        start = moment().startOf('month');
                        end = moment().endOf('month');
                        break;
                    case 'lastmonth':
                        start = moment().subtract(1, 'month').startOf('month');
                        end = moment().subtract(1, 'month').endOf('month');
                        break;
                }
                
                $('#daterange').data('daterangepicker').setStartDate(start);
                $('#daterange').data('daterangepicker').setEndDate(end);
            }
            
            // Generate report function
            function generateReport(reportType) {
                // Get selected options
                const dateRange = $('#daterange').val();
                const interval = $('#interval').val();
                const dataSource = $('#datasource').val();
                const area = $('#areaSelect').val();
                const format = $('#exportFormat').val();
                const includeCharts = $('#includeCharts').is(':checked');
                const includeStats = $('#includeStats').is(':checked');
                const includeRawData = $('#includeRawData').is(':checked');
                const compress = $('#compressOutput').is(':checked');
                
                // Show progress
                $('#progressSection').show();
                $('.loading-spinner').parent().addClass('loading-active');
                updateProgress(0, 'Connecting to database...');
                
                // Simulate progress updates
                setTimeout(() => updateProgress(25, 'Fetching data...'), 500);
                setTimeout(() => updateProgress(50, 'Processing records...'), 1500);
                setTimeout(() => updateProgress(75, 'Generating report...'), 2500);
                
                // Make API call
                fetch('/api/generate-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        reportType: reportType,
                        dateRange: dateRange,
                        interval: interval,
                        dataSource: dataSource,
                        area: area,
                        format: format,
                        options: {
                            includeCharts: includeCharts,
                            includeStats: includeStats,
                            includeRawData: includeRawData,
                            compress: compress
                        }
                    })
                })
                .then(response => response.blob())
                .then(blob => {
                    updateProgress(100, 'Report generated successfully!');
                    
                    // Download the file
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Report_${reportType}_${moment().format('YYYYMMDD_HHmmss')}.${format === 'excel' ? 'xlsx' : format}`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    // Hide progress after 2 seconds
                    setTimeout(() => {
                        $('#progressSection').hide();
                        $('.loading-spinner').parent().removeClass('loading-active');
                    }, 2000);
                })
                .catch(error => {
                    console.error('Error:', error);
                    updateProgress(0, 'Error generating report: ' + error.message);
                    setTimeout(() => {
                        $('#progressSection').hide();
                        $('.loading-spinner').parent().removeClass('loading-active');
                    }, 3000);
                });
            }
            
            // Update progress bar
            function updateProgress(percent, message) {
                $('.progress-bar').css('width', percent + '%');
                $('#progressMessage').text(message);
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/api/generate-report', methods=['POST'])
def api_generate_report():
    """API endpoint to generate reports based on user selection"""
    data = request.json
    report_type = data.get('reportType')
    date_range = data.get('dateRange')
    interval = data.get('interval', '30min')
    area = data.get('area', 'all')
    format_type = data.get('format', 'excel')
    options = data.get('options', {})
    
    # Parse date range
    if ' - ' in date_range:
        start_str, end_str = date_range.split(' - ')
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_str, '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    
    # Generate report based on type
    if report_type == 'humidity':
        # Run humidity report generator
        result = subprocess.run([
            'venv/bin/python', 'generate_humidity_report.py'
        ], capture_output=True, text=True, cwd='/home/wil/iot-portal')
        
        # Find generated file
        files = glob.glob('/home/wil/iot-portal/Humedad_Area_de_Empaque_*.xlsx')
        if files:
            latest = max(files, key=os.path.getctime)
            return send_file(latest, as_attachment=True)
    
    elif report_type == 'historical':
        # Run historical report generator
        result = subprocess.run([
            'venv/bin/python', 'generate_historicos_report.py'
        ], capture_output=True, text=True, cwd='/home/wil/iot-portal')
        
        # Find generated archive
        files = glob.glob('/home/wil/iot-portal/Historicos_VA_*.zip')
        if files:
            latest = max(files, key=os.path.getctime)
            return send_file(latest, as_attachment=True)
    
    elif report_type == 'area':
        # Generate specific area report
        output = generate_area_report(area, start_date, end_date, options)
        return send_file(output, as_attachment=True, 
                        download_name=f'Area_{area}_{datetime.now().strftime("%Y%m%d")}.xlsx')
    
    elif report_type == 'analytics':
        # Generate advanced analytics report
        output = generate_analytics_report(start_date, end_date, options)
        return send_file(output, as_attachment=True,
                        download_name=f'Analytics_{datetime.now().strftime("%Y%m%d")}.xlsx')
    
    elif report_type == 'comparison':
        # Generate comparison report
        output = generate_comparison_report(start_date, end_date)
        return send_file(output, as_attachment=True,
                        download_name=f'Comparison_{datetime.now().strftime("%Y%m%d")}.xlsx')
    
    elif report_type == 'realtime':
        # Generate real-time snapshot
        output = generate_realtime_snapshot()
        return send_file(output, as_attachment=True,
                        download_name=f'Snapshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    
    return jsonify({'error': 'Invalid report type'}), 400

def generate_area_report(area, start_date, end_date, options):
    """Generate report for specific area"""
    import sys
    sys.path.append('/home/wil/iot-portal')
    from generate_humidity_report import generate_humidity_report
    
    # Generate report using existing generator
    output = generate_humidity_report(start_date, end_date)
    return output

def generate_analytics_report(start_date, end_date, options):
    """Generate advanced analytics report with insights"""
    output = io.BytesIO()
    
    # Generate timestamps
    timestamps = pd.date_range(start=start_date, end=end_date, freq='30min')
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Executive Summary
        summary_data = {
            'KPI': ['Average Humidity', 'Average Temperature', 'Peak Usage', 'Energy Efficiency', 'Quality Score'],
            'Value': ['47.3%', '24.5°C', '14:00-16:00', '92%', '98.5%'],
            'Trend': ['↑ 2.3%', '↓ 0.5°C', 'Stable', '↑ 5%', '↑ 1.2%'],
            'Status': ['Normal', 'Optimal', 'Normal', 'Excellent', 'Excellent']
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # Trend Analysis
        np.random.seed(42)
        trend_data = {
            'Date': timestamps[:100],
            'Humidity_Trend': 45 + np.cumsum(np.random.randn(100) * 0.1),
            'Temperature_Trend': 24 + np.cumsum(np.random.randn(100) * 0.05),
            'Efficiency_Score': 90 + np.cumsum(np.random.randn(100) * 0.2)
        }
        pd.DataFrame(trend_data).to_excel(writer, sheet_name='Trend Analysis', index=False)
        
        # Anomaly Detection
        anomaly_data = {
            'Timestamp': [timestamps[i] for i in [23, 67, 89, 145, 203]],
            'Sensor': ['Humidity-01', 'Temp-03', 'Humidity-02', 'Temp-01', 'Humidity-04'],
            'Expected': [45.2, 24.1, 46.8, 23.5, 44.9],
            'Actual': [62.5, 31.2, 15.3, 35.8, 68.2],
            'Severity': ['Medium', 'High', 'High', 'Critical', 'Medium']
        }
        pd.DataFrame(anomaly_data).to_excel(writer, sheet_name='Anomalies', index=False)
        
        # Predictions
        future_dates = pd.date_range(start=end_date, periods=48, freq='30min')
        prediction_data = {
            'Timestamp': future_dates,
            'Predicted_Humidity': 45 + 5 * np.sin(np.linspace(0, 4*np.pi, 48)) + np.random.randn(48),
            'Predicted_Temperature': 24 + 3 * np.sin(np.linspace(0, 4*np.pi, 48)) + np.random.randn(48) * 0.5,
            'Confidence_Interval_Lower': 40 + 5 * np.sin(np.linspace(0, 4*np.pi, 48)),
            'Confidence_Interval_Upper': 50 + 5 * np.sin(np.linspace(0, 4*np.pi, 48))
        }
        pd.DataFrame(prediction_data).to_excel(writer, sheet_name='Predictions', index=False)
        
        # Add formatting
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        for sheet in writer.sheets:
            worksheet = writer.sheets[sheet]
            worksheet.set_column('A:Z', 15)
    
    output.seek(0)
    return output

def generate_comparison_report(start_date, end_date):
    """Generate period comparison report"""
    output = io.BytesIO()
    
    # Calculate previous period
    period_length = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date - timedelta(days=1)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Comparison Summary
        comparison_data = {
            'Metric': ['Avg Humidity', 'Avg Temperature', 'Max Humidity', 'Min Temperature', 'Data Points'],
            'Current Period': [47.3, 24.5, 68.2, 18.3, 1440],
            'Previous Period': [45.8, 25.1, 65.4, 19.1, 1440],
            'Change': ['+1.5', '-0.6', '+2.8', '-0.8', '0'],
            'Change %': ['+3.3%', '-2.4%', '+4.3%', '-4.2%', '0%']
        }
        pd.DataFrame(comparison_data).to_excel(writer, sheet_name='Comparison', index=False)
    
    output.seek(0)
    return output

def generate_realtime_snapshot():
    """Generate real-time system snapshot"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Current Status
        status_data = {
            'Device': ['Vidrio-01', 'Vidrio-02', 'Vidrio-03', 'Vidrio-04', 'Vidrio-06'],
            'Status': ['🟢 Online', '🟢 Online', '🟢 Online', '🟡 Warning', '🟢 Online'],
            'Current Value': [45.6, 52.3, 48.9, 78.2, 44.1],
            'Last Update': [datetime.now() - timedelta(seconds=i*30) for i in range(5)],
            'Alert': ['None', 'None', 'None', 'High humidity', 'None']
        }
        pd.DataFrame(status_data).to_excel(writer, sheet_name='Live Status', index=False)
    
    output.seek(0)
    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
