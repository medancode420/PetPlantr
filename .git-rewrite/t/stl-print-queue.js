#!/usr/bin/env node

/**
 * PetPlantr STL-to-Print Automation Pipeline
 * Automates the process from generated STL files to 3D printer queue
 */

const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');

class STLPrintQueue {
    constructor() {
        this.s3 = new AWS.S3({ region: 'us-west-2' });
        this.sqs = new AWS.SQS({ region: 'us-west-2' });
        this.sns = new AWS.SNS({ region: 'us-west-2' });
        
        this.buckets = {
            stlReady: 'petplantr-stl-ready-dev',
            printQueue: 'petplantr-print-queue',
            completed: 'petplantr-prints-completed'
        };
        
        this.queues = {
            printJobs: process.env.PRINT_QUEUE_URL || 'https://sqs.us-west-2.amazonaws.com/your-account/petplantr-print-queue',
            notifications: process.env.NOTIFICATION_QUEUE_URL
        };
    }

    async log(message) {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] ${message}`);
        
        // Optional: Send to CloudWatch Logs
        try {
            await this.sns.publish({
                TopicArn: process.env.LOGGING_TOPIC_ARN,
                Message: `${timestamp}: ${message}`,
                Subject: 'PetPlantr Print Queue Log'
            }).promise();
        } catch (error) {
            // Silent fail for logging
        }
    }

    async validateSTL(stlBuffer) {
        this.log('Validating STL file format and printability...');
        
        try {
            // Basic STL validation
            const header = stlBuffer.slice(0, 80).toString();
            const triangleCount = stlBuffer.readUInt32LE(80);
            const expectedSize = 80 + 4 + (triangleCount * 50);
            
            if (stlBuffer.length !== expectedSize) {
                throw new Error(`Invalid STL file size. Expected: ${expectedSize}, Got: ${stlBuffer.length}`);
            }

            // Check for minimum/maximum size constraints
            const stats = await this.analyzeSTLGeometry(stlBuffer);
            
            if (stats.volume < 1) { // Less than 1 cubic cm
                throw new Error('STL volume too small for printing');
            }
            
            if (stats.volume > 1000) { // More than 1000 cubic cm
                throw new Error('STL volume too large for printing');
            }

            if (stats.minWallThickness < 0.8) { // Less than 0.8mm
                throw new Error('Wall thickness too thin for reliable printing');
            }

            return {
                valid: true,
                stats,
                printable: true
            };
        } catch (error) {
            return {
                valid: false,
                error: error.message,
                printable: false
            };
        }
    }

    async analyzeSTLGeometry(stlBuffer) {
        // Basic STL geometry analysis
        const triangleCount = stlBuffer.readUInt32LE(80);
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        let minZ = Infinity, maxZ = -Infinity;
        
        for (let i = 0; i < triangleCount; i++) {
            const offset = 84 + i * 50;
            
            // Read vertices (3 vertices * 3 coordinates * 4 bytes each)
            for (let v = 0; v < 3; v++) {
                const vertexOffset = offset + 12 + v * 12;
                const x = stlBuffer.readFloatLE(vertexOffset);
                const y = stlBuffer.readFloatLE(vertexOffset + 4);
                const z = stlBuffer.readFloatLE(vertexOffset + 8);
                
                minX = Math.min(minX, x);
                maxX = Math.max(maxX, x);
                minY = Math.min(minY, y);
                maxY = Math.max(maxY, y);
                minZ = Math.min(minZ, z);
                maxZ = Math.max(maxZ, z);
            }
        }

        const dimensions = {
            x: maxX - minX,
            y: maxY - minY,
            z: maxZ - minZ
        };

        return {
            triangleCount,
            dimensions,
            volume: dimensions.x * dimensions.y * dimensions.z,
            minWallThickness: 0.8, // Simplified - would need actual mesh analysis
            boundingBox: { minX, maxX, minY, maxY, minZ, maxZ }
        };
    }

    async optimizeForPrinting(stlBuffer, orderId) {
        this.log(`Optimizing STL for printing: ${orderId}`);
        
        try {
            // Save STL temporarily for processing
            const tempPath = `/tmp/${orderId}.stl`;
            fs.writeFileSync(tempPath, stlBuffer);
            
            // Use mesh processing tools (if available)
            const optimizations = await this.runMeshOptimizations(tempPath);
            
            // Read optimized file
            const optimizedBuffer = fs.readFileSync(tempPath);
            
            // Clean up
            fs.unlinkSync(tempPath);
            
            return {
                optimized: true,
                buffer: optimizedBuffer,
                changes: optimizations
            };
        } catch (error) {
            this.log(`Optimization failed: ${error.message}, using original STL`);
            return {
                optimized: false,
                buffer: stlBuffer,
                error: error.message
            };
        }
    }

    async runMeshOptimizations(stlPath) {
        // Example optimizations using external tools
        const optimizations = [];
        
        try {
            // Repair mesh (using meshlab or similar)
            await this.executeCommand(`meshlabserver -i ${stlPath} -o ${stlPath} -s repair_mesh.mlx`);
            optimizations.push('mesh_repair');
        } catch (error) {
            // Fallback if meshlab not available
        }

        try {
            // Add support structures metadata
            optimizations.push('support_analysis');
        } catch (error) {
            // Continue without supports
        }

        return optimizations;
    }

    async generatePrintJob(stlKey, orderData) {
        this.log(`Generating print job for order: ${orderData.orderId}`);
        
        // Download STL from S3
        const stlObject = await this.s3.getObject({
            Bucket: this.buckets.stlReady,
            Key: stlKey
        }).promise();

        // Validate STL
        const validation = await this.validateSTL(stlObject.Body);
        if (!validation.valid) {
            throw new Error(`STL validation failed: ${validation.error}`);
        }

        // Optimize for printing
        const optimization = await this.optimizeForPrinting(stlObject.Body, orderData.orderId);

        // Calculate print time and material usage
        const printEstimate = await this.estimatePrintRequirements(optimization.buffer);

        // Generate slicing instructions
        const slicingProfile = await this.generateSlicingProfile(validation.stats, orderData);

        const printJob = {
            jobId: `print_${orderData.orderId}_${Date.now()}`,
            orderId: orderData.orderId,
            customerId: orderData.customerId,
            stlKey: stlKey,
            
            // Print specifications
            material: orderData.material || 'PLA',
            color: orderData.color || 'natural',
            quality: orderData.quality || 'standard',
            
            // Technical details
            printTime: printEstimate.timeMinutes,
            materialUsage: printEstimate.materialGrams,
            supportRequired: printEstimate.needsSupports,
            
            // Slicing configuration
            slicingProfile: slicingProfile,
            
            // Validation results
            geometry: validation.stats,
            optimizations: optimization.changes,
            
            // Queue metadata
            priority: this.calculatePriority(orderData),
            estimatedStart: new Date(),
            status: 'queued',
            
            // Tracking
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString()
        };

        return printJob;
    }

    async estimatePrintRequirements(stlBuffer) {
        const stats = await this.analyzeSTLGeometry(stlBuffer);
        
        // Simplified calculations - would use actual slicer in production
        const volume = stats.volume;
        const fillDensity = 0.15; // 15% infill
        const materialDensity = 1.24; // PLA density g/cm³
        
        const materialUsage = volume * fillDensity * materialDensity;
        const printSpeed = 50; // mm/s average
        const printTime = (volume * 0.1) + 30; // Simplified estimate in minutes
        
        const needsSupports = stats.dimensions.z > stats.dimensions.x * 1.5;

        return {
            timeMinutes: Math.round(printTime),
            materialGrams: Math.round(materialUsage),
            needsSupports,
            estimatedCost: materialUsage * 0.05 + (printTime / 60) * 2 // $0.05/g + $2/hour
        };
    }

    async generateSlicingProfile(geometry, orderData) {
        const baseProfile = {
            // Layer settings
            layerHeight: orderData.quality === 'high' ? 0.15 : 0.2,
            firstLayerHeight: 0.3,
            
            // Speed settings
            printSpeed: 50,
            travelSpeed: 120,
            firstLayerSpeed: 20,
            
            // Temperature settings
            hotendTemp: this.getMaterialTemp(orderData.material),
            bedTemp: this.getBedTemp(orderData.material),
            
            // Infill settings
            infillDensity: orderData.quality === 'high' ? 20 : 15,
            infillPattern: 'gyroid',
            
            // Support settings
            supportEnabled: geometry.dimensions.z > geometry.dimensions.x * 1.5,
            supportDensity: 15,
            supportPattern: 'rectilinear',
            
            // Perimeter settings
            perimeters: orderData.quality === 'high' ? 3 : 2,
            topSolidLayers: 4,
            bottomSolidLayers: 3
        };

        return baseProfile;
    }

    getMaterialTemp(material) {
        const temps = {
            'PLA': 210,
            'PETG': 235,
            'ABS': 245,
            'TPU': 220
        };
        return temps[material] || 210;
    }

    getBedTemp(material) {
        const temps = {
            'PLA': 60,
            'PETG': 70,
            'ABS': 90,
            'TPU': 50
        };
        return temps[material] || 60;
    }

    calculatePriority(orderData) {
        let priority = 5; // Normal priority
        
        // Rush orders
        if (orderData.rushOrder) priority += 3;
        
        // Premium customers
        if (orderData.customerTier === 'premium') priority += 2;
        
        // Small prints (faster turnaround)
        if (orderData.estimatedTime < 60) priority += 1;
        
        return Math.min(priority, 10); // Max priority 10
    }

    async queuePrintJob(printJob) {
        this.log(`Queuing print job: ${printJob.jobId}`);
        
        try {
            // Upload optimized STL to print queue bucket
            const printStlKey = `queue/${printJob.jobId}.stl`;
            await this.s3.putObject({
                Bucket: this.buckets.printQueue,
                Key: printStlKey,
                Body: printJob.stlBuffer,
                Metadata: {
                    'job-id': printJob.jobId,
                    'order-id': printJob.orderId,
                    'priority': printJob.priority.toString(),
                    'material': printJob.material,
                    'estimated-time': printJob.printTime.toString()
                }
            }).promise();

            // Send job to SQS queue
            const queueMessage = {
                jobId: printJob.jobId,
                orderId: printJob.orderId,
                stlKey: printStlKey,
                priority: printJob.priority,
                printTime: printJob.printTime,
                material: printJob.material,
                slicingProfile: printJob.slicingProfile,
                createdAt: printJob.createdAt
            };

            await this.sqs.sendMessage({
                QueueUrl: this.queues.printJobs,
                MessageBody: JSON.stringify(queueMessage),
                MessageAttributes: {
                    'Priority': {
                        DataType: 'Number',
                        StringValue: printJob.priority.toString()
                    },
                    'Material': {
                        DataType: 'String',
                        StringValue: printJob.material
                    },
                    'EstimatedTime': {
                        DataType: 'Number',
                        StringValue: printJob.printTime.toString()
                    }
                }
            }).promise();

            // Update order status
            await this.updateOrderStatus(printJob.orderId, 'print_queued', {
                jobId: printJob.jobId,
                estimatedStart: this.calculateEstimatedStart(printJob.priority)
            });

            this.log(`Print job queued successfully: ${printJob.jobId}`);
            return {
                success: true,
                jobId: printJob.jobId,
                queuePosition: await this.getQueuePosition(printJob.priority)
            };
        } catch (error) {
            this.log(`Failed to queue print job: ${error.message}`);
            throw error;
        }
    }

    async calculateEstimatedStart(priority) {
        // Get current queue length and estimate start time
        const queueAttributes = await this.sqs.getQueueAttributes({
            QueueUrl: this.queues.printJobs,
            AttributeNames: ['ApproximateNumberOfMessages']
        }).promise();

        const queueLength = parseInt(queueAttributes.Attributes.ApproximateNumberOfMessages);
        const avgPrintTime = 120; // 2 hours average
        const hoursDelay = (queueLength * avgPrintTime) / 60;
        
        // Priority jobs jump ahead
        const priorityBonus = Math.max(0, (priority - 5) * 2);
        const adjustedDelay = Math.max(0, hoursDelay - priorityBonus);

        const estimatedStart = new Date();
        estimatedStart.setHours(estimatedStart.getHours() + adjustedDelay);
        
        return estimatedStart;
    }

    async getQueuePosition(priority) {
        // Simplified queue position calculation
        const queueAttributes = await this.sqs.getQueueAttributes({
            QueueUrl: this.queues.printJobs,
            AttributeNames: ['ApproximateNumberOfMessages']
        }).promise();

        const totalJobs = parseInt(queueAttributes.Attributes.ApproximateNumberOfMessages);
        const priorityFactor = Math.max(1, (10 - priority) / 10);
        
        return Math.ceil(totalJobs * priorityFactor);
    }

    async updateOrderStatus(orderId, status, metadata = {}) {
        // Update order in database (DynamoDB, etc.)
        try {
            const updateData = {
                orderId,
                status,
                lastUpdated: new Date().toISOString(),
                ...metadata
            };

            // This would integrate with your order management system
            this.log(`Order ${orderId} status updated to: ${status}`);
            
            // Send customer notification
            await this.sendCustomerNotification(orderId, status, metadata);
            
        } catch (error) {
            this.log(`Failed to update order status: ${error.message}`);
        }
    }

    async sendCustomerNotification(orderId, status, metadata) {
        const messages = {
            'print_queued': `Your PetPlantr order ${orderId} has been queued for printing! Estimated start time: ${metadata.estimatedStart}`,
            'printing': `Great news! Your PetPlantr order ${orderId} is now printing. Estimated completion: ${metadata.estimatedCompletion}`,
            'print_complete': `Your PetPlantr order ${orderId} has finished printing and is being prepared for shipping!`,
            'shipped': `Your PetPlantr order ${orderId} has shipped! Track your package: ${metadata.trackingNumber}`
        };

        const message = messages[status];
        if (!message) return;

        try {
            await this.sns.publish({
                TopicArn: process.env.CUSTOMER_NOTIFICATIONS_TOPIC,
                Message: message,
                Subject: `PetPlantr Order Update - ${orderId}`
            }).promise();
        } catch (error) {
            this.log(`Failed to send customer notification: ${error.message}`);
        }
    }

    async processSTLToPrintQueue(stlKey, orderData) {
        this.log(`Processing STL to print queue: ${stlKey}`);
        
        try {
            // Generate print job
            const printJob = await this.generatePrintJob(stlKey, orderData);
            
            // Queue the print job
            const queueResult = await this.queuePrintJob(printJob);
            
            // Log success
            this.log(`STL successfully queued for printing: ${printJob.jobId}`);
            
            return {
                success: true,
                jobId: printJob.jobId,
                orderId: orderData.orderId,
                queuePosition: queueResult.queuePosition,
                estimatedStart: await this.calculateEstimatedStart(printJob.priority),
                printTime: printJob.printTime,
                materialUsage: printJob.materialUsage
            };
            
        } catch (error) {
            this.log(`STL processing failed: ${error.message}`);
            
            // Update order with error status
            await this.updateOrderStatus(orderData.orderId, 'print_failed', {
                error: error.message,
                retryable: !error.message.includes('validation')
            });
            
            throw error;
        }
    }

    async executeCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) reject(error);
                else resolve({ stdout, stderr });
            });
        });
    }

    // Monitor and process new STL files
    async monitorSTLBucket() {
        this.log('Starting STL bucket monitoring...');
        
        // This would typically be triggered by S3 events
        setInterval(async () => {
            try {
                const objects = await this.s3.listObjects({
                    Bucket: this.buckets.stlReady,
                    Prefix: 'ready/'
                }).promise();

                for (const object of objects.Contents) {
                    if (object.Key.endsWith('.stl')) {
                        // Extract order data from object metadata or key
                        const orderId = this.extractOrderId(object.Key);
                        const orderData = await this.getOrderData(orderId);
                        
                        if (orderData && !orderData.processed) {
                            await this.processSTLToPrintQueue(object.Key, orderData);
                            
                            // Mark as processed
                            await this.markSTLProcessed(object.Key);
                        }
                    }
                }
            } catch (error) {
                this.log(`Monitoring error: ${error.message}`);
            }
        }, 30000); // Check every 30 seconds
    }

    extractOrderId(s3Key) {
        // Extract order ID from S3 key pattern
        const match = s3Key.match(/ready\/order_(\w+)_/);
        return match ? match[1] : null;
    }

    async getOrderData(orderId) {
        // Fetch order data from your database
        return {
            orderId,
            customerId: 'customer_123',
            material: 'PLA',
            color: 'green',
            quality: 'standard',
            rushOrder: false,
            customerTier: 'standard',
            processed: false
        };
    }

    async markSTLProcessed(s3Key) {
        // Move STL to processed folder
        const newKey = s3Key.replace('ready/', 'processed/');
        
        await this.s3.copyObject({
            Bucket: this.buckets.stlReady,
            CopySource: `${this.buckets.stlReady}/${s3Key}`,
            Key: newKey
        }).promise();

        await this.s3.deleteObject({
            Bucket: this.buckets.stlReady,
            Key: s3Key
        }).promise();
    }
}

// Example usage and testing
async function demonstrateSTLQueue() {
    const queue = new STLPrintQueue();
    
    // Example order data
    const orderData = {
        orderId: 'ORD_12345',
        customerId: 'CUST_67890',
        material: 'PLA',
        color: 'forest_green',
        quality: 'high',
        rushOrder: false,
        customerTier: 'premium'
    };

    try {
        // Process an STL file
        const result = await queue.processSTLToPrintQueue('ready/order_12345_planter.stl', orderData);
        console.log('Print job queued:', result);
        
    } catch (error) {
        console.error('Queue processing failed:', error.message);
    }
}

// Main execution
if (require.main === module) {
    const queue = new STLPrintQueue();
    
    if (process.argv[2] === 'monitor') {
        queue.monitorSTLBucket();
    } else if (process.argv[2] === 'demo') {
        demonstrateSTLQueue();
    } else {
        console.log('Usage: node stl-print-queue.js [monitor|demo]');
    }
}

module.exports = STLPrintQueue;
