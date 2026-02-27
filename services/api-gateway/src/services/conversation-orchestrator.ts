import { ServiceClientFactory } from '../../../../shared/service-client';
import Redis from 'redis';

export interface ConversationState {
  sessionId: string;
  userId: string;
  currentStage: ConversationStage;
  detectedDialect?: string;
  detectedLanguage?: string;
  userProfile?: any;
  eligibleSchemes?: any[];
  selectedScheme?: any;
  formSessionId?: string;
  documentRequirements?: any[];
  applicationId?: string;
  conversationHistory: ConversationMessage[];
  metadata: {
    startTime: Date;
    lastActivity: Date;
    errorCount: number;
    retryCount: number;
  };
}

export enum ConversationStage {
  INITIAL = 'initial',
  DIALECT_DETECTION = 'dialect_detection',
  PROFILE_COLLECTION = 'profile_collection',
  SCHEME_DISCOVERY = 'scheme_discovery',
  SCHEME_SELECTION = 'scheme_selection',
  FORM_FILLING = 'form_filling',
  DOCUMENT_GUIDANCE = 'document_guidance',
  APPLICATION_SUBMISSION = 'application_submission',
  TRACKING = 'tracking',
  COMPLETED = 'completed',
  ERROR = 'error',
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    service?: string;
    confidence?: number;
    language?: string;
  };
}

export interface ConversationInput {
  sessionId?: string;
  userId: string;
  audioData?: ArrayBuffer;
  textInput?: string;
  preferredLanguage?: string;
}

export interface ConversationOutput {
  sessionId: string;
  stage: ConversationStage;
  response: {
    text: string;
    audioUrl?: string;
    visualData?: any;
  };
  nextActions?: string[];
  error?: {
    code: string;
    message: string;
    recoverable: boolean;
  };
}

export class ConversationOrchestrator {
  private redisClient: any;
  private readonly SESSION_TTL = 3600; // 1 hour

  constructor() {
    this.initializeRedis();
  }

