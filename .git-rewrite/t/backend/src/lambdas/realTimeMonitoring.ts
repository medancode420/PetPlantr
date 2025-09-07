import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

/**
 * 📊 Real-Time Monitoring & Analytics Lambda
 * Provides comprehensive monitoring of the entire PetPlantr production pipeline
 */

interface ProductionMetrics {
  timestamp: string;
  overview: {
    activeOrders: number;
    printingJobs: number;
    completedToday: number;
    revenue24h: number;
    averageOrderValue: number;
    customerSatisfaction: number;
  };
  farmStatus: {
    totalPrinters: number;
    activePrinters: number;
    utilizationRate: number;
    averageQuality: number;
    successRate: number;
    queueLength: number;
  };
  performance: {
    orderProcessingTime: number;
    modelingTime: number;
    printTime: number;
    shippingTime: number;
    totalFulfillmentTime: number;
  };
  alerts: Alert[];
  trends: {
    orderVolume: number[];
    qualityTrend: number[];
    utilizationTrend: number[];
  };
}

interface Alert {
  id: string;
  type: 'warning' | 'error' | 'info';
  category: 'farm' | 'orders' | 'quality' | 'performance';
  title: string;
  description: string;
  timestamp: string;
  acknowledged: boolean;
}

interface CustomerAnalytics {
  totalCustomers: number;
  newCustomersToday: number;
  repeatCustomers: number;
  averageOrderValue: number;
  popularBreeds: { breed: string; count: number }[];
  popularProducts: { product: string; count: number }[];
  geographicDistribution: { region: string; count: number }[];
  satisfactionScores: { score: number; count: number }[];
}

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    const { httpMethod, path, queryStringParameters } = event;
    const pathSegments = path.split('/').filter(Boolean);
    
    console.log(`📊 Monitoring Request: ${httpMethod} ${path}`);

    switch (httpMethod) {
      case 'GET':
        return await handleGetRequest(pathSegments, queryStringParameters);
      case 'POST':
        return await handlePostRequest(pathSegments, JSON.parse(event.body || '{}'));
      default:
        return createResponse(405, { error: 'Method not allowed' });
    }

  } catch (error) {
    console.error('🚨 Monitoring error:', error);
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
  const endpoint = pathSegments[2]; // /api/monitoring/{endpoint}

  switch (endpoint) {
    case 'dashboard':
      return await getDashboardData(queryParams?.timeframe || '24h');
    case 'metrics':
      return await getProductionMetrics(queryParams?.timeframe || '24h');
    case 'alerts':
      return await getAlerts(queryParams?.status);
    case 'analytics':
      return await getCustomerAnalytics(queryParams?.timeframe || '30d');
    case 'health':
      return await getSystemHealth();
    case 'performance':
      return await getPerformanceMetrics(queryParams?.timeframe || '24h');
    case 'real-time':
      return await getRealTimeData();
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
    case 'alerts':
      return await acknowledgeAlert(body.alertId);
    case 'metrics':
      return await recordCustomMetric(body);
    default:
      return createResponse(404, { error: 'Endpoint not found' });
  }
}

async function getDashboardData(timeframe: string): Promise<APIGatewayProxyResult> {
  try {
    const metrics = await generateProductionMetrics(timeframe);
    const analytics = await generateCustomerAnalytics(timeframe);
    const alerts = await generateActiveAlerts();

    const dashboardData = {
      timestamp: new Date().toISOString(),
      timeframe,
      summary: {
        totalRevenue: calculateRevenue(timeframe),
        ordersProcessed: metrics.overview.completedToday,
        printingUtilization: metrics.farmStatus.utilizationRate,
        customerSatisfaction: analytics.satisfactionScores.reduce((avg, s) => avg + (s.score * s.count), 0) / 
                             analytics.satisfactionScores.reduce((sum, s) => sum + s.count, 0) || 0,
        systemHealth: calculateSystemHealth(metrics, alerts)
      },
      metrics,
      analytics,
      alerts: alerts.filter(a => !a.acknowledged),
      recommendations: generateRecommendations(metrics, analytics, alerts)
    };

    return createResponse(200, dashboardData);

  } catch (error) {
    console.error('Error getting dashboard data:', error);
    return createResponse(500, { error: 'Failed to get dashboard data' });
  }
}

