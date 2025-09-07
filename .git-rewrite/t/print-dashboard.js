#!/usr/bin/env node

/**
 * Print Queue Dashboard - Real-time monitoring and management
 */

const express = require('express');
const WebSocket = require('ws');
const AWS = require('aws-sdk');
const PrintQueueController = require('./print-queue-controller');
const STLValidator = require('./stl-validator');

class PrintQueueDashboard {
    constructor(port = 3001) {
        this.app = express();
        this.port = port;
        this.controller = new PrintQueueController();
        this.validator = new STLValidator();
        this.clients = new Set();
        
        this.setupMiddleware();
        this.setupRoutes();
        this.setupWebSocket();
    }

    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.static('public'));
        
        // CORS for development
        this.app.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', '*');
            res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
            next();
        });
    }

    setupRoutes() {
        // Dashboard API endpoints
        
        // Get overall status
        this.app.get('/api/status', async (req, res) => {
            try {
                const status = await this.controller.getStatus();
                res.json(status);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Get queue metrics
        this.app.get('/api/metrics', async (req, res) => {
            try {
                const metrics = await this.getDetailedMetrics();
                res.json(metrics);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Get printer status
        this.app.get('/api/printers', async (req, res) => {
            try {
                const printers = Array.from(this.controller.printers.entries()).map(([id, printer]) => ({
                    id,
                    name: printer.name,
                    status: printer.status,
                    location: printer.location,
                    capabilities: printer.capabilities,
                    currentJob: printer.currentJob?.jobId,
                    queuedJobs: printer.getQueuedJobs(),
                    lastHealthCheck: printer.lastHealthCheck
                }));
                res.json(printers);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Get specific printer details
        this.app.get('/api/printers/:id', async (req, res) => {
            try {
                const printer = this.controller.printers.get(req.params.id);
                if (!printer) {
                    return res.status(404).json({ error: 'Printer not found' });
                }
                
                res.json({
                    id: req.params.id,
                    name: printer.name,
                    status: printer.status,
                    location: printer.location,
                    capabilities: printer.capabilities,
                    maxBuildVolume: printer.maxBuildVolume,
                    currentJob: printer.currentJob,
                    queuedJobs: printer.queuedJobs,
                    lastHealthCheck: printer.lastHealthCheck
                });
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Get queue contents
        this.app.get('/api/queue', async (req, res) => {
            try {
                const queueContents = await this.getQueueContents();
                res.json(queueContents);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Get active jobs
        this.app.get('/api/jobs/active', async (req, res) => {
            try {
                const activeJobs = Array.from(this.controller.activeJobs.entries()).map(([id, job]) => ({
                    jobId: id,
                    orderId: job.orderId,
                    printer: job.printer.name,
                    status: job.status,
                    startTime: job.startTime,
                    estimatedCompletion: job.estimatedCompletion,
                    progress: job.progress || 0
                }));
                res.json(activeJobs);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Get job history
        this.app.get('/api/jobs/history', async (req, res) => {
            try {
                const history = await this.getJobHistory(req.query.limit || 50);
                res.json(history);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Validate STL file
        this.app.post('/api/validate-stl', async (req, res) => {
            try {
                if (!req.body.stlData) {
                    return res.status(400).json({ error: 'No STL data provided' });
                }
                
                const stlBuffer = Buffer.from(req.body.stlData, 'base64');
                const validation = await this.validator.validateSTL(stlBuffer);
                res.json(validation);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Manual job submission
        this.app.post('/api/jobs/submit', async (req, res) => {
            try {
                const { stlKey, orderData } = req.body;
                const result = await this.controller.stlQueue.processSTLToPrintQueue(stlKey, orderData);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Cancel job
        this.app.delete('/api/jobs/:jobId', async (req, res) => {
            try {
                const result = await this.cancelJob(req.params.jobId);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Printer control
        this.app.post('/api/printers/:id/:action', async (req, res) => {
            try {
                const result = await this.controlPrinter(req.params.id, req.params.action);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Dashboard HTML page
        this.app.get('/', (req, res) => {
            res.send(this.generateDashboardHTML());
        });
    }

    setupWebSocket() {
        this.wss = new WebSocket.Server({ port: this.port + 1 });
        
        this.wss.on('connection', (ws) => {
            console.log('📡 Dashboard client connected');
            this.clients.add(ws);
            
            // Send initial status
            this.sendStatusUpdate(ws);
            
            ws.on('close', () => {
                this.clients.delete(ws);
                console.log('📡 Dashboard client disconnected');
            });
            
            ws.on('message', async (message) => {
                try {
                    const data = JSON.parse(message);
                    await this.handleWebSocketMessage(ws, data);
                } catch (error) {
                    ws.send(JSON.stringify({ error: error.message }));
                }
            });
        });

        // Broadcast updates every 5 seconds
        setInterval(() => {
            this.broadcastUpdate();
        }, 5000);
    }

    async handleWebSocketMessage(ws, data) {
        switch (data.type) {
            case 'get_status':
                await this.sendStatusUpdate(ws);
                break;
            case 'get_metrics':
                const metrics = await this.getDetailedMetrics();
                ws.send(JSON.stringify({ type: 'metrics', data: metrics }));
                break;
            case 'control_printer':
                const result = await this.controlPrinter(data.printerId, data.action);
                ws.send(JSON.stringify({ type: 'printer_control_result', data: result }));
                break;
        }
    }

    async sendStatusUpdate(ws) {
        try {
            const status = await this.controller.getStatus();
            ws.send(JSON.stringify({ type: 'status_update', data: status }));
        } catch (error) {
            ws.send(JSON.stringify({ type: 'error', error: error.message }));
        }
    }

    async broadcastUpdate() {
        if (this.clients.size === 0) return;
        
        try {
            const status = await this.controller.getStatus();
            const message = JSON.stringify({ type: 'status_update', data: status });
            
            this.clients.forEach(client => {
                if (client.readyState === WebSocket.OPEN) {
                    client.send(message);
                }
            });
        } catch (error) {
            console.error('Failed to broadcast update:', error.message);
        }
    }

    async getDetailedMetrics() {
        const basic = this.controller.queueMetrics;
        const queueDepth = await this.controller.getQueueDepth();
        
        // Calculate additional metrics
        const successRate = basic.totalJobs > 0 ? 
            (basic.completedJobs / basic.totalJobs) * 100 : 0;
        
        const failureRate = basic.totalJobs > 0 ? 
            (basic.failedJobs / basic.totalJobs) * 100 : 0;

        return {
            ...basic,
            queueDepth,
            successRate: Math.round(successRate * 100) / 100,
            failureRate: Math.round(failureRate * 100) / 100,
            throughputPerHour: this.calculateThroughput(),
            avgWaitTime: this.calculateAvgWaitTime(),
            peakQueueDepth: this.getPeakQueueDepth()
        };
    }

    calculateThroughput() {
        // Simplified throughput calculation
        const hoursRunning = (Date.now() - this.startTime) / (1000 * 60 * 60);
        return hoursRunning > 0 ? this.controller.queueMetrics.completedJobs / hoursRunning : 0;
    }

    calculateAvgWaitTime() {
        // Simplified average wait time
        const queueDepth = this.controller.queueMetrics.queueDepth || 0;
        const avgPrintTime = this.controller.queueMetrics.avgPrintTime || 120;
        return queueDepth * avgPrintTime / Math.max(1, this.controller.queueMetrics.activePrinters);
    }

    getPeakQueueDepth() {
        // Would track this over time in a real implementation
        return this.controller.queueMetrics.queueDepth || 0;
    }

    async getQueueContents() {
        try {
            const messages = await this.controller.sqs.receiveMessage({
                QueueUrl: this.controller.stlQueue.queues.printJobs,
                MaxNumberOfMessages: 10,
                MessageAttributeNames: ['All']
            }).promise();

            if (!messages.Messages) {
                return [];
            }

            return messages.Messages.map(msg => {
                const jobData = JSON.parse(msg.Body);
                return {
                    jobId: jobData.jobId,
                    orderId: jobData.orderId,
                    priority: jobData.priority,
                    material: jobData.material,
                    estimatedTime: jobData.printTime,
                    queuedAt: jobData.createdAt
                };
            });
        } catch (error) {
            console.error('Failed to get queue contents:', error.message);
            return [];
        }
    }

    async getJobHistory(limit = 50) {
        // In a real implementation, this would query a database
        return [
            {
                jobId: 'job_123',
                orderId: 'ORD_456',
                status: 'completed',
                printer: 'Prusa MK3S #1',
                startTime: '2024-01-15T10:00:00Z',
                endTime: '2024-01-15T12:30:00Z',
                printTime: 150,
                material: 'PLA'
            }
        ];
    }

    async cancelJob(jobId) {
        const job = this.controller.activeJobs.get(jobId);
        if (!job) {
            throw new Error('Job not found');
        }

        // Stop the job and update status
        await job.cancel();
        this.controller.activeJobs.delete(jobId);

        return { success: true, jobId, status: 'cancelled' };
    }

    async controlPrinter(printerId, action) {
        const printer = this.controller.printers.get(printerId);
        if (!printer) {
            throw new Error('Printer not found');
        }

        switch (action) {
            case 'pause':
                printer.status = 'paused';
                break;
            case 'resume':
                printer.status = 'printing';
                break;
            case 'stop':
                printer.status = 'idle';
                if (printer.currentJob) {
                    await this.cancelJob(printer.currentJob.jobId);
                }
                break;
            case 'maintenance':
                printer.status = 'maintenance';
                break;
            default:
                throw new Error(`Unknown action: ${action}`);
        }

        return { success: true, printerId, action, newStatus: printer.status };
    }

    generateDashboardHTML() {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PetPlantr Print Queue Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 1rem; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
        .card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { text-align: center; margin-bottom: 1rem; }
        .metric-value { font-size: 2rem; font-weight: bold; color: #3498db; }
        .metric-label { color: #7f8c8d; font-size: 0.9rem; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-idle { background: #95a5a6; }
        .status-printing { background: #e74c3c; animation: pulse 2s infinite; }
        .status-offline { background: #34495e; }
        .status-error { background: #e67e22; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .printer-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
        .printer-card { border: 1px solid #ecf0f1; border-radius: 4px; padding: 1rem; }
        .queue-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid #ecf0f1; }
        .queue-item:last-child { border-bottom: none; }
        .priority-high { border-left: 4px solid #e74c3c; }
        .priority-medium { border-left: 4px solid #f39c12; }
        .priority-low { border-left: 4px solid #95a5a6; }
        .btn { background: #3498db; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖨️ PetPlantr Print Queue Dashboard</h1>
        <p>Real-time monitoring and control</p>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- Metrics Overview -->
            <div class="card">
                <h2>📊 Queue Metrics</h2>
                <div class="metric">
                    <div class="metric-value" id="queue-depth">--</div>
                    <div class="metric-label">Jobs in Queue</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="active-jobs">--</div>
                    <div class="metric-label">Active Jobs</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="success-rate">--%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>

            <!-- Printer Status -->
            <div class="card">
                <h2>🖨️ Printer Fleet</h2>
                <div id="printer-status" class="printer-grid">
                    <div class="printer-card">
                        <div><span class="status-indicator status-idle"></span>Loading...</div>
                    </div>
                </div>
            </div>

            <!-- Active Jobs -->
            <div class="card">
                <h2>⚡ Active Jobs</h2>
                <div id="active-jobs-list">
                    Loading active jobs...
                </div>
            </div>

            <!-- Queue Contents -->
            <div class="card">
                <h2>📋 Queue Contents</h2>
                <div id="queue-contents">
                    Loading queue...
                </div>
            </div>
        </div>
    </div>

    <script>
        class DashboardClient {
            constructor() {
                this.ws = null;
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;
                this.connect();
                this.setupRefreshInterval();
            }

            connect() {
                try {
                    this.ws = new WebSocket('ws://localhost:3002');
                    
                    this.ws.onopen = () => {
                        console.log('Connected to dashboard server');
                        this.reconnectAttempts = 0;
                        this.requestStatusUpdate();
                    };

                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    };

                    this.ws.onclose = () => {
                        console.log('Disconnected from dashboard server');
                        this.attemptReconnect();
                    };

                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                } catch (error) {
                    console.error('Failed to connect:', error);
                    this.attemptReconnect();
                }
            }

            attemptReconnect() {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(\`Attempting reconnect \${this.reconnectAttempts}/\${this.maxReconnectAttempts}\`);
                    setTimeout(() => this.connect(), 5000);
                } else {
                    console.error('Max reconnect attempts reached');
                }
            }

            requestStatusUpdate() {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'get_status' }));
                }
            }

            handleMessage(data) {
                switch (data.type) {
                    case 'status_update':
                        this.updateDashboard(data.data);
                        break;
                    case 'error':
                        console.error('Server error:', data.error);
                        break;
                }
            }

            updateDashboard(status) {
                // Update metrics
                document.getElementById('queue-depth').textContent = status.queueDepth || 0;
                document.getElementById('active-jobs').textContent = status.activeJobs || 0;
                
                // Update printers
                const printerContainer = document.getElementById('printer-status');
                printerContainer.innerHTML = status.printers.map(printer => \`
                    <div class="printer-card">
                        <div>
                            <span class="status-indicator status-\${printer.status}"></span>
                            \${printer.name}
                        </div>
                        <div style="font-size: 0.8rem; color: #7f8c8d;">
                            \${printer.location} • \${printer.status}
                        </div>
                        \${printer.currentJob ? \`<div style="font-size: 0.8rem;">Job: \${printer.currentJob}</div>\` : ''}
                    </div>
                \`).join('');

                // Update active jobs
                fetch('/api/jobs/active')
                    .then(response => response.json())
                    .then(jobs => {
                        const activeJobsList = document.getElementById('active-jobs-list');
                        if (jobs.length === 0) {
                            activeJobsList.innerHTML = '<div style="text-align: center; color: #7f8c8d;">No active jobs</div>';
                        } else {
                            activeJobsList.innerHTML = jobs.map(job => \`
                                <div class="queue-item">
                                    <div>
                                        <strong>\${job.jobId}</strong><br>
                                        <small>\${job.printer} • \${job.status}</small>
                                    </div>
                                    <button class="btn btn-danger" onclick="cancelJob('\${job.jobId}')">Cancel</button>
                                </div>
                            \`).join('');
                        }
                    });

                // Update queue
                fetch('/api/queue')
                    .then(response => response.json())
                    .then(queue => {
                        const queueContents = document.getElementById('queue-contents');
                        if (queue.length === 0) {
                            queueContents.innerHTML = '<div style="text-align: center; color: #7f8c8d;">Queue is empty</div>';
                        } else {
                            queueContents.innerHTML = queue.map(item => \`
                                <div class="queue-item priority-\${item.priority > 7 ? 'high' : item.priority > 4 ? 'medium' : 'low'}">
                                    <div>
                                        <strong>\${item.orderId}</strong><br>
                                        <small>\${item.material} • \${item.estimatedTime}min</small>
                                    </div>
                                    <div>Priority: \${item.priority}</div>
                                </div>
                            \`).join('');
                        }
                    });
            }

            setupRefreshInterval() {
                setInterval(() => {
                    this.requestStatusUpdate();
                }, 10000); // Refresh every 10 seconds
            }
        }

        function cancelJob(jobId) {
            if (confirm(\`Cancel job \${jobId}?\`)) {
                fetch(\`/api/jobs/\${jobId}\`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            alert('Job cancelled successfully');
                        } else {
                            alert('Failed to cancel job');
                        }
                    })
                    .catch(error => {
                        alert('Error cancelling job: ' + error.message);
                    });
            }
        }

        // Initialize dashboard
        const dashboard = new DashboardClient();
    </script>
</body>
</html>
        `;
    }

    async start() {
        this.startTime = Date.now();
        
        // Initialize the print queue controller
        await this.controller.initialize();
        
        // Start the HTTP server
        this.server = this.app.listen(this.port, () => {
            console.log(`🌐 Print Queue Dashboard running at http://localhost:${this.port}`);
            console.log(`📡 WebSocket server running on port ${this.port + 1}`);
        });
    }

    async stop() {
        console.log('🛑 Stopping Print Queue Dashboard...');
        
        if (this.server) {
            this.server.close();
        }
        
        if (this.wss) {
            this.wss.close();
        }
        
        await this.controller.shutdown();
        console.log('✅ Dashboard stopped');
    }
}

// Main execution
if (require.main === module) {
    const dashboard = new PrintQueueDashboard();
    
    const handleShutdown = async (signal) => {
        console.log(`\n🛑 Received ${signal}, shutting down...`);
        await dashboard.stop();
        process.exit(0);
    };

    process.on('SIGINT', () => handleShutdown('SIGINT'));
    process.on('SIGTERM', () => handleShutdown('SIGTERM'));

    dashboard.start().catch(error => {
        console.error('Failed to start dashboard:', error);
        process.exit(1);
    });
}

module.exports = PrintQueueDashboard;