  private async initializeRedis() {
    this.redisClient = Redis.createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379',
    });

    this.redisClient.on('error', (err: Error) => {
      console.error('Redis Client Error', err);
    });

    await this.redisClient.connect();
  }

  /**
   * Main entry point for processing conversation input
   */
  async processConversation(input: ConversationInput): Promise<ConversationOutput> {
    try {
      // Get or create conversation state
      const state = await this.getOrCreateState(input);

      // Process based on current stage
      let output: ConversationOutput;

      switch (state.currentStage) {
        case ConversationStage.INITIAL:
        case ConversationStage.DIALECT_DETECTION:
          output = await this.handleDialectDetection(state, input);
          break;

        case ConversationStage.PROFILE_COLLECTION:
          output = await this.handleProfileCollection(state, input);
          break;

        case ConversationStage.SCHEME_DISCOVERY:
          output = await this.handleSchemeDiscovery(state, input);
          break;

        case ConversationStage.SCHEME_SELECTION:
          output = await this.handleSchemeSelection(state, input);
          break;

        case ConversationStage.FORM_FILLING:
          output = await this.handleFormFilling(state, input);
          break;

        case ConversationStage.DOCUMENT_GUIDANCE:
          output = await this.handleDocumentGuidance(state, input);
          break;

        case ConversationStage.APPLICATION_SUBMISSION:
          output = await this.handleApplicationSubmission(state, input);
          break;

        case ConversationStage.TRACKING:
          output = await this.handleTracking(state, input);
          break;

        default:
          throw new Error(`Unknown conversation stage: ${state.currentStage}`);
      }

      // Update state
      await this.saveState(state);

      return output;
    } catch (error: any) {
      return this.handleError(error, input.sessionId);
    }
  }

  private async getOrCreateState(input: ConversationInput): Promise<ConversationState> {
    if (input.sessionId) {
      const existingState = await this.loadState(input.sessionId);
      if (existingState) {
        existingState.metadata.lastActivity = new Date();
        return existingState;
      }
    }

    // Create new state
    const sessionId = input.sessionId || this.generateSessionId();
    return {
      sessionId,
      userId: input.userId,
      currentStage: ConversationStage.INITIAL,
      conversationHistory: [],
      metadata: {
        startTime: new Date(),
        lastActivity: new Date(),
        errorCount: 0,
        retryCount: 0,
      },
    };
  }

  private async handleDialectDetection(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    // Step 1: Convert speech to text
    const voiceClient = ServiceClientFactory.getVoiceEngineClient();
    let transcription: any;

    if (input.audioData) {
      transcription = await voiceClient.post('/transcribe', {
        audio: input.audioData,
        language: input.preferredLanguage,
      });
    } else if (input.textInput) {
      transcription = { text: input.textInput };
    } else {
      throw new Error('No input provided');
    }

    // Step 2: Detect dialect
    const dialectClient = ServiceClientFactory.getDialectDetectorClient();
    const dialectResult: any = await dialectClient.post('/detect', {
      text: transcription.text,
      audioFeatures: input.audioData ? { /* audio features */ } : undefined,
    });

    // Update state
    state.detectedDialect = dialectResult.dialect;
    state.detectedLanguage = dialectResult.language;
    state.currentStage = ConversationStage.PROFILE_COLLECTION;

    // Add to conversation history
    state.conversationHistory.push({
      role: 'user',
      content: transcription.text,
      timestamp: new Date(),
      metadata: {
        language: dialectResult.language,
        confidence: dialectResult.confidence,
      },
    });

    // Generate response
    const responseText = this.generateWelcomeMessage(dialectResult.language);
    state.conversationHistory.push({
      role: 'assistant',
      content: responseText,
      timestamp: new Date(),
    });

    // Synthesize speech
    const audioResponse: any = await voiceClient.post('/synthesize', {
      text: responseText,
      dialect: state.detectedDialect,
      language: state.detectedLanguage,
    });

    return {
      sessionId: state.sessionId,
      stage: state.currentStage,
      response: {
        text: responseText,
        audioUrl: audioResponse.audioUrl,
      },
      nextActions: ['provide_profile_information'],
    };
  }

  private async handleProfileCollection(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    // Get user profile or create new one
    const profileClient = ServiceClientFactory.getUserProfileClient();

    try {
      const profile = await profileClient.get(`/profiles/${state.userId}`);
      state.userProfile = profile;
      state.currentStage = ConversationStage.SCHEME_DISCOVERY;

      return {
        sessionId: state.sessionId,
        stage: state.currentStage,
        response: {
          text: 'I have your profile. Let me find schemes for you.',
        },
        nextActions: ['discover_schemes'],
      };
    } catch (error: any) {
      // Profile doesn't exist, need to collect information
      // This would involve a multi-turn conversation to collect profile data
      // For now, we'll create a basic profile

      const voiceClient = ServiceClientFactory.getVoiceEngineClient();
      const transcription: any = input.audioData
        ? await voiceClient.post('/transcribe', { audio: input.audioData })
        : { text: input.textInput };

      // Extract profile information from conversation
      // In a real implementation, this would use NLP to extract entities
      const profileData = await this.extractProfileData(transcription.text, state);

      if (profileData.isComplete) {
        // Create profile
        const newProfile = await profileClient.post('/profiles', {
          userId: state.userId,
          ...profileData.data,
        });

        state.userProfile = newProfile;
        state.currentStage = ConversationStage.SCHEME_DISCOVERY;

        return {
          sessionId: state.sessionId,
          stage: state.currentStage,
          response: {
            text: 'Thank you. Let me find schemes for you.',
          },
          nextActions: ['discover_schemes'],
        };
      } else {
        // Need more information
        return {
          sessionId: state.sessionId,
          stage: state.currentStage,
          response: {
            text: profileData.nextQuestion || 'Please provide more information.',
          },
          nextActions: ['provide_profile_information'],
        };
      }
    }
  }

  private async handleSchemeDiscovery(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    const schemeClient = ServiceClientFactory.getSchemeMatcherClient();

    // Find eligible schemes
    const schemes: any = await schemeClient.post('/match', {
      userProfile: state.userProfile,
    });

    state.eligibleSchemes = schemes.matches;
    state.currentStage = ConversationStage.SCHEME_SELECTION;

    // Generate response with top schemes
    const responseText = this.generateSchemeListMessage(schemes.matches, state.detectedLanguage!);

    return {
      sessionId: state.sessionId,
      stage: state.currentStage,
      response: {
        text: responseText,
        visualData: {
          schemes: schemes.matches.slice(0, 5),
        },
      },
      nextActions: ['select_scheme', 'get_more_schemes'],
    };
  }

  private async handleSchemeSelection(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    // Parse user selection from input
    const voiceClient = ServiceClientFactory.getVoiceEngineClient();
    const transcription: any = input.audioData
      ? await voiceClient.post('/transcribe', { audio: input.audioData })
      : { text: input.textInput };

    // Extract scheme selection
    const selectedScheme = await this.extractSchemeSelection(
      transcription.text,
      state.eligibleSchemes!
    );

    if (!selectedScheme) {
      return {
        sessionId: state.sessionId,
        stage: state.currentStage,
        response: {
          text: 'I did not understand which scheme you want. Please select again.',
        },
        nextActions: ['select_scheme'],
      };
    }

    state.selectedScheme = selectedScheme;
    state.currentStage = ConversationStage.FORM_FILLING;

    // Start form filling session
    const formClient = ServiceClientFactory.getFormGeneratorClient();
    const formSession: any = await formClient.post('/forms/start', {
      schemeId: selectedScheme.schemeId,
      userId: state.userId,
    });

    state.formSessionId = formSession.sessionId;

    return {
      sessionId: state.sessionId,
      stage: state.currentStage,
      response: {
        text: `Great! Let's apply for ${selectedScheme.name}. ${formSession.firstQuestion}`,
      },
      nextActions: ['answer_form_question'],
    };
  }

  private async handleFormFilling(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    const voiceClient = ServiceClientFactory.getVoiceEngineClient();
    const formClient = ServiceClientFactory.getFormGeneratorClient();

    // Get user response
    const transcription: any = input.audioData
      ? await voiceClient.post('/transcribe', { audio: input.audioData })
      : { text: input.textInput };

    // Process form response
    const formUpdate: any = await formClient.post(`/forms/${state.formSessionId}/respond`, {
      response: transcription.text,
    });

    if (formUpdate.isComplete) {
      // Form is complete, move to document guidance
      state.currentStage = ConversationStage.DOCUMENT_GUIDANCE;

      return {
        sessionId: state.sessionId,
        stage: state.currentStage,
        response: {
          text: 'Form completed! Now let me tell you about required documents.',
        },
        nextActions: ['get_document_guidance'],
      };
    } else {
      // Continue form filling
      return {
        sessionId: state.sessionId,
        stage: state.currentStage,
        response: {
          text: formUpdate.nextQuestion,
          visualData: {
            progress: formUpdate.progress,
            currentField: formUpdate.currentField,
          },
        },
        nextActions: ['answer_form_question'],
      };
    }
  }

  private async handleDocumentGuidance(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    const documentClient = ServiceClientFactory.getDocumentGuideClient();

    // Get document requirements
    const documents: any = await documentClient.post('/documents/requirements', {
      schemeId: state.selectedScheme!.schemeId,
      language: state.detectedLanguage,
    });

    state.documentRequirements = documents.requirements;
    state.currentStage = ConversationStage.APPLICATION_SUBMISSION;

    const responseText = this.generateDocumentGuidanceMessage(
      documents.requirements,
      state.detectedLanguage!
    );

    return {
      sessionId: state.sessionId,
      stage: state.currentStage,
      response: {
        text: responseText,
        visualData: {
          documents: documents.requirements,
        },
      },
      nextActions: ['submit_application', 'get_document_help'],
    };
  }

  private async handleApplicationSubmission(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    const formClient = ServiceClientFactory.getFormGeneratorClient();
    const trackerClient = ServiceClientFactory.getApplicationTrackerClient();

    // Generate PDF
    const pdf: any = await formClient.post(`/forms/${state.formSessionId}/generate-pdf`);

    // Submit application
    const submission: any = await trackerClient.post('/applications/submit', {
      userId: state.userId,
      schemeId: state.selectedScheme!.schemeId,
      formData: pdf.formData,
      pdfUrl: pdf.pdfUrl,
    });

    state.applicationId = submission.applicationId;
    state.currentStage = ConversationStage.TRACKING;

    return {
      sessionId: state.sessionId,
      stage: state.currentStage,
      response: {
        text: `Application submitted! Your reference number is ${submission.referenceNumber}. Expected processing time is ${submission.expectedDays} days.`,
        visualData: {
          applicationId: submission.applicationId,
          referenceNumber: submission.referenceNumber,
          expectedDays: submission.expectedDays,
        },
      },
      nextActions: ['track_application', 'start_new_application'],
    };
  }

  private async handleTracking(
    state: ConversationState,
    input: ConversationInput
  ): Promise<ConversationOutput> {
    const trackerClient = ServiceClientFactory.getApplicationTrackerClient();

    // Get application status
    const status: any = await trackerClient.get(`/applications/${state.applicationId}/status`);

    return {
      sessionId: state.sessionId,
      stage: state.currentStage,
      response: {
        text: `Your application status is: ${status.status}. ${status.message}`,
        visualData: {
          status: status.status,
          timeline: status.timeline,
          nextSteps: status.nextSteps,
        },
      },
      nextActions: ['check_again_later', 'start_new_application'],
    };
  }

  private async handleError(error: Error, sessionId?: string): Promise<ConversationOutput> {
    console.error('Conversation error:', error);

    return {
      sessionId: sessionId || 'error',
      stage: ConversationStage.ERROR,
      response: {
        text: 'I encountered an error. Please try again.',
      },
      error: {
        code: 'CONVERSATION_ERROR',
        message: error.message,
        recoverable: true,
      },
    };
  }

  // Helper methods

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateWelcomeMessage(language: string): string {
    // In a real implementation, this would use proper i18n
    return 'Welcome to Gram Sahayak! I will help you find and apply for government schemes. Let me know about yourself.';
  }

  private generateSchemeListMessage(schemes: any[], language: string): string {
    const topSchemes = schemes.slice(0, 3);
    const schemeNames = topSchemes.map((s, i) => `${i + 1}. ${s.name}`).join(', ');
    return `I found ${schemes.length} schemes for you. Top matches are: ${schemeNames}. Which one interests you?`;
  }

  private generateDocumentGuidanceMessage(documents: any[], language: string): string {
    const docList = documents.map((d, i) => `${i + 1}. ${d.name}`).join(', ');
    return `You will need these documents: ${docList}. Do you have these documents ready?`;
  }

  private async extractProfileData(text: string, state: ConversationState): Promise<any> {
    // Simplified profile extraction
    // In a real implementation, this would use NLP/NER
    return {
      isComplete: false,
      nextQuestion: 'What is your age?',
      data: {},
    };
  }

  private async extractSchemeSelection(text: string, schemes: any[]): Promise<any> {
    // Simplified scheme selection
    // In a real implementation, this would use NLP to understand user intent
    const lowerText = text.toLowerCase();

    for (const scheme of schemes) {
      if (lowerText.includes(scheme.name.toLowerCase())) {
        return scheme;
      }
    }

    // Try to match by number
    const match = text.match(/\d+/);
    if (match) {
      const index = parseInt(match[0]) - 1;
      if (index >= 0 && index < schemes.length) {
        return schemes[index];
      }
    }

    return null;
  }

  private async loadState(sessionId: string): Promise<ConversationState | null> {
    try {
      const data = await this.redisClient.get(`conversation:${sessionId}`);
      if (!data) return null;

      const state = JSON.parse(data);
      // Convert date strings back to Date objects
      state.metadata.startTime = new Date(state.metadata.startTime);
      state.metadata.lastActivity = new Date(state.metadata.lastActivity);
      state.conversationHistory = state.conversationHistory.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }));

      return state;
    } catch (error) {
      console.error('Error loading state:', error);
      return null;
    }
  }

  private async saveState(state: ConversationState): Promise<void> {
    try {
      await this.redisClient.setEx(
        `conversation:${state.sessionId}`,
        this.SESSION_TTL,
        JSON.stringify(state)
      );
    } catch (error) {
      console.error('Error saving state:', error);
      throw error;
    }
  }

  async getConversationHistory(sessionId: string): Promise<ConversationMessage[]> {
    const state = await this.loadState(sessionId);
    return state?.conversationHistory || [];
  }

  async deleteConversation(sessionId: string): Promise<void> {
    await this.redisClient.del(`conversation:${sessionId}`);
  }
}
