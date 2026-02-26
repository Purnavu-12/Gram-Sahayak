export interface ServiceInstance {
  url: string;
  healthy: boolean;
  weight: number;
  activeConnections: number;
}

export enum LoadBalancingStrategy {
  ROUND_ROBIN = 'ROUND_ROBIN',
  LEAST_CONNECTIONS = 'LEAST_CONNECTIONS',
  WEIGHTED_ROUND_ROBIN = 'WEIGHTED_ROUND_ROBIN',
}

export class LoadBalancer {
  private instances: Map<string, ServiceInstance[]> = new Map();
  private currentIndex: Map<string, number> = new Map();

  constructor(private strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN) {}

  registerInstance(serviceName: string, instance: ServiceInstance): void {
    if (!this.instances.has(serviceName)) {
      this.instances.set(serviceName, []);
      this.currentIndex.set(serviceName, 0);
    }
    this.instances.get(serviceName)!.push(instance);
  }

  getNextInstance(serviceName: string): ServiceInstance | undefined {
    const instances = this.instances.get(serviceName);
    if (!instances || instances.length === 0) {
      return undefined;
    }

    // Filter healthy instances
    const healthyInstances = instances.filter(i => i.healthy);
    if (healthyInstances.length === 0) {
      return undefined;
    }

    switch (this.strategy) {
      case LoadBalancingStrategy.ROUND_ROBIN:
        return this.roundRobin(serviceName, healthyInstances);
      case LoadBalancingStrategy.LEAST_CONNECTIONS:
        return this.leastConnections(healthyInstances);
      case LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
        return this.weightedRoundRobin(serviceName, healthyInstances);
      default:
        return this.roundRobin(serviceName, healthyInstances);
    }
  }

  private roundRobin(serviceName: string, instances: ServiceInstance[]): ServiceInstance {
    const currentIdx = this.currentIndex.get(serviceName) || 0;
    const instance = instances[currentIdx % instances.length];
    this.currentIndex.set(serviceName, currentIdx + 1);
    return instance;
  }

  private leastConnections(instances: ServiceInstance[]): ServiceInstance {
    return instances.reduce((min, instance) =>
      instance.activeConnections < min.activeConnections ? instance : min
    );
  }

  private weightedRoundRobin(serviceName: string, instances: ServiceInstance[]): ServiceInstance {
    const totalWeight = instances.reduce((sum, i) => sum + i.weight, 0);
    const currentIdx = this.currentIndex.get(serviceName) || 0;
    
    let weightSum = 0;
    for (const instance of instances) {
      weightSum += instance.weight;
      if (currentIdx % totalWeight < weightSum) {
        this.currentIndex.set(serviceName, currentIdx + 1);
        return instance;
      }
    }
    
    // Fallback to first instance
    this.currentIndex.set(serviceName, currentIdx + 1);
    return instances[0];
  }

  markInstanceHealthy(serviceName: string, url: string, healthy: boolean): void {
    const instances = this.instances.get(serviceName);
    if (!instances) return;

    const instance = instances.find(i => i.url === url);
    if (instance) {
      instance.healthy = healthy;
    }
  }

  incrementConnections(serviceName: string, url: string): void {
    const instances = this.instances.get(serviceName);
    if (!instances) return;

    const instance = instances.find(i => i.url === url);
    if (instance) {
      instance.activeConnections++;
    }
  }

  decrementConnections(serviceName: string, url: string): void {
    const instances = this.instances.get(serviceName);
    if (!instances) return;

    const instance = instances.find(i => i.url === url);
    if (instance && instance.activeConnections > 0) {
      instance.activeConnections--;
    }
  }

  getStats(serviceName: string) {
    const instances = this.instances.get(serviceName);
    if (!instances) return null;

    return {
      serviceName,
      totalInstances: instances.length,
      healthyInstances: instances.filter(i => i.healthy).length,
      instances: instances.map(i => ({
        url: i.url,
        healthy: i.healthy,
        weight: i.weight,
        activeConnections: i.activeConnections,
      })),
    };
  }
}
