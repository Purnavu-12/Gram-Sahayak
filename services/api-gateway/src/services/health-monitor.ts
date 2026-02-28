import axios from 'axios';

export interface ServiceHealth {
  name: string;
  url: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  responseTime?: number;
  lastChecked: Date;
  error?: string;
}

export interface SystemHealth {
  overall: 'healthy' | 'degraded' | 'unhealthy';
  services: ServiceHealth[];
  timestamp: Date;
}

export class HealthMonitor {
  private services = [
    { name: 'voice-engine', url: 'http://voice-engine:3001/health' },
    { name: 'dialect-detector', url: 'http://dialect-detector:8001/health' },
    { name: 'scheme-matcher', url: 'http://scheme-matcher:8002/health' },
    { name: 'form-generator', url: 'http://form-generator:3002/health' },
    { name: 'document-guide', url: 'http://document-guide:8003/health' },
    { name: 'application-tracker', url: 'http://application-tracker:8004/health' },
    { name: 'user-profile', url: 'http://user-profile:8005/health' },
    { name: 'accessibility', url: 'http://accessibility:3003/health' },
  ];

  private healthCache: Map<string, ServiceHealth> = new Map();
  private cacheTimeout = 30000; // 30 seconds

  async checkServiceHealth(service: { name: string; url: string }): Promise<ServiceHealth> {
    const startTime = Date.now();
    
    try {
      const response = await axios.get(service.url, { timeout: 5000 });
      const responseTime = Date.now() - startTime;
      
      const health: ServiceHealth = {
        name: service.name,
        url: service.url,
        status: response.status === 200 ? 'healthy' : 'unhealthy',
        responseTime,
        lastChecked: new Date(),
      };

      this.healthCache.set(service.name, health);
      return health;
    } catch (error: any) {
      const health: ServiceHealth = {
        name: service.name,
        url: service.url,
        status: 'unhealthy',
        responseTime: Date.now() - startTime,
        lastChecked: new Date(),
        error: error.message,
      };

      this.healthCache.set(service.name, health);
      return health;
    }
  }

  async checkAllServices(): Promise<SystemHealth> {
    const healthChecks = await Promise.all(
      this.services.map(service => this.checkServiceHealth(service))
    );

    // Update cache
    healthChecks.forEach(health => {
      this.healthCache.set(health.name, health);
    });

    // Determine overall health
    const healthyCount = healthChecks.filter(h => h.status === 'healthy').length;
    const totalCount = healthChecks.length;
    
    let overall: 'healthy' | 'degraded' | 'unhealthy';
    if (healthyCount === totalCount) {
      overall = 'healthy';
    } else if (healthyCount >= totalCount * 0.5) {
      overall = 'degraded';
    } else {
      overall = 'unhealthy';
    }

    return {
      overall,
      services: healthChecks,
      timestamp: new Date(),
    };
  }

  getCachedHealth(serviceName: string): ServiceHealth | undefined {
    const cached = this.healthCache.get(serviceName);
    if (!cached) return undefined;

    // Check if cache is still valid
    const age = Date.now() - cached.lastChecked.getTime();
    if (age > this.cacheTimeout) {
      return undefined;
    }

    return cached;
  }

  async getServiceHealth(serviceName: string): Promise<ServiceHealth> {
    // Try cache first
    const cached = this.getCachedHealth(serviceName);
    if (cached) return cached;

    // Check service
    const service = this.services.find(s => s.name === serviceName);
    if (!service) {
      return {
        name: serviceName,
        url: 'unknown',
        status: 'unknown',
        lastChecked: new Date(),
        error: 'Service not found',
      };
    }

    return this.checkServiceHealth(service);
  }
}
