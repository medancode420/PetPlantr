import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

/**
 * 🏭 Multi-Printer Farm Management Lambda
 * Manages printer farm operations, job assignment, and monitoring
 */

interface PrinterStatus {
  printerId: string;
  name: string;
  ipAddress: string;
  status: 'idle' | 'printing' | 'paused' | 'error' | 'offline' | 'maintenance';
  currentJob?: string;
  progress: number;
  qualityScoreAvg: number;
  successRate: number;
  totalJobsCompleted: number;
}

interface PrintJob {
  jobId: string;
  customerId: string;
  customerEmail: string;
  petName: string;
  breed: string;
  stlFile: string;
  estimatedTime: number;
  materialType: string;
  materialColor: string;
  priority: number;
  complexity: number;
  qualityRequirements: 'standard' | 'high' | 'premium';
  status: 'queued' | 'assigned' | 'printing' | 'completed' | 'failed';
  assignedPrinter?: string;
  createdAt: string;
  updatedAt: string;
}

interface FarmStats {
  totalPrinters: number;
  activePrinters: number;
  printingPrinters: number;
  utilizationRate: number;
  queueSize: number;
  activeJobs: number;
  completedToday: number;
  averageQuality: number;
  averageSuccessRate: number;
}

// Mock data for demonstration - in production, this would use DynamoDB
const mockPrinters: PrinterStatus[] = [
  {
    printerId: 'k1_max_01',
    name: 'Primary K1 Max',
    ipAddress: '10.0.0.200',
    status: 'printing',
    currentJob: 'JOB_001',
    progress: 65.5,
    qualityScoreAvg: 96.2,
    successRate: 98.5,
    totalJobsCompleted: 127
  },
  {
    printerId: 'k1_max_02',
    name: 'Quality K1 Max',
    ipAddress: '10.0.0.201',
    status: 'idle',
    progress: 0,
    qualityScoreAvg: 97.8,
    successRate: 99.2,
    totalJobsCompleted: 98
  },
  {
    printerId: 'k1_max_03',
    name: 'Speed K1 Max',
    ipAddress: '10.0.0.202',
    status: 'printing',
    currentJob: 'JOB_002',
    progress: 23.1,
    qualityScoreAvg: 94.5,
    successRate: 96.8,
    totalJobsCompleted: 156
  },
  {
    printerId: 'k1_max_04',
    name: 'Production K1 Max',
    ipAddress: '10.0.0.203',
    status: 'idle',
    progress: 0,
    qualityScoreAvg: 95.3,
    successRate: 97.1,
    totalJobsCompleted: 134
  }
];

