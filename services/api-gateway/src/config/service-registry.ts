export interface ServiceConfig {
  name: string;
  url: string;
  healthEndpoint: string;
  port: number;
  protocol: 'http' | 'https';
  type: 'typescript' | 'python';
}

export const SERVICE_REGISTRY: ServiceConfig[] = [
  {
    name: 'voice-engine',
    url: 'voice-engine',
    healthEndpoint: '/health',
    port: 3001,
    protocol: 'http',
    type: 'typescript',
  },
  {
    name: 'dialect-detector',
    url: 'dialect-detector',
    healthEndpoint: '/health',
    port: 8001,
    protocol: 'http',
    type: 'python',
  },
  {
    name: 'scheme-matcher',
    url: 'scheme-matcher',
    healthEndpoint: '/health',
    port: 8002,
    protocol: 'http',
    type: 'python',
  },
  {
    name: 'form-generator',
    url: 'form-generator',
    healthEndpoint: '/health',
    port: 3002,
    protocol: 'http',
    type: 'typescript',
  },
  {
    name: 'document-guide',
    url: 'document-guide',
    healthEndpoint: '/health',
    port: 8003,
    protocol: 'http',
    type: 'python',
  },
  {
    name: 'application-tracker',
    url: 'application-tracker',
    healthEndpoint: '/health',
    port: 8004,
    protocol: 'http',
    type: 'python',
  },
  {
    name: 'user-profile',
    url: 'user-profile',
    healthEndpoint: '/health',
    port: 8005,
    protocol: 'http',
    type: 'python',
  },
  {
    name: 'accessibility',
    url: 'accessibility',
    healthEndpoint: '/health',
    port: 3003,
    protocol: 'http',
    type: 'typescript',
  },
];

export function getServiceUrl(serviceName: string): string | undefined {
  const service = SERVICE_REGISTRY.find(s => s.name === serviceName);
  if (!service) return undefined;
  return `${service.protocol}://${service.url}:${service.port}`;
}

export function getServiceConfig(serviceName: string): ServiceConfig | undefined {
  return SERVICE_REGISTRY.find(s => s.name === serviceName);
}

export function getAllServices(): ServiceConfig[] {
  return SERVICE_REGISTRY;
}
