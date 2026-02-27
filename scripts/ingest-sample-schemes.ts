/**
 * Sample Scheme Ingestion Script
 * Loads sample schemes into Bedrock Knowledge Base
 * Usage: npx ts-node scripts/ingest-sample-schemes.ts
 */

import { KBIngestionPipeline } from '../shared/bedrock/kb-ingestion-pipeline';
import { BedrockAgentWrapper } from '../shared/bedrock/bedrock-agent-wrapper';
import { loadBedrockConfig } from '../shared/bedrock/bedrock-config';
import { SchemeData } from '../shared/types/bedrock';
import * as fs from 'fs';
import * as path from 'path';

async function main() {
  console.log('=== Gram Sahayak Sample Scheme Ingestion ===\n');

  // Load configuration
  const config = loadBedrockConfig();
  console.log(`Bedrock enabled: ${config.enabled}`);
  console.log(`Region: ${config.region}`);
  console.log(`Knowledge Base ID: ${config.knowledgeBase.kbId || '(not configured)'}\n`);

  // Load sample schemes
  const schemesPath = path.join(__dirname, '..', 'shared', 'bedrock', 'sample-schemes.json');
  const rawData = fs.readFileSync(schemesPath, 'utf-8');
  const data = JSON.parse(rawData);
  const schemes: SchemeData[] = data.schemes;

  console.log(`Loaded ${schemes.length} sample schemes from ${schemesPath}`);
  console.log(`Metadata: v${data.metadata.version}, languages: ${data.metadata.languages.join(', ')}\n`);

  // Initialize pipeline
  const wrapper = new BedrockAgentWrapper(config);
  const pipeline = new KBIngestionPipeline(wrapper);

  // Validate all schemes first
  console.log('--- Validation Phase ---');
  let validCount = 0;
  for (const scheme of schemes) {
    const validation = pipeline.validateScheme(scheme);
    if (validation.valid) {
      validCount++;
      console.log(`  ✓ ${scheme.schemeId}: ${scheme.name.en}`);
    } else {
      console.log(`  ✗ ${scheme.schemeId}: ${validation.errors.join(', ')}`);
    }
    if (validation.warnings.length > 0) {
      console.log(`    ⚠ ${validation.warnings.join(', ')}`);
    }
  }
  console.log(`\nValidation: ${validCount}/${schemes.length} schemes valid\n`);

  // Ingest schemes
  console.log('--- Ingestion Phase ---');
  const result = await pipeline.ingestSchemes(schemes);

  console.log(`\n=== Ingestion Complete ===`);
  console.log(`  Success: ${result.successCount}`);
  console.log(`  Failures: ${result.failureCount}`);
  console.log(`  Duration: ${result.duration}ms`);

  if (result.errors.length > 0) {
    console.log('\nErrors:');
    for (const err of result.errors) {
      console.log(`  - ${err.schemeId}: ${err.error}`);
    }
  }

  console.log('\nDone!');
}

main().catch(console.error);
