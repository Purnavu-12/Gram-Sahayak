import PDFDocument from 'pdfkit';
import { FormSession, FormTemplate, PDFDocument as PDFDocumentType } from '../../../shared/types';
import * as crypto from 'crypto';

// Type for PDFKit document
type PDFKitDocument = typeof PDFDocument.prototype;

export interface PDFTemplate {
  schemeId: string;
  title: string;
  headerText: string;
  footerText: string;
  layout: PDFLayout;
  signature?: SignatureConfig;
}

export interface PDFLayout {
  pageSize: 'A4' | 'LETTER';
  margins: { top: number; bottom: number; left: number; right: number };
  fontSize: { title: number; heading: number; body: number; footer: number };
  colors: { primary: string; secondary: string; text: string };
}

export interface SignatureConfig {
  enabled: boolean;
  position: { x: number; y: number };
  size: { width: number; height: number };
  includeQRCode: boolean;
}

export interface DigitalSignature {
  hash: string;
  timestamp: Date;
  algorithm: string;
  qrCodeData?: string;
}

export class PDFGenerator {
  private templates: Map<string, PDFTemplate>;

  constructor() {
    this.templates = new Map();
    this.initializeTemplates();
  }

  private initializeTemplates(): void {
    // PM-KISAN template
    this.templates.set('pm-kisan', {
      schemeId: 'pm-kisan',
      title: 'PM-KISAN Application Form',
      headerText: 'Pradhan Mantri Kisan Samman Nidhi Yojana',
      footerText: 'Ministry of Agriculture & Farmers Welfare, Government of India',
      layout: {
        pageSize: 'A4',
        margins: { top: 50, bottom: 50, left: 50, right: 50 },
        fontSize: { title: 18, heading: 14, body: 11, footer: 9 },
        colors: { primary: '#1a5490', secondary: '#f47920', text: '#333333' }
      },
      signature: {
        enabled: true,
        position: { x: 400, y: 700 },
        size: { width: 100, height: 50 },
        includeQRCode: true
      }
    });
  }

  async generatePDF(session: FormSession, template: FormTemplate): Promise<PDFDocumentType> {
    const pdfTemplate = this.templates.get(session.schemeId);
    if (!pdfTemplate) {
      throw new Error(`PDF template not found for scheme: ${session.schemeId}`);
    }

    return new Promise((resolve, reject) => {
      try {
        const doc = new PDFDocument({
          size: pdfTemplate.layout.pageSize,
          margins: pdfTemplate.layout.margins
        });

        const chunks: Buffer[] = [];
        doc.on('data', (chunk: Buffer) => chunks.push(chunk));
        doc.on('end', () => {
          const buffer = Buffer.concat(chunks);
          resolve({
            buffer,
            filename: `${session.schemeId}_${session.userId}_${Date.now()}.pdf`,
            mimeType: 'application/pdf'
          });
        });
        doc.on('error', reject);

        // Generate PDF content
        this.addHeader(doc, pdfTemplate);
        this.addFormContent(doc, session, template, pdfTemplate);
        
        // Add digital signature if enabled
        if (pdfTemplate.signature?.enabled) {
          const signature = this.generateDigitalSignature(session, template);
          this.addSignature(doc, signature, pdfTemplate);
        }

        this.addFooter(doc, pdfTemplate);

        doc.end();
      } catch (error) {
        reject(error);
      }
    });
  }

  private addHeader(doc: any, template: PDFTemplate): void {
    const { layout } = template;
    
    // Add header background
    doc.rect(0, 0, doc.page.width, 80)
       .fill(layout.colors.primary);

    // Add title
    doc.fillColor('#FFFFFF')
       .fontSize(layout.fontSize.title)
       .font('Helvetica-Bold')
       .text(template.title, layout.margins.left, 25, {
         width: doc.page.width - layout.margins.left - layout.margins.right,
         align: 'center'
       });

    // Add header text
    doc.fontSize(layout.fontSize.body)
       .font('Helvetica')
       .text(template.headerText, layout.margins.left, 50, {
         width: doc.page.width - layout.margins.left - layout.margins.right,
         align: 'center'
       });

    // Reset position
    doc.y = 100;
    doc.fillColor(layout.colors.text);
  }