async function getProductionMetrics(timeframe: string): Promise<APIGatewayProxyResult> {
  try {
    const metrics = await generateProductionMetrics(timeframe);
    return createResponse(200, metrics);

  } catch (error) {
    console.error('Error getting production metrics:', error);
    return createResponse(500, { error: 'Failed to get production metrics' });
  }
}

async function getAlerts(status?: string): Promise<APIGatewayProxyResult> {
  try {
    const alerts = await generateActiveAlerts();
    
    const filteredAlerts = status ? 
      alerts.filter(a => status === 'acknowledged' ? a.acknowledged : !a.acknowledged) :
      alerts;

    return createResponse(200, {
      alerts: filteredAlerts,
      summary: {
        total: alerts.length,
        unacknowledged: alerts.filter(a => !a.acknowledged).length,
        critical: alerts.filter(a => a.type === 'error').length,
        warnings: alerts.filter(a => a.type === 'warning').length
      }
    });

  } catch (error) {
    console.error('Error getting alerts:', error);
    return createResponse(500, { error: 'Failed to get alerts' });
  }
}

async function getCustomerAnalytics(timeframe: string): Promise<APIGatewayProxyResult> {
  try {
    const analytics = await generateCustomerAnalytics(timeframe);
    return createResponse(200, analytics);

  } catch (error) {
    console.error('Error getting customer analytics:', error);
    return createResponse(500, { error: 'Failed to get customer analytics' });
  }
}

async function getSystemHealth(): Promise<APIGatewayProxyResult> {
  try {
    const healthData = {
      timestamp: new Date().toISOString(),
      services: {
        orderProcessing: await checkServiceHealth('orders'),
        farmManager: await checkServiceHealth('farm'),
        aiModeling: await checkServiceHealth('modeling'),
        paymentProcessing: await checkServiceHealth('payments'),
        notifications: await checkServiceHealth('notifications')
      },
      infrastructure: {
        lambdaHealth: 'healthy',
        databaseHealth: 'healthy',
        s3Health: 'healthy',
        eventBridgeHealth: 'healthy'
      },
      overall: 'healthy',
      uptime: '99.97%',
      lastIncident: null
    };

    const overallHealth = Object.values(healthData.services).every(status => status === 'healthy') &&
                         Object.values(healthData.infrastructure).every(status => status === 'healthy') ?
                         'healthy' : 'degraded';

    healthData.overall = overallHealth;

    return createResponse(200, healthData);

  } catch (error) {
    console.error('Error getting system health:', error);
    return createResponse(500, { error: 'Failed to get system health' });
  }
}

async function getPerformanceMetrics(timeframe: string): Promise<APIGatewayProxyResult> {
  try {
    const performanceData = {
      timestamp: new Date().toISOString(),
      timeframe,
      apiPerformance: {
        averageResponseTime: 245, // ms
        p95ResponseTime: 890,
        p99ResponseTime: 1450,
        errorRate: 0.12, // %
        requestsPerSecond: 12.4
      },
      orderProcessing: {
        averageProcessingTime: 1.8, // minutes
        modelingTime: 8.5, // minutes
        printTime: 185, // minutes
        shippingTime: 1440, // minutes (24 hours)
        totalFulfillmentTime: 7200 // minutes (5 days)
      },
      farmPerformance: {
        averageUtilization: 87.3,
        averageQuality: 95.8,
        successRate: 98.2,
        averagePrintTime: 3.2,
        maintenanceDowntime: 45 // minutes
      },
      bottlenecks: identifyBottlenecks()
    };

    return createResponse(200, performanceData);

  } catch (error) {
    console.error('Error getting performance metrics:', error);
    return createResponse(500, { error: 'Failed to get performance metrics' });
  }
}