const mockJobs: PrintJob[] = [
  {
    jobId: 'JOB_001',
    customerId: 'cust_001',
    customerEmail: 'sarah@example.com',
    petName: 'Buddy',
    breed: 'Golden Retriever',
    stlFile: '/output/golden_retriever_planter.stl',
    estimatedTime: 3.5,
    materialType: 'PLA',
    materialColor: 'Golden',
    priority: 1,
    complexity: 6.5,
    qualityRequirements: 'high',
    status: 'printing',
    assignedPrinter: 'k1_max_01',
    createdAt: '2025-07-28T10:00:00Z',
    updatedAt: '2025-07-28T10:30:00Z'
  },
  {
    jobId: 'JOB_002',
    customerId: 'cust_002',
    customerEmail: 'mike@example.com',
    petName: 'Luna',
    breed: 'Siberian Husky',
    stlFile: '/output/husky_planter.stl',
    estimatedTime: 4.0,
    materialType: 'PLA',
    materialColor: 'White',
    priority: 2,
    complexity: 7.5,
    qualityRequirements: 'high',
    status: 'printing',
    assignedPrinter: 'k1_max_03',
    createdAt: '2025-07-28T09:30:00Z',
    updatedAt: '2025-07-28T10:45:00Z'
  },
  {
    jobId: 'JOB_003',
    customerId: 'cust_003',
    customerEmail: 'emily@example.com',
    petName: 'Max',
    breed: 'Beagle',
    stlFile: '/output/beagle_planter.stl',
    estimatedTime: 2.5,
    materialType: 'PLA',
    materialColor: 'Brown',
    priority: 3,
    complexity: 4.5,
    qualityRequirements: 'standard',
    status: 'queued',
    createdAt: '2025-07-28T11:00:00Z',
    updatedAt: '2025-07-28T11:00:00Z'
  }
];

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    const { httpMethod, path, body } = event;
    const pathSegments = path.split('/').filter(Boolean);
    
    console.log(`🏭 Farm Management Request: ${httpMethod} ${path}`);

    // Route to appropriate handler
    switch (httpMethod) {
      case 'GET':
        return await handleGetRequest(pathSegments, event.queryStringParameters);
      case 'POST':
        return await handlePostRequest(pathSegments, JSON.parse(body || '{}'));
      case 'PUT':
        return await handlePutRequest(pathSegments, JSON.parse(body || '{}'));
      case 'DELETE':
        return await handleDeleteRequest(pathSegments);
      default:
        return createResponse(405, { error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('🚨 Farm management error:', error);
    return createResponse(500, { 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

async function handleGetRequest(
  pathSegments: string[], 
  queryParams: any
): Promise<APIGatewayProxyResult> {
  const endpoint = pathSegments[2]; // /api/farm/{endpoint}

  switch (endpoint) {
    case 'status':
      return await getFarmStatus();
    case 'printers':
      return await getPrinters(queryParams?.detailed === 'true');
    case 'jobs':
      return await getJobs(queryParams);
    case 'metrics':
      return await getFarmMetrics(queryParams?.timeframe || '24h');
    case 'optimization':
      return await getFarmOptimization();
    default:
      return createResponse(404, { error: 'Endpoint not found' });
  }
}

async function handlePostRequest(
  pathSegments: string[], 
  body: any
): Promise<APIGatewayProxyResult> {
  const endpoint = pathSegments[2];

  switch (endpoint) {
    case 'printers':
      return await addPrinter(body);
    case 'jobs':
      return await createPrintJob(body);
    case 'assign':
      return await assignJob(body.jobId, body.printerId);
    case 'complete':
      return await completeJob(body.jobId, body.success, body.qualityScore);
    default:
      return createResponse(404, { error: 'Endpoint not found' });
  }
}

async function handlePutRequest(
  pathSegments: string[], 
  body: any
): Promise<APIGatewayProxyResult> {
  const endpoint = pathSegments[2];
  const id = pathSegments[3];

  switch (endpoint) {
    case 'printers':
      return await updatePrinter(id, body);
    case 'jobs':
      return await updateJob(id, body);
    default:
      return createResponse(404, { error: 'Endpoint not found' });
  }
}

async function handleDeleteRequest(pathSegments: string[]): Promise<APIGatewayProxyResult> {
  const endpoint = pathSegments[2];
  const id = pathSegments[3];

  switch (endpoint) {
    case 'printers':
      return await removePrinter(id);
    case 'jobs':
      return await cancelJob(id);
    default:
      return createResponse(404, { error: 'Endpoint not found' });
  }
}

async function getFarmStatus(): Promise<APIGatewayProxyResult> {
  try {
    const printers = mockPrinters;
    const jobs = mockJobs;

    const stats: FarmStats = {
      totalPrinters: printers.length,
      activePrinters: printers.filter(p => p.status !== 'offline').length,
      printingPrinters: printers.filter(p => p.status === 'printing').length,
      utilizationRate: printers.length > 0 ? 
        (printers.filter(p => p.status === 'printing').length / printers.length) * 100 : 0,
      queueSize: jobs.filter(j => j.status === 'queued').length,
      activeJobs: jobs.filter(j => j.status === 'printing').length,
      completedToday: 15, // Mock value
      averageQuality: printers.reduce((sum, p) => sum + p.qualityScoreAvg, 0) / printers.length || 0,
      averageSuccessRate: printers.reduce((sum, p) => sum + p.successRate, 0) / printers.length || 0
    };

    return createResponse(200, {
      timestamp: new Date().toISOString(),
      farmStats: stats,
      printers: printers,
      activeJobs: jobs.filter(j => j.status !== 'queued')
    });

  } catch (error) {
    console.error('Error getting farm status:', error);
    return createResponse(500, { error: 'Failed to get farm status' });
  }
}

async function getPrinters(detailed: boolean = false): Promise<APIGatewayProxyResult> {
  try {
    const printers = detailed ? mockPrinters : mockPrinters.map(p => ({
      printerId: p.printerId,
      name: p.name,
      status: p.status,
      progress: p.progress,
      currentJob: p.currentJob
    }));

    return createResponse(200, { printers });

  } catch (error) {
    console.error('Error getting printers:', error);
    return createResponse(500, { error: 'Failed to get printers' });
  }
}

async function getJobs(queryParams: any): Promise<APIGatewayProxyResult> {
  try {
    let jobs = [...mockJobs];

    // Filter by status if provided
    if (queryParams?.status) {
      jobs = jobs.filter(j => j.status === queryParams.status);
    }

    // Filter by printer if provided
    if (queryParams?.printer) {
      jobs = jobs.filter(j => j.assignedPrinter === queryParams.printer);
    }

    return createResponse(200, { jobs });

  } catch (error) {
    console.error('Error getting jobs:', error);
    return createResponse(500, { error: 'Failed to get jobs' });
  }
}

async function getFarmMetrics(timeframe: string): Promise<APIGatewayProxyResult> {
  try {
    // Mock metrics based on timeframe
    const metrics = {
      timeframe,
      timestamp: new Date().toISOString(),
      production: {
        totalJobs: timeframe === '24h' ? 23 : timeframe === '7d' ? 156 : 634,
        completedJobs: timeframe === '24h' ? 21 : timeframe === '7d' ? 148 : 612,
        failedJobs: timeframe === '24h' ? 2 : timeframe === '7d' ? 8 : 22,
        averagePrintTime: 3.2,
        totalPrintTime: timeframe === '24h' ? 67.2 : timeframe === '7d' ? 473.6 : 1964.8
      },
      quality: {
        averageScore: 95.8,
        highQualityJobs: timeframe === '24h' ? 15 : timeframe === '7d' ? 89 : 378,
        standardQualityJobs: timeframe === '24h' ? 6 : timeframe === '7d' ? 59 : 234
      },
      efficiency: {
        utilizationRate: 87.3,
        idleTime: timeframe === '24h' ? 3.6 : timeframe === '7d' ? 21.2 : 89.7,
        maintenanceTime: timeframe === '24h' ? 1.2 : timeframe === '7d' ? 8.4 : 34.2
      }
    };

    return createResponse(200, metrics);

  } catch (error) {
    console.error('Error getting farm metrics:', error);
    return createResponse(500, { error: 'Failed to get farm metrics' });
  }
}

async function addPrinter(printerData: any): Promise<APIGatewayProxyResult> {
  try {
    const newPrinter: PrinterStatus = {
      printerId: printerData.printerId || `printer_${Date.now()}`,
      name: printerData.name,
      ipAddress: printerData.ipAddress,
      status: 'idle',
      progress: 0,
      qualityScoreAvg: 95.0,
      successRate: 100.0,
      totalJobsCompleted: 0
    };

    // In production, this would save to DynamoDB
    mockPrinters.push(newPrinter);

    console.log(`✅ Added printer: ${newPrinter.name} (${newPrinter.printerId})`);
    return createResponse(201, { 
      message: 'Printer added successfully',
      printer: newPrinter 
    });

  } catch (error) {
    console.error('Error adding printer:', error);
    return createResponse(500, { error: 'Failed to add printer' });
  }
}

async function createPrintJob(jobData: any): Promise<APIGatewayProxyResult> {
  try {
    const newJob: PrintJob = {
      jobId: jobData.jobId || `job_${Date.now()}`,
      customerId: jobData.customerId,
      customerEmail: jobData.customerEmail,
      petName: jobData.petName,
      breed: jobData.breed,
      stlFile: jobData.stlFile,
      estimatedTime: jobData.estimatedTime,
      materialType: jobData.materialType,
      materialColor: jobData.materialColor,
      priority: jobData.priority || 5,
      complexity: jobData.complexity || 5,
      qualityRequirements: jobData.qualityRequirements || 'standard',
      status: 'queued',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // In production, this would save to DynamoDB
    mockJobs.push(newJob);

    console.log(`📋 Created print job: ${newJob.jobId} for ${newJob.petName}`);
    return createResponse(201, { 
      message: 'Print job created successfully',
      job: newJob 
    });

  } catch (error) {
    console.error('Error creating print job:', error);
    return createResponse(500, { error: 'Failed to create print job' });
  }
}

async function assignJob(jobId: string, printerId?: string): Promise<APIGatewayProxyResult> {
  try {
    const job = mockJobs.find(j => j.jobId === jobId);
    if (!job) {
      return createResponse(404, { error: 'Job not found' });
    }

    let selectedPrinterId = printerId;
    if (!selectedPrinterId) {
      // Find optimal printer
      const availablePrinters = mockPrinters.filter(p => p.status === 'idle');
      if (availablePrinters.length === 0) {
        return createResponse(400, { error: 'No available printers' });
      }
      selectedPrinterId = availablePrinters[0].printerId;
    }

    const printer = mockPrinters.find(p => p.printerId === selectedPrinterId);
    if (!printer) {
      return createResponse(404, { error: 'Printer not found' });
    }

    // Update job and printer
    job.status = 'assigned';
    job.assignedPrinter = selectedPrinterId;
    job.updatedAt = new Date().toISOString();
    
    printer.status = 'printing';
    printer.currentJob = jobId;

    console.log(`🎯 Assigned job ${jobId} to printer ${selectedPrinterId}`);
    return createResponse(200, { 
      message: 'Job assigned successfully',
      jobId,
      printerId: selectedPrinterId
    });

  } catch (error) {
    console.error('Error assigning job:', error);
    return createResponse(500, { error: 'Failed to assign job' });
  }
}

async function completeJob(jobId: string, success: boolean, qualityScore: number): Promise<APIGatewayProxyResult> {
  try {
    const job = mockJobs.find(j => j.jobId === jobId);
    if (!job) {
      return createResponse(404, { error: 'Job not found' });
    }

    const printer = mockPrinters.find(p => p.printerId === job.assignedPrinter);
    if (!printer) {
      return createResponse(404, { error: 'Assigned printer not found' });
    }

    // Update job
    job.status = success ? 'completed' : 'failed';
    job.updatedAt = new Date().toISOString();

    // Update printer
    printer.status = 'idle';
    printer.currentJob = undefined;
    printer.progress = 0;
    printer.totalJobsCompleted += 1;
    
    if (success) {
      printer.qualityScoreAvg = (printer.qualityScoreAvg * 0.9) + (qualityScore * 0.1);
    }

    console.log(`${success ? '✅' : '❌'} Job ${jobId} completed on ${printer.printerId}`);
    return createResponse(200, { 
      message: `Job ${success ? 'completed' : 'failed'} successfully`,
      jobId,
      qualityScore: success ? qualityScore : undefined
    });

  } catch (error) {
    console.error('Error completing job:', error);
    return createResponse(500, { error: 'Failed to complete job' });
  }
}

async function updatePrinter(printerId: string, updateData: any): Promise<APIGatewayProxyResult> {
  try {
    const printer = mockPrinters.find(p => p.printerId === printerId);
    if (!printer) {
      return createResponse(404, { error: 'Printer not found' });
    }

    // Update printer properties
    Object.assign(printer, updateData);

    return createResponse(200, { 
      message: 'Printer updated successfully',
      printer 
    });

  } catch (error) {
    console.error('Error updating printer:', error);
    return createResponse(500, { error: 'Failed to update printer' });
  }
}

async function updateJob(jobId: string, updateData: any): Promise<APIGatewayProxyResult> {
  try {
    const job = mockJobs.find(j => j.jobId === jobId);
    if (!job) {
      return createResponse(404, { error: 'Job not found' });
    }

    // Update job properties
    Object.assign(job, updateData);
    job.updatedAt = new Date().toISOString();

    return createResponse(200, { 
      message: 'Job updated successfully',
      job 
    });

  } catch (error) {
    console.error('Error updating job:', error);
    return createResponse(500, { error: 'Failed to update job' });
  }
}

async function removePrinter(printerId: string): Promise<APIGatewayProxyResult> {
  try {
    const index = mockPrinters.findIndex(p => p.printerId === printerId);
    if (index === -1) {
      return createResponse(404, { error: 'Printer not found' });
    }

    mockPrinters.splice(index, 1);

    return createResponse(200, { 
      message: 'Printer removed successfully'
    });

  } catch (error) {
    console.error('Error removing printer:', error);
    return createResponse(500, { error: 'Failed to remove printer' });
  }
}

async function cancelJob(jobId: string): Promise<APIGatewayProxyResult> {
  try {
    const job = mockJobs.find(j => j.jobId === jobId);
    if (!job) {
      return createResponse(404, { error: 'Job not found' });
    }

    // If job is assigned to a printer, free up the printer
    if (job.assignedPrinter) {
      const printer = mockPrinters.find(p => p.printerId === job.assignedPrinter);
      if (printer) {
        printer.status = 'idle';
        printer.currentJob = undefined;
        printer.progress = 0;
      }
    }

    // Remove job
    const index = mockJobs.findIndex(j => j.jobId === jobId);
    if (index !== -1) {
      mockJobs.splice(index, 1);
    }

    return createResponse(200, { 
      message: 'Job cancelled successfully'
    });

  } catch (error) {
    console.error('Error cancelling job:', error);
    return createResponse(500, { error: 'Failed to cancel job' });
  }
}

async function getFarmOptimization(): Promise<APIGatewayProxyResult> {
  try {
    const recommendations: string[] = [];
    let optimizationScore = 100;

    const stats = await getFarmStatus();
    const farmData = JSON.parse(stats.body);
    
    const { farmStats } = farmData;

    // Analyze utilization
    if (farmStats.utilizationRate > 90) {
      recommendations.push('🚨 High utilization detected - consider adding more printers');
      optimizationScore -= 15;
    } else if (farmStats.utilizationRate < 30) {
      recommendations.push('📊 Low utilization - optimize job scheduling');
      optimizationScore -= 10;
    }

    // Check queue size
    if (farmStats.queueSize > farmStats.activePrinters * 2) {
      recommendations.push('📈 Large queue detected - scaling needed');
      optimizationScore -= 10;
    }

    // Quality checks
    if (farmStats.averageQuality < 90) {
      recommendations.push('🎯 Quality declining - maintenance required');
      optimizationScore -= 20;
    }

    // Success rate checks
    if (farmStats.averageSuccessRate < 95) {
      recommendations.push('🔧 Success rate low - investigate printer issues');
      optimizationScore -= 15;
    }

    const farmHealth = optimizationScore >= 90 ? 'excellent' : 
                      optimizationScore >= 70 ? 'good' : 'needs_attention';

    return createResponse(200, {
      timestamp: new Date().toISOString(),
      farmHealth,
      optimizationScore,
      recommendations,
      suggestedActions: {
        immediate: recommendations.filter(r => r.includes('🚨') || r.includes('🔧')),
        planning: recommendations.filter(r => r.includes('📈') || r.includes('📊'))
      }
    });

  } catch (error) {
    console.error('Error getting farm optimization:', error);
    return createResponse(500, { error: 'Failed to get optimization data' });
  }
}

function createResponse(statusCode: number, body: any): APIGatewayProxyResult {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    },
    body: JSON.stringify(body)
  };
}