  private addFormContent(
    doc: any,
    session: FormSession,
    template: FormTemplate,
    pdfTemplate: PDFTemplate
  ): void {
    const { layout } = pdfTemplate;
    const startY = doc.y + 20;
    
    doc.fontSize(layout.fontSize.heading)
       .font('Helvetica-Bold')
       .fillColor(layout.colors.primary)
       .text('Application Details', layout.margins.left, startY);

    doc.moveDown(1);

    // Add form fields
    doc.fontSize(layout.fontSize.body)
       .font('Helvetica')
       .fillColor(layout.colors.text);

    for (const field of template.fields) {
      const value = session.formData[field.name];
      if (value !== undefined && value !== null) {
        // Check if we need a new page
        if (doc.y > doc.page.height - 150) {
          doc.addPage();
          doc.y = layout.margins.top;
        }

        // Field label
        doc.font('Helvetica-Bold')
           .text(`${field.label}:`, layout.margins.left, doc.y, {
             continued: false
           });

        // Field value
        doc.font('Helvetica')
           .text(this.formatFieldValue(value, field.type), layout.margins.left + 20, doc.y, {
             width: doc.page.width - layout.margins.left - layout.margins.right - 20
           });

        doc.moveDown(0.5);
      }
    }

    // Add submission info
    doc.moveDown(2);
    doc.fontSize(layout.fontSize.body - 1)
       .fillColor('#666666')
       .text(`Application ID: ${session.sessionId}`, layout.margins.left);
    doc.text(`Submission Date: ${new Date().toLocaleDateString('en-IN')}`, layout.margins.left);
  }

  private formatFieldValue(value: any, fieldType: string): string {
    if (value === null || value === undefined) return 'N/A';

    switch (fieldType) {
      case 'date':
        return new Date(value).toLocaleDateString('en-IN');
      case 'number':
        return value.toString();
      case 'phone':
        return value.toString();
      case 'address':
        if (typeof value === 'object') {
          return Object.values(value).filter(v => v).join(', ');
        }
        return value.toString();
      default:
        return value.toString();
    }
  }

  private generateDigitalSignature(session: FormSession, template: FormTemplate): DigitalSignature {
    // Create hash of form data for verification
    const dataToSign = JSON.stringify({
      sessionId: session.sessionId,
      userId: session.userId,
      schemeId: session.schemeId,
      formData: session.formData,
      timestamp: new Date().toISOString()
    });

    const hash = crypto.createHash('sha256').update(dataToSign).digest('hex');

    // Generate QR code data (simplified - in production, use a proper QR library)
    const qrCodeData = `VERIFY:${hash.substring(0, 16)}:${session.sessionId}`;

    return {
      hash,
      timestamp: new Date(),
      algorithm: 'SHA-256',
      qrCodeData
    };
  }

  private addSignature(
    doc: any,
    signature: DigitalSignature,
    template: PDFTemplate
  ): void {
    if (!template.signature) return;

    const { position, size } = template.signature;
    const { layout } = template;

    // Position signature area
    const signatureY = doc.page.height - layout.margins.bottom - 100;
    doc.y = signatureY;

    // Add signature box
    doc.rect(position.x, signatureY, size.width, size.height)
       .stroke('#CCCCCC');

    // Add signature label
    doc.fontSize(layout.fontSize.body - 2)
       .fillColor(layout.colors.text)
       .text('Digital Signature', position.x, signatureY - 15);

    // Add verification hash (truncated)
    doc.fontSize(layout.fontSize.footer)
       .fillColor('#666666')
       .text(`Hash: ${signature.hash.substring(0, 20)}...`, position.x, signatureY + size.height + 5);

    // Add timestamp
    doc.text(`Signed: ${signature.timestamp.toLocaleString('en-IN')}`, position.x, signatureY + size.height + 18);

    // Add QR code placeholder (in production, use qrcode library)
    if (template.signature.includeQRCode && signature.qrCodeData) {
      const qrX = position.x - 80;
      const qrSize = 60;
      
      doc.rect(qrX, signatureY, qrSize, qrSize)
         .stroke('#CCCCCC');
      
      doc.fontSize(8)
         .text('QR Code', qrX, signatureY + qrSize + 5, {
           width: qrSize,
           align: 'center'
         });
    }
  }

  private addFooter(doc: any, template: PDFTemplate): void {
    const { layout } = template;
    const footerY = doc.page.height - layout.margins.bottom + 20;

    // Add footer line
    doc.moveTo(layout.margins.left, footerY)
       .lineTo(doc.page.width - layout.margins.right, footerY)
       .stroke('#CCCCCC');

    // Add footer text
    doc.fontSize(layout.fontSize.footer)
       .fillColor('#666666')
       .text(template.footerText, layout.margins.left, footerY + 10, {
         width: doc.page.width - layout.margins.left - layout.margins.right,
         align: 'center'
       });

    // Add page number
    const pageNumber = doc.bufferedPageRange().count;
    doc.text(`Page ${pageNumber}`, layout.margins.left, footerY + 25, {
      width: doc.page.width - layout.margins.left - layout.margins.right,
      align: 'center'
    });
  }

  addTemplate(template: PDFTemplate): void {
    this.templates.set(template.schemeId, template);
  }

  getTemplate(schemeId: string): PDFTemplate | undefined {
    return this.templates.get(schemeId);
  }

  validateSignature(hash: string, sessionData: any): boolean {
    const dataToVerify = JSON.stringify(sessionData);
    const computedHash = crypto.createHash('sha256').update(dataToVerify).digest('hex');
    return hash === computedHash;
  }
}