async function getRealTimeData(): Promise<APIGatewayProxyResult> {
  try {
    const realTimeData = {
      timestamp: new Date().toISOString(),
      currentActivity: {
        ordersInProgress: 23,
        printersActive: 3,
        queueLength: 8,
        modelsBeingGenerated: 5,
        customersOnline: 42
      },
      liveMetrics: {
        orderRate: 2.3, // orders per hour
        printCompletionRate: 1.8, // prints per hour
        systemLoad: 68, // %
        errorRate: 0.08 // %
      },
      recentActivity: await getRecentActivity(),
      systemAlerts: await generateActiveAlerts()
    };

    return createResponse(200, realTimeData);

  } catch (error) {
    console.error('Error getting real-time data:', error);
    return createResponse(500, { error: 'Failed to get real-time data' });
  }
}

// Helper functions for generating mock data

async function generateProductionMetrics(timeframe: string): Promise<ProductionMetrics> {
  const multiplier = timeframe === '24h' ? 1 : timeframe === '7d' ? 7 : 30;
  
  return {
    timestamp: new Date().toISOString(),
    overview: {
      activeOrders: 23,
      printingJobs: 4,
      completedToday: 18 * multiplier,
      revenue24h: 1567.89 * multiplier,
      averageOrderValue: 87.16,
      customerSatisfaction: 4.7
    },
    farmStatus: {
      totalPrinters: 4,
      activePrinters: 4,
      utilizationRate: 87.3,
      averageQuality: 95.8,
      successRate: 98.2,
      queueLength: 8
    },
    performance: {
      orderProcessingTime: 1.8,
      modelingTime: 8.5,
      printTime: 185,
      shippingTime: 1440,
      totalFulfillmentTime: 7200
    },
    alerts: await generateActiveAlerts(),
    trends: {
      orderVolume: generateTrendData(24, 15, 25),
      qualityTrend: generateTrendData(24, 94, 98),
      utilizationTrend: generateTrendData(24, 80, 95)
    }
  };
}

async function generateCustomerAnalytics(timeframe: string): Promise<CustomerAnalytics> {
  return {
    totalCustomers: 1247,
    newCustomersToday: 23,
    repeatCustomers: 156,
    averageOrderValue: 87.16,
    popularBreeds: [
      { breed: 'Golden Retriever', count: 45 },
      { breed: 'Labrador', count: 38 },
      { breed: 'German Shepherd', count: 32 },
      { breed: 'Bulldog', count: 28 },
      { breed: 'Beagle', count: 25 }
    ],
    popularProducts: [
      { product: 'Basic Planter', count: 89 },
      { product: 'Premium Planter', count: 56 },
      { product: 'Custom Planter', count: 23 }
    ],
    geographicDistribution: [
      { region: 'California', count: 67 },
      { region: 'Texas', count: 45 },
      { region: 'New York', count: 38 },
      { region: 'Florida', count: 32 },
      { region: 'Illinois', count: 28 }
    ],
    satisfactionScores: [
      { score: 5, count: 78 },
      { score: 4, count: 45 },
      { score: 3, count: 12 },
      { score: 2, count: 3 },
      { score: 1, count: 1 }
    ]
  };
}

async function generateActiveAlerts(): Promise<Alert[]> {
  return [
    {
      id: 'alert_001',
      type: 'warning',
      category: 'farm',
      title: 'High Utilization',
      description: 'Printer farm utilization at 87% - consider adding capacity',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      acknowledged: false
    },
    {
      id: 'alert_002',
      type: 'info',
      category: 'orders',
      title: 'Order Volume Spike',
      description: 'Order volume 23% higher than usual for this time',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      acknowledged: false
    },
    {
      id: 'alert_003',
      type: 'warning',
      category: 'quality',
      title: 'Quality Variance',
      description: 'Printer k1_max_03 showing quality variance - maintenance recommended',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      acknowledged: true
    }
  ];
}

