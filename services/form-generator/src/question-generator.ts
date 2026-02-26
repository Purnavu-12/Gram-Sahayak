import { FormTemplate, FormSession } from '../../../shared/types';

export class QuestionGenerator {
  detectMissingInformation(session: FormSession, template: FormTemplate): string[] {
    const requiredFields = template.fields.filter(f => f.required);
    const missingFields: string[] = [];
    for (const field of requiredFields) {
      if (!session.formData[field.name]) {
        missingFields.push(field.name);
      }
    }
    return missingFields;
  }

  generateContextAwareQuestion(fieldName: string, session: FormSession, template: FormTemplate): string {
    const field = template.fields.find(f => f.name === fieldName);
    if (!field) {
      return 'Please provide the next information.';
    }
    return `What is your ${field.label}?`;
  }

  optimizeConversationFlow(missingFields: string[], session: FormSession, template: FormTemplate): any {
    return {
      questions: [],
      canGroupQuestions: false,
      suggestedGroupSize: 0
    };
  }
}
