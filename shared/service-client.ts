import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

export interface ServiceClientConfig {
  baseURL: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

export class ServiceClient {
  private client: AxiosInstance;
  private retries: number;
  private retryDelay: number;

  constructor(config: ServiceClientConfig) {
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.retries = config.retries || 3;
    this.retryDelay = config.retryDelay || 1000;
  }

  async get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    return this.executeWithRetry(() => 
      this.client.get<T>(path, config).then(res => res.data)
    );
  }

  async post<T>(path: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.executeWithRetry(() =>
      this.client.post<T>(path, data, config).then(res => res.data)
    );
  }

  async put<T>(path: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.executeWithRetry(() =>
      this.client.put<T>(path, data, config).then(res => res.data)
    );
  }

  async delete<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    return this.executeWithRetry(() =>
      this.client.delete<T>(path, config).then(res => res.data)
    );
  }

  private async executeWithRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 1; attempt <= this.retries; attempt++) {
      try {
        return await fn();
      } catch (error: any) {
        lastError = error;

        // Don't retry on client errors (4xx)
        if (error.response && error.response.status >= 400 && error.response.status < 500) {
          throw error;
        }

        // Don't retry on last attempt
        if (attempt === this.retries) {
          break;
        }

        // Wait before retry
        await this.sleep(this.retryDelay * attempt);
      }
    }

    throw lastError || new Error('Request failed');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Service client factory
export class ServiceClientFactory {
  private static clients: Map<string, ServiceClient> = new Map();

  static getClient(serviceName: string, baseURL: string): ServiceClient {
    if (!this.clients.has(serviceName)) {
      this.clients.set(serviceName, new ServiceClient({ baseURL }));
    }
    return this.clients.get(serviceName)!;
  }

  static getVoiceEngineClient(): ServiceClient {
    return this.getClient('voice-engine', process.env.VOICE_ENGINE_URL || 'http://voice-engine:3001');
  }

  static getDialectDetectorClient(): ServiceClient {
    return this.getClient('dialect-detector', process.env.DIALECT_DETECTOR_URL || 'http://dialect-detector:8001');
  }

  static getSchemeMatcherClient(): ServiceClient {
    return this.getClient('scheme-matcher', process.env.SCHEME_MATCHER_URL || 'http://scheme-matcher:8002');
  }

  static getFormGeneratorClient(): ServiceClient {
    return this.getClient('form-generator', process.env.FORM_GENERATOR_URL || 'http://form-generator:3002');
  }

  static getDocumentGuideClient(): ServiceClient {
    return this.getClient('document-guide', process.env.DOCUMENT_GUIDE_URL || 'http://document-guide:8003');
  }

  static getApplicationTrackerClient(): ServiceClient {
    return this.getClient('application-tracker', process.env.APPLICATION_TRACKER_URL || 'http://application-tracker:8004');
  }

  static getUserProfileClient(): ServiceClient {
    return this.getClient('user-profile', process.env.USER_PROFILE_URL || 'http://user-profile:8005');
  }

  static getAccessibilityClient(): ServiceClient {
    return this.getClient('accessibility', process.env.ACCESSIBILITY_URL || 'http://accessibility:3003');
  }
}