function generateTrendData(hours: number, min: number, max: number): number[] {
  return Array.from({ length: hours }, () => 
    Math.random() * (max - min) + min
  );
}

function calculateRevenue(timeframe: string): number {
  const baseRevenue = 1567.89;
  return timeframe === '24h' ? baseRevenue : 
         timeframe === '7d' ? baseRevenue * 7 : 
         baseRevenue * 30;
}

function calculateSystemHealth(metrics: ProductionMetrics, alerts: Alert[]): number {
  let health = 100;
  
  // Deduct for critical alerts
  health -= alerts.filter(a => a.type === 'error' && !a.acknowledged).length * 20;
  health -= alerts.filter(a => a.type === 'warning' && !a.acknowledged).length * 10;
  
  // Factor in farm performance
  if (metrics.farmStatus.successRate < 95) health -= 15;
  if (metrics.farmStatus.utilizationRate > 90) health -= 5;
  
  return Math.max(health, 0);
}

function generateRecommendations(
  metrics: ProductionMetrics, 
  analytics: CustomerAnalytics, 
  alerts: Alert[]
): string[] {
  const recommendations: string[] = [];
  
  if (metrics.farmStatus.utilizationRate > 85) {
    recommendations.push('📈 Consider adding more 3D printers to handle increased demand');
  }
  
  if (metrics.farmStatus.averageQuality < 95) {
    recommendations.push('🔧 Schedule maintenance for printers with declining quality scores');
  }
  
  if (analytics.averageOrderValue < 80) {
    recommendations.push('💰 Implement upselling strategies to increase average order value');
  }
  
  if (alerts.filter(a => !a.acknowledged).length > 5) {
    recommendations.push('⚠️ Address pending alerts to maintain system health');
  }
  
  return recommendations;
}

async function checkServiceHealth(service: string): Promise<string> {
  // Mock service health check
  const healthStatuses = ['healthy', 'degraded', 'unhealthy'];
  const weights = [0.9, 0.08, 0.02]; // 90% healthy, 8% degraded, 2% unhealthy
  
  const random = Math.random();
  let cumulative = 0;
  
  for (let i = 0; i < weights.length; i++) {
    cumulative += weights[i];
    if (random <= cumulative) {
      return healthStatuses[i];
    }
  }
  
  return 'healthy';
}

function identifyBottlenecks(): string[] {
  return [
    'AI modeling queue during peak hours',
    'Print time for complex geometries',
    'Manual quality inspection process'
  ];
}

async function getRecentActivity(): Promise<any[]> {
  return [
    {
      timestamp: new Date(Date.now() - 300000).toISOString(),
      type: 'order_completed',
      description: 'Order #12345 completed printing - Golden Retriever planter'
    },
    {
      timestamp: new Date(Date.now() - 600000).toISOString(),
      type: 'new_order',
      description: 'New order received - Beagle planter from Sarah J.'
    },
    {
      timestamp: new Date(Date.now() - 900000).toISOString(),
      type: 'printer_maintenance',
      description: 'Printer k1_max_02 completed scheduled maintenance'
    }
  ];
}

async function acknowledgeAlert(alertId: string): Promise<APIGatewayProxyResult> {
  try {
    // In production, this would update the alert in the database
    console.log(`✅ Alert ${alertId} acknowledged`);
    
    return createResponse(200, {
      message: 'Alert acknowledged successfully',
      alertId
    });

  } catch (error) {
    console.error('Error acknowledging alert:', error);
    return createResponse(500, { error: 'Failed to acknowledge alert' });
  }
}

async function recordCustomMetric(metricData: any): Promise<APIGatewayProxyResult> {
  try {
    console.log(`📊 Recording custom metric: ${metricData.name}`);
    
    return createResponse(200, {
      message: 'Metric recorded successfully',
      metric: metricData
    });

  } catch (error) {
    console.error('Error recording metric:', error);
    return createResponse(500, { error: 'Failed to record metric' });
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
