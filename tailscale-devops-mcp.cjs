#!/usr/bin/env node

/**
 * Tailscale DevOps MCP Server
 * Provides comprehensive Tailscale network management and DevOps automation
 * Integrates with INSA infrastructure for secure network operations
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const os = require('os');

const execAsync = promisify(exec);

class TailscaleDevOpsMCP {
  constructor() {
    this.server = new Server({
      name: 'tailscale-devops',
      version: '1.0.0',
      description: 'Tailscale DevOps automation and network management for INSA infrastructure'
    }, {
      capabilities: {
        tools: {},
        resources: {}
      }
    });

    // INSA Infrastructure mapping (from your CLAUDE.md)
    this.infrastructure = {
      workstation: {
        hostname: 'lu1',
        ip: '100.81.103.99',
        role: 'development',
        services: ['syncthing', 'grafana', 'prometheus', 'timescaledb'],
        capabilities: ['docker', 'development', 'analytics']
      },
      erp_server: {
        hostname: 'insa-automation-erp',
        ip: '100.105.64.109',
        role: 'production',
        services: ['thingsboard', 'postgresql', 'pgadmin', 'iot-portal'],
        capabilities: ['database', 'iot', 'web_services']
      },
      current_host: {
        hostname: 'iac1',
        ip: '100.100.101.1',
        role: 'compute',
        services: ['tailscale', 'docker'],
        capabilities: ['compute', 'orchestration']
      },
      edge_node: {
        hostname: 'netg',
        ip: '100.121.213.50',
        role: 'edge',
        services: ['wazuh-manager'],
        capabilities: ['monitoring', 'security', 'exit_node']
      }
    };

    this.setupHandlers();
  }

  setupHandlers() {
    // Tool handlers
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'network_status',
          description: 'Get comprehensive Tailscale network status and topology',
          inputSchema: {
            type: 'object',
            properties: {
              include_metrics: {
                type: 'boolean',
                default: true,
                description: 'Include traffic and performance metrics'
              },
              include_routes: {
                type: 'boolean',
                default: true,
                description: 'Include subnet routes and exit nodes'
              }
            }
          }
        },
        {
          name: 'ssh_management',
          description: 'Manage SSH connections and keys across Tailscale network',
          inputSchema: {
            type: 'object',
            properties: {
              action: {
                type: 'string',
                enum: ['enable', 'disable', 'status', 'rotate_keys', 'list_sessions'],
                description: 'SSH management action'
              },
              target_host: {
                type: 'string',
                description: 'Target hostname (optional, defaults to all)'
              },
              user: {
                type: 'string',
                description: 'Username for SSH operations'
              }
            },
            required: ['action']
          }
        },
        {
          name: 'secure_tunnel',
          description: 'Create secure tunnels between services across the network',
          inputSchema: {
            type: 'object',
            properties: {
              action: {
                type: 'string',
                enum: ['create', 'list', 'remove'],
                description: 'Tunnel action'
              },
              source_host: {
                type: 'string',
                description: 'Source hostname'
              },
              target_host: {
                type: 'string',
                description: 'Target hostname'
              },
              source_port: {
                type: 'number',
                description: 'Source port'
              },
              target_port: {
                type: 'number',
                description: 'Target port'
              },
              protocol: {
                type: 'string',
                enum: ['tcp', 'udp'],
                default: 'tcp'
              }
            },
            required: ['action']
          }
        },
        {
          name: 'subnet_routing',
          description: 'Configure subnet routes and exit nodes',
          inputSchema: {
            type: 'object',
            properties: {
              action: {
                type: 'string',
                enum: ['advertise', 'accept', 'list', 'remove'],
                description: 'Routing action'
              },
              subnet: {
                type: 'string',
                description: 'Subnet CIDR (e.g., 192.168.1.0/24)'
              },
              exit_node: {
                type: 'boolean',
                default: false,
                description: 'Enable as exit node'
              },
              host: {
                type: 'string',
                description: 'Target host for route advertisement'
              }
            },
            required: ['action']
          }
        },
        {
          name: 'access_control',
          description: 'Manage network access control and policies',
          inputSchema: {
            type: 'object',
            properties: {
              action: {
                type: 'string',
                enum: ['list_policies', 'create_policy', 'test_access', 'block_host', 'unblock_host'],
                description: 'Access control action'
              },
              policy_name: {
                type: 'string',
                description: 'Name for the policy'
              },
              source: {
                type: 'string',
                description: 'Source host or tag'
              },
              destination: {
                type: 'string',
                description: 'Destination host or service'
              },
              ports: {
                type: 'array',
                items: { type: 'number' },
                description: 'Allowed ports'
              },
              protocol: {
                type: 'string',
                enum: ['tcp', 'udp', 'icmp', 'any'],
                default: 'tcp'
              }
            },
            required: ['action']
          }
        },
        {
          name: 'service_discovery',
          description: 'Discover and catalog services across the Tailscale network',
          inputSchema: {
            type: 'object',
            properties: {
              scan_type: {
                type: 'string',
                enum: ['quick', 'full', 'service_specific'],
                default: 'quick',
                description: 'Type of network scan'
              },
              target_host: {
                type: 'string',
                description: 'Specific host to scan (optional)'
              },
              service_type: {
                type: 'string',
                enum: ['web', 'database', 'api', 'ssh', 'all'],
                default: 'all',
                description: 'Type of services to discover'
              }
            }
          }
        },
        {
          name: 'traffic_analysis',
          description: 'Analyze network traffic patterns and performance',
          inputSchema: {
            type: 'object',
            properties: {
              duration: {
                type: 'number',
                default: 60,
                description: 'Analysis duration in seconds'
              },
              host_filter: {
                type: 'string',
                description: 'Filter by specific host'
              },
              include_flows: {
                type: 'boolean',
                default: false,
                description: 'Include detailed traffic flows'
              }
            }
          }
        },
        {
          name: 'infrastructure_health',
          description: 'Check health and connectivity of INSA infrastructure',
          inputSchema: {
            type: 'object',
            properties: {
              check_services: {
                type: 'boolean',
                default: true,
                description: 'Check service availability'
              },
              check_performance: {
                type: 'boolean',
                default: true,
                description: 'Include performance metrics'
              },
              detailed_report: {
                type: 'boolean',
                default: false,
                description: 'Generate detailed health report'
              }
            }
          }
        },
        {
          name: 'automated_deployment',
          description: 'Deploy services across Tailscale network with DevOps automation',
          inputSchema: {
            type: 'object',
            properties: {
              deployment_type: {
                type: 'string',
                enum: ['docker', 'kubernetes', 'systemd', 'script'],
                description: 'Type of deployment'
              },
              service_name: {
                type: 'string',
                description: 'Name of the service to deploy'
              },
              target_hosts: {
                type: 'array',
                items: { type: 'string' },
                description: 'Target hosts for deployment'
              },
              image_or_script: {
                type: 'string',
                description: 'Docker image, script path, or service definition'
              },
              environment: {
                type: 'object',
                description: 'Environment variables'
              },
              ports: {
                type: 'array',
                items: { type: 'number' },
                description: 'Ports to expose'
              }
            },
            required: ['deployment_type', 'service_name', 'target_hosts']
          }
        },
        {
          name: 'network_optimization',
          description: 'Optimize network paths and performance',
          inputSchema: {
            type: 'object',
            properties: {
              optimization_type: {
                type: 'string',
                enum: ['latency', 'bandwidth', 'reliability', 'cost'],
                default: 'latency',
                description: 'Type of optimization'
              },
              source_host: {
                type: 'string',
                description: 'Source host for optimization'
              },
              target_host: {
                type: 'string',
                description: 'Target host for optimization'
              }
            }
          }
        }
      ]
    }));

    // Resource handlers
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: 'tailscale://network/status',
          name: 'Network Status',
          mimeType: 'application/json',
          description: 'Real-time Tailscale network status'
        },
        {
          uri: 'tailscale://infrastructure/map',
          name: 'INSA Infrastructure Map',
          mimeType: 'application/json',
          description: 'Complete INSA infrastructure mapping'
        },
        {
          uri: 'tailscale://security/policies',
          name: 'Security Policies',
          mimeType: 'application/json',
          description: 'Active security policies and ACLs'
        },
        {
          uri: 'tailscale://services/catalog',
          name: 'Service Catalog',
          mimeType: 'application/json',
          description: 'Discovered services across the network'
        }
      ]
    }));

    // Tool execution handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch(name) {
          case 'network_status':
            return await this.getNetworkStatus(args);
          case 'ssh_management':
            return await this.manageSSH(args);
          case 'secure_tunnel':
            return await this.manageTunnels(args);
          case 'subnet_routing':
            return await this.manageSubnetRouting(args);
          case 'access_control':
            return await this.manageAccessControl(args);
          case 'service_discovery':
            return await this.discoverServices(args);
          case 'traffic_analysis':
            return await this.analyzeTraffic(args);
          case 'infrastructure_health':
            return await this.checkInfrastructureHealth(args);
          case 'automated_deployment':
            return await this.automatedDeployment(args);
          case 'network_optimization':
            return await this.optimizeNetwork(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error.message}`
          }]
        };
      }
    });

    // Resource read handler
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      try {
        switch(uri) {
          case 'tailscale://network/status':
            return await this.getNetworkResource();
          case 'tailscale://infrastructure/map':
            return await this.getInfrastructureResource();
          case 'tailscale://security/policies':
            return await this.getSecurityResource();
          case 'tailscale://services/catalog':
            return await this.getServicesResource();
          default:
            throw new Error(`Unknown resource: ${uri}`);
        }
      } catch (error) {
        return {
          contents: [{
            uri,
            mimeType: 'text/plain',
            text: `Error: ${error.message}`
          }]
        };
      }
    });
  }

  // Tool implementations
  async getNetworkStatus({ include_metrics = true, include_routes = true }) {
    const status = {};

    // Get basic Tailscale status
    const { stdout: statusOutput } = await execAsync('tailscale status');
    status.peers = this.parseTailscaleStatus(statusOutput);

    // Get current node info
    const { stdout: ipOutput } = await execAsync('tailscale ip -4');
    status.current_node = {
      ip: ipOutput.trim(),
      hostname: os.hostname()
    };

    // Get routes if requested
    if (include_routes) {
      try {
        const { stdout: routeOutput } = await execAsync('tailscale status --peers=false');
        status.routes = this.parseRoutes(routeOutput);
      } catch (error) {
        status.routes = { error: error.message };
      }
    }

    // Get metrics if requested
    if (include_metrics) {
      status.metrics = await this.collectNetworkMetrics();
    }

    // Add INSA infrastructure context
    status.infrastructure_status = await this.checkInfrastructureConnectivity();

    return {
      content: [{
        type: 'text',
        text: `Tailscale Network Status:\n${JSON.stringify(status, null, 2)}`
      }]
    };
  }

  async manageSSH({ action, target_host, user = 'wil' }) {
    let result = '';

    switch(action) {
      case 'enable':
        const { stdout: enableOutput } = await execAsync('tailscale up --ssh');
        result = `SSH enabled on Tailscale network\n${enableOutput}`;
        break;

      case 'disable':
        const { stdout: disableOutput } = await execAsync('tailscale up --ssh=false');
        result = `SSH disabled on Tailscale network\n${disableOutput}`;
        break;

      case 'status':
        const { stdout: statusOutput } = await execAsync('tailscale status | grep -E "ssh|SSH" || echo "SSH status: Not enabled"');
        result = `SSH Status:\n${statusOutput}`;
        break;

      case 'list_sessions':
        try {
          const { stdout: sessionsOutput } = await execAsync('ss -tuln | grep :22');
          result = `Active SSH connections:\n${sessionsOutput}`;
        } catch (error) {
          result = 'No active SSH sessions found';
        }
        break;

      case 'rotate_keys':
        // Generate new SSH keys
        const keyPath = path.join(os.homedir(), '.ssh', 'tailscale_key');
        await execAsync(`ssh-keygen -t ed25519 -f ${keyPath} -N "" -C "tailscale-${Date.now()}"`);
        result = `New SSH key generated: ${keyPath}`;
        break;
    }

    return {
      content: [{
        type: 'text',
        text: result
      }]
    };
  }

  async manageTunnels({ action, source_host, target_host, source_port, target_port, protocol = 'tcp' }) {
    let result = '';

    switch(action) {
      case 'create':
        if (!source_host || !target_host || !source_port || !target_port) {
          throw new Error('Source host, target host, source port, and target port are required for tunnel creation');
        }

        // Use SSH port forwarding over Tailscale
        const tunnelCmd = `ssh -f -N -L ${source_port}:${target_host}:${target_port} ${source_host}`;
        await execAsync(tunnelCmd);
        result = `Secure tunnel created: ${source_host}:${source_port} -> ${target_host}:${target_port}`;
        break;

      case 'list':
        const { stdout: processOutput } = await execAsync('ps aux | grep "ssh.*-L" | grep -v grep || echo "No active tunnels"');
        result = `Active tunnels:\n${processOutput}`;
        break;

      case 'remove':
        const { stdout: killOutput } = await execAsync('pkill -f "ssh.*-L" || echo "No tunnels to remove"');
        result = `Tunnels removed:\n${killOutput}`;
        break;
    }

    return {
      content: [{
        type: 'text',
        text: result
      }]
    };
  }

  async manageSubnetRouting({ action, subnet, exit_node = false, host }) {
    let result = '';

    switch(action) {
      case 'advertise':
        if (exit_node) {
          const { stdout: exitOutput } = await execAsync('tailscale up --advertise-exit-node');
          result = `Exit node advertising enabled\n${exitOutput}`;
        } else if (subnet) {
          const { stdout: subnetOutput } = await execAsync(`tailscale up --advertise-routes=${subnet}`);
          result = `Subnet route advertised: ${subnet}\n${subnetOutput}`;
        }
        break;

      case 'accept':
        const { stdout: acceptOutput } = await execAsync('tailscale up --accept-routes');
        result = `Route acceptance enabled\n${acceptOutput}`;
        break;

      case 'list':
        const { stdout: statusOutput } = await execAsync('tailscale status');
        const routes = this.parseRoutes(statusOutput);
        result = `Current routes:\n${JSON.stringify(routes, null, 2)}`;
        break;

      case 'remove':
        const { stdout: removeOutput } = await execAsync('tailscale up --advertise-routes="" --advertise-exit-node=false');
        result = `Route advertisements removed\n${removeOutput}`;
        break;
    }

    return {
      content: [{
        type: 'text',
        text: result
      }]
    };
  }

  async manageAccessControl({ action, policy_name, source, destination, ports = [], protocol = 'tcp' }) {
    let result = '';

    // Note: Full ACL management requires admin access to Tailscale admin console
    // These are local firewall and connection management operations

    switch(action) {
      case 'list_policies':
        const { stdout: firewallOutput } = await execAsync('iptables -L INPUT -n --line-numbers | grep tailscale || echo "No Tailscale-specific rules found"');
        result = `Local firewall policies:\n${firewallOutput}`;
        break;

      case 'test_access':
        if (!destination) {
          throw new Error('Destination is required for access testing');
        }

        const testPort = ports.length > 0 ? ports[0] : 22;
        try {
          const { stdout: testOutput } = await execAsync(`nc -zv ${destination} ${testPort}`, { timeout: 5000 });
          result = `Access test PASSED: ${destination}:${testPort}\n${testOutput}`;
        } catch (error) {
          result = `Access test FAILED: ${destination}:${testPort}\n${error.message}`;
        }
        break;

      case 'block_host':
        if (!source) {
          throw new Error('Source host is required for blocking');
        }
        const blockCmd = `iptables -I INPUT -s ${source} -j DROP`;
        await execAsync(blockCmd);
        result = `Host blocked: ${source}`;
        break;

      case 'unblock_host':
        if (!source) {
          throw new Error('Source host is required for unblocking');
        }
        const unblockCmd = `iptables -D INPUT -s ${source} -j DROP`;
        await execAsync(unblockCmd);
        result = `Host unblocked: ${source}`;
        break;
    }

    return {
      content: [{
        type: 'text',
        text: result
      }]
    };
  }

  async discoverServices({ scan_type = 'quick', target_host, service_type = 'all' }) {
    const services = {};

    if (target_host) {
      // Scan specific host
      services[target_host] = await this.scanHost(target_host, service_type, scan_type === 'full');
    } else {
      // Scan all infrastructure hosts
      for (const [key, host] of Object.entries(this.infrastructure)) {
        try {
          services[host.hostname] = await this.scanHost(host.ip, service_type, scan_type === 'full');
        } catch (error) {
          services[host.hostname] = { error: error.message };
        }
      }
    }

    return {
      content: [{
        type: 'text',
        text: `Service Discovery Results:\n${JSON.stringify(services, null, 2)}`
      }]
    };
  }

  async analyzeTraffic({ duration = 60, host_filter, include_flows = false }) {
    const analysis = {
      duration: `${duration}s`,
      timestamp: new Date().toISOString(),
      traffic_summary: {}
    };

    try {
      // Use netstat/ss to analyze connections
      const { stdout: connectionOutput } = await execAsync('ss -tuln');
      analysis.active_connections = this.parseConnections(connectionOutput);

      // Monitor interface statistics
      const { stdout: interfaceOutput } = await execAsync('cat /proc/net/dev | grep tailscale');
      if (interfaceOutput) {
        analysis.interface_stats = this.parseInterfaceStats(interfaceOutput);
      }

      // Get bandwidth usage if available
      try {
        const { stdout: bandwidthOutput } = await execAsync('vnstat -i tailscale0 --json || echo "vnstat not available"');
        if (bandwidthOutput !== 'vnstat not available') {
          analysis.bandwidth = JSON.parse(bandwidthOutput);
        }
      } catch (error) {
        analysis.bandwidth = { error: 'vnstat not available' };
      }

    } catch (error) {
      analysis.error = error.message;
    }

    return {
      content: [{
        type: 'text',
        text: `Traffic Analysis:\n${JSON.stringify(analysis, null, 2)}`
      }]
    };
  }

  async checkInfrastructureHealth({ check_services = true, check_performance = true, detailed_report = false }) {
    const health = {
      timestamp: new Date().toISOString(),
      overall_status: 'healthy',
      nodes: {},
      services: {},
      connectivity: {}
    };

    for (const [key, node] of Object.entries(this.infrastructure)) {
      health.nodes[key] = await this.checkNodeHealth(node, check_services, check_performance);

      // Test connectivity
      health.connectivity[key] = await this.testConnectivity(node.ip);
    }

    // Determine overall status
    const nodeStatuses = Object.values(health.nodes).map(n => n.status);
    if (nodeStatuses.some(s => s === 'critical')) {
      health.overall_status = 'critical';
    } else if (nodeStatuses.some(s => s === 'warning')) {
      health.overall_status = 'warning';
    }

    if (detailed_report) {
      health.detailed_metrics = await this.gatherDetailedMetrics();
    }

    return {
      content: [{
        type: 'text',
        text: `Infrastructure Health Report:\n${JSON.stringify(health, null, 2)}`
      }]
    };
  }

  async automatedDeployment({ deployment_type, service_name, target_hosts, image_or_script, environment = {}, ports = [] }) {
    const deploymentResults = {};

    for (const host of target_hosts) {
      try {
        let result = '';

        switch(deployment_type) {
          case 'docker':
            const portMappings = ports.map(p => `-p ${p}:${p}`).join(' ');
            const envVars = Object.entries(environment).map(([k, v]) => `-e ${k}=${v}`).join(' ');
            const dockerCmd = `docker run -d --name ${service_name} ${portMappings} ${envVars} ${image_or_script}`;

            // Execute on target host via SSH
            result = await this.executeOnHost(host, dockerCmd);
            break;

          case 'systemd':
            // Create systemd service file and start service
            const serviceContent = this.generateSystemdService(service_name, image_or_script, environment);
            result = await this.deploySystemdService(host, service_name, serviceContent);
            break;

          case 'script':
            // Execute script on target host
            result = await this.executeOnHost(host, image_or_script);
            break;
        }

        deploymentResults[host] = {
          status: 'success',
          result: result
        };

      } catch (error) {
        deploymentResults[host] = {
          status: 'failed',
          error: error.message
        };
      }
    }

    return {
      content: [{
        type: 'text',
        text: `Deployment Results:\n${JSON.stringify(deploymentResults, null, 2)}`
      }]
    };
  }

  async optimizeNetwork({ optimization_type = 'latency', source_host, target_host }) {
    const optimization = {
      type: optimization_type,
      timestamp: new Date().toISOString(),
      recommendations: [],
      metrics: {}
    };

    // Test current performance
    if (source_host && target_host) {
      optimization.metrics = await this.measureNetworkPerformance(source_host, target_host);
    }

    // Generate recommendations based on optimization type
    switch(optimization_type) {
      case 'latency':
        optimization.recommendations = [
          'Consider using direct connections instead of relay',
          'Enable MagicDNS for faster name resolution',
          'Optimize subnet routing paths'
        ];
        break;

      case 'bandwidth':
        optimization.recommendations = [
          'Enable compression for large data transfers',
          'Use load balancing across multiple paths',
          'Configure QoS policies for critical traffic'
        ];
        break;

      case 'reliability':
        optimization.recommendations = [
          'Configure multiple exit nodes for redundancy',
          'Enable automatic failover mechanisms',
          'Monitor link quality and switch paths proactively'
        ];
        break;

      case 'cost':
        optimization.recommendations = [
          'Prefer direct connections over relay to reduce bandwidth costs',
          'Consolidate traffic through fewer exit nodes',
          'Optimize subnet advertisement to minimize unnecessary routing'
        ];
        break;
    }

    return {
      content: [{
        type: 'text',
        text: `Network Optimization Report:\n${JSON.stringify(optimization, null, 2)}`
      }]
    };
  }

  // Helper methods
  parseTailscaleStatus(output) {
    const lines = output.split('\n').filter(line => line.trim());
    const peers = [];

    for (const line of lines) {
      if (line.includes('100.') && !line.includes('Health check')) {
        const parts = line.trim().split(/\s+/);
        const peer = {
          ip: parts[0],
          hostname: parts[1],
          user: parts[2],
          os: parts[3],
          status: parts[4] || 'unknown'
        };
        peers.push(peer);
      }
    }

    return peers;
  }

  parseRoutes(output) {
    const routes = {
      advertised: [],
      accepted: [],
      exit_nodes: []
    };

    const lines = output.split('\n');
    for (const line of lines) {
      if (line.includes('offers exit node')) {
        const parts = line.trim().split(/\s+/);
        routes.exit_nodes.push(parts[0]);
      }
    }

    return routes;
  }

  async collectNetworkMetrics() {
    const metrics = {};

    try {
      // Get interface statistics
      const { stdout: interfaceStats } = await execAsync('cat /proc/net/dev | grep tailscale0 || echo "No tailscale interface"');
      if (interfaceStats !== 'No tailscale interface') {
        metrics.interface = this.parseInterfaceStats(interfaceStats);
      }

      // Get connection count
      const { stdout: connCount } = await execAsync('ss -tuln | wc -l');
      metrics.active_connections = parseInt(connCount.trim());

    } catch (error) {
      metrics.error = error.message;
    }

    return metrics;
  }

  async checkInfrastructureConnectivity() {
    const connectivity = {};

    for (const [key, node] of Object.entries(this.infrastructure)) {
      try {
        const { stdout } = await execAsync(`ping -c 1 -W 2 ${node.ip}`);
        connectivity[key] = {
          status: 'reachable',
          response_time: this.extractPingTime(stdout)
        };
      } catch (error) {
        connectivity[key] = {
          status: 'unreachable',
          error: error.message
        };
      }
    }

    return connectivity;
  }

  async scanHost(host, serviceType, fullScan) {
    const services = {
      host: host,
      scanned_at: new Date().toISOString(),
      services: []
    };

    try {
      // Use nmap if available, otherwise use netcat
      const commonPorts = fullScan ?
        '1-1000' :
        '22,80,443,3000,3001,5432,6379,8080,8443,8888';

      try {
        const { stdout } = await execAsync(`nmap -p ${commonPorts} ${host}`, { timeout: 30000 });
        services.services = this.parseNmapOutput(stdout);
      } catch (error) {
        // Fallback to manual port testing
        const portList = commonPorts.includes('-') ? [22, 80, 443, 3000, 5432] : commonPorts.split(',').map(Number);
        services.services = await this.testPorts(host, portList);
      }

    } catch (error) {
      services.error = error.message;
    }

    return services;
  }

  async testPorts(host, ports) {
    const results = [];

    for (const port of ports) {
      try {
        await execAsync(`nc -zv ${host} ${port}`, { timeout: 2000 });
        results.push({ port, status: 'open', service: this.identifyService(port) });
      } catch (error) {
        results.push({ port, status: 'closed' });
      }
    }

    return results;
  }

  identifyService(port) {
    const serviceMap = {
      22: 'SSH',
      80: 'HTTP',
      443: 'HTTPS',
      3000: 'Grafana/Development',
      3001: 'Grafana',
      5432: 'PostgreSQL',
      6379: 'Redis',
      7777: 'ThingsBoard',
      8080: 'HTTP Alt',
      8443: 'HTTPS Alt',
      8888: 'Development Server'
    };

    return serviceMap[port] || 'Unknown';
  }

  parseNmapOutput(output) {
    const services = [];
    const lines = output.split('\n');

    for (const line of lines) {
      if (line.includes('/tcp') && line.includes('open')) {
        const parts = line.trim().split(/\s+/);
        const portService = parts[0].split('/')[0];
        services.push({
          port: parseInt(portService),
          status: 'open',
          service: parts[2] || 'unknown'
        });
      }
    }

    return services;
  }

  parseInterfaceStats(output) {
    const parts = output.trim().split(/\s+/);
    return {
      interface: parts[0].replace(':', ''),
      rx_bytes: parseInt(parts[1]),
      rx_packets: parseInt(parts[2]),
      tx_bytes: parseInt(parts[9]),
      tx_packets: parseInt(parts[10])
    };
  }

  parseConnections(output) {
    const connections = [];
    const lines = output.split('\n').filter(line => line.includes('100.'));

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      if (parts.length >= 4) {
        connections.push({
          protocol: parts[0],
          local_address: parts[3],
          state: parts[1]
        });
      }
    }

    return connections;
  }

  extractPingTime(output) {
    const match = output.match(/time=(\d+\.?\d*)/);
    return match ? parseFloat(match[1]) : null;
  }

  async checkNodeHealth(node, checkServices, checkPerformance) {
    const health = {
      hostname: node.hostname,
      ip: node.ip,
      role: node.role,
      status: 'healthy',
      issues: []
    };

    try {
      // Test basic connectivity
      await execAsync(`ping -c 1 -W 2 ${node.ip}`);
      health.connectivity = 'ok';
    } catch (error) {
      health.connectivity = 'failed';
      health.status = 'critical';
      health.issues.push('Node unreachable');
    }

    if (checkServices && node.services) {
      health.services = {};
      for (const service of node.services) {
        // Check if service-specific ports are accessible
        const servicePort = this.getServicePort(service);
        if (servicePort) {
          try {
            await execAsync(`nc -zv ${node.ip} ${servicePort}`, { timeout: 5000 });
            health.services[service] = 'running';
          } catch (error) {
            health.services[service] = 'down';
            health.issues.push(`${service} service unavailable`);
            if (health.status === 'healthy') health.status = 'warning';
          }
        }
      }
    }

    return health;
  }

  getServicePort(service) {
    const servicePorts = {
      'grafana': 3001,
      'thingsboard': 7777,
      'postgresql': 5432,
      'pgadmin': 8443,
      'redis': 6379,
      'prometheus': 9091,
      'syncthing': 8384,
      'docker': 2376
    };

    return servicePorts[service];
  }

  async testConnectivity(ip) {
    try {
      const { stdout } = await execAsync(`ping -c 1 -W 2 ${ip}`);
      return {
        status: 'connected',
        latency: this.extractPingTime(stdout)
      };
    } catch (error) {
      return {
        status: 'disconnected',
        error: error.message
      };
    }
  }

  async executeOnHost(host, command) {
    // Execute command on remote host via SSH over Tailscale
    const sshCmd = `ssh -o StrictHostKeyChecking=no wil@${host} "${command}"`;
    const { stdout, stderr } = await execAsync(sshCmd);
    return stdout || stderr;
  }

  generateSystemdService(serviceName, executable, environment) {
    const envVars = Object.entries(environment)
      .map(([key, value]) => `Environment=${key}=${value}`)
      .join('\n');

    return `[Unit]
Description=${serviceName} service
After=network.target

[Service]
Type=simple
User=wil
ExecStart=${executable}
Restart=always
RestartSec=10
${envVars}

[Install]
WantedBy=multi-user.target`;
  }

  async deploySystemdService(host, serviceName, serviceContent) {
    const tempFile = `/tmp/${serviceName}.service`;

    // Write service file
    await fs.writeFile(tempFile, serviceContent);

    // Copy to target host and install
    const commands = [
      `scp ${tempFile} wil@${host}:/tmp/`,
      `ssh wil@${host} "sudo mv /tmp/${serviceName}.service /etc/systemd/system/"`,
      `ssh wil@${host} "sudo systemctl daemon-reload"`,
      `ssh wil@${host} "sudo systemctl enable ${serviceName}"`,
      `ssh wil@${host} "sudo systemctl start ${serviceName}"`
    ];

    let result = '';
    for (const cmd of commands) {
      const { stdout, stderr } = await execAsync(cmd);
      result += `${cmd}: ${stdout || stderr}\n`;
    }

    return result;
  }

  async measureNetworkPerformance(sourceHost, targetHost) {
    const metrics = {};

    try {
      // Measure latency
      const { stdout: pingOutput } = await execAsync(`ping -c 10 ${targetHost}`);
      metrics.latency = this.parsePingStats(pingOutput);

      // Measure bandwidth (if iperf3 is available)
      try {
        const { stdout: bandwidthOutput } = await execAsync(`iperf3 -c ${targetHost} -t 5 -J`);
        const bandwidthData = JSON.parse(bandwidthOutput);
        metrics.bandwidth = bandwidthData.end.sum_received.bits_per_second;
      } catch (error) {
        metrics.bandwidth = { error: 'iperf3 not available' };
      }

    } catch (error) {
      metrics.error = error.message;
    }

    return metrics;
  }

  parsePingStats(output) {
    const lines = output.split('\n');
    for (const line of lines) {
      if (line.includes('min/avg/max')) {
        const match = line.match(/(\d+\.?\d*)\/(\d+\.?\d*)\/(\d+\.?\d*)/);
        if (match) {
          return {
            min: parseFloat(match[1]),
            avg: parseFloat(match[2]),
            max: parseFloat(match[3])
          };
        }
      }
    }
    return null;
  }

  async gatherDetailedMetrics() {
    const metrics = {};

    try {
      // System metrics
      const { stdout: uptimeOutput } = await execAsync('uptime');
      metrics.uptime = uptimeOutput.trim();

      const { stdout: memoryOutput } = await execAsync('free -h');
      metrics.memory = memoryOutput;

      const { stdout: diskOutput } = await execAsync('df -h');
      metrics.disk = diskOutput;

      // Network interface metrics
      const { stdout: interfaceOutput } = await execAsync('cat /proc/net/dev');
      metrics.network_interfaces = interfaceOutput;

    } catch (error) {
      metrics.error = error.message;
    }

    return metrics;
  }

  // Resource implementations
  async getNetworkResource() {
    const status = await this.getNetworkStatus({ include_metrics: true, include_routes: true });
    return {
      contents: [{
        uri: 'tailscale://network/status',
        mimeType: 'application/json',
        text: status.content[0].text
      }]
    };
  }

  async getInfrastructureResource() {
    return {
      contents: [{
        uri: 'tailscale://infrastructure/map',
        mimeType: 'application/json',
        text: JSON.stringify(this.infrastructure, null, 2)
      }]
    };
  }

  async getSecurityResource() {
    const policies = {
      firewall_rules: [],
      access_policies: [],
      active_connections: []
    };

    try {
      const { stdout: firewallOutput } = await execAsync('iptables -L -n');
      policies.firewall_rules = firewallOutput.split('\n');

      const { stdout: connectionsOutput } = await execAsync('ss -tuln');
      policies.active_connections = this.parseConnections(connectionsOutput);

    } catch (error) {
      policies.error = error.message;
    }

    return {
      contents: [{
        uri: 'tailscale://security/policies',
        mimeType: 'application/json',
        text: JSON.stringify(policies, null, 2)
      }]
    };
  }

  async getServicesResource() {
    const catalog = {
      discovered_services: {},
      service_map: {},
      last_scan: new Date().toISOString()
    };

    // Quick discovery of known services
    for (const [key, node] of Object.entries(this.infrastructure)) {
      catalog.discovered_services[key] = {
        hostname: node.hostname,
        ip: node.ip,
        role: node.role,
        known_services: node.services,
        capabilities: node.capabilities
      };
    }

    return {
      contents: [{
        uri: 'tailscale://services/catalog',
        mimeType: 'application/json',
        text: JSON.stringify(catalog, null, 2)
      }]
    };
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Tailscale DevOps MCP Server started');
  }
}

// Start the server
const mcpServer = new TailscaleDevOpsMCP();
mcpServer.start().catch(console.error);

// Graceful shutdown
process.on('SIGINT', () => {
  console.error('Tailscale DevOps MCP Server shutting down...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error('Tailscale DevOps MCP Server shutting down...');
  process.exit(0);
});
