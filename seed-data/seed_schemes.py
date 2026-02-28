#!/usr/bin/env python3
"""
Seed script for loading government scheme data from JSON files.

This script reads scheme definitions from seed-data/schemes/ and can:
1. Load them into the in-memory scheme matcher service
2. Seed them into a Neo4j graph database (if available)

Usage:
    # Print summary of schemes
    python seed-data/seed_schemes.py

    # Seed into Neo4j
    python seed-data/seed_schemes.py --neo4j-uri bolt://localhost:7687 --neo4j-user neo4j --neo4j-password password
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), 'schemes')


def load_schemes_from_json(directory: str = SEED_DATA_DIR) -> List[Dict[str, Any]]:
    """Load all scheme definitions from JSON files in the given directory."""
    schemes = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    schemes.extend(data)
                else:
                    schemes.append(data)
    logger.info(f"Loaded {len(schemes)} schemes from {directory}")
    return schemes


def transform_to_matcher_format(scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a seed data scheme into the format expected by SchemeMatcherService."""
    eligibility = scheme.get('eligibility', {})

    matcher_eligibility = {}
    if eligibility.get('occupation'):
        matcher_eligibility['occupation'] = eligibility['occupation']
    if eligibility.get('income_limit') is not None:
        matcher_eligibility['max_income'] = eligibility['income_limit']
    if eligibility.get('age_min') is not None:
        matcher_eligibility['min_age'] = eligibility['age_min']
    if eligibility.get('age_max') is not None:
        matcher_eligibility['max_age'] = eligibility['age_max']
    if eligibility.get('gender') and eligibility['gender'] != 'all':
        matcher_eligibility['gender'] = [eligibility['gender']]
    if eligibility.get('category'):
        caste_categories = [c for c in eligibility['category'] if c in ('sc', 'st', 'obc')]
        if caste_categories and len(caste_categories) < 6:
            matcher_eligibility['caste'] = caste_categories
    if eligibility.get('area') and eligibility['area'] != 'both':
        matcher_eligibility['area'] = eligibility['area']

    benefits = scheme.get('benefits', {})
    benefit_amount = 0
    amount_str = benefits.get('amount', '')
    import re
    numbers = re.findall(r'[\d,]+', amount_str.replace(',', ''))
    if numbers:
        try:
            benefit_amount = int(numbers[0])
        except ValueError:
            benefit_amount = 0

    return {
        'scheme_id': scheme['id'].upper(),
        'name': scheme['name'],
        'name_hi': scheme.get('name_hi', ''),
        'description': scheme.get('description', ''),
        'eligibility': matcher_eligibility,
        'benefit_amount': benefit_amount,
        'difficulty': 'easy' if benefits.get('type') == 'cash' else 'medium',
        'category': scheme.get('category', 'general'),
        'documents_required': scheme.get('documents_required', []),
        'application_process': scheme.get('application_process', ''),
        'website': scheme.get('website', ''),
        'ministry': scheme.get('ministry', ''),
        'benefits': benefits,
        'related_schemes': [],
        'last_updated': datetime.now().isoformat(),
        'status': scheme.get('status', 'active')
    }


def build_scheme_relationships(schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build related_schemes relationships based on category and eligibility overlap."""
    by_category = {}
    for scheme in schemes:
        cat = scheme.get('category', '')
        by_category.setdefault(cat, []).append(scheme['scheme_id'])

    for scheme in schemes:
        cat = scheme.get('category', '')
        related = [sid for sid in by_category.get(cat, []) if sid != scheme['scheme_id']]
        scheme['related_schemes'] = related[:5]

    return schemes


def seed_neo4j(schemes: List[Dict[str, Any]], uri: str, user: str, password: str):
    """Seed schemes into a Neo4j graph database."""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        logger.error("neo4j package not installed. Run: pip install neo4j")
        return False

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("MATCH (n:Scheme) DETACH DELETE n")
            logger.info("Cleared existing scheme nodes")

            for scheme in schemes:
                session.run(
                    """
                    CREATE (s:Scheme {
                        scheme_id: $scheme_id,
                        name: $name,
                        name_hi: $name_hi,
                        description: $description,
                        category: $category,
                        benefit_amount: $benefit_amount,
                        difficulty: $difficulty,
                        ministry: $ministry,
                        website: $website,
                        status: $status,
                        last_updated: $last_updated
                    })
                    """,
                    scheme_id=scheme['scheme_id'],
                    name=scheme['name'],
                    name_hi=scheme.get('name_hi', ''),
                    description=scheme.get('description', ''),
                    category=scheme.get('category', ''),
                    benefit_amount=scheme.get('benefit_amount', 0),
                    difficulty=scheme.get('difficulty', 'medium'),
                    ministry=scheme.get('ministry', ''),
                    website=scheme.get('website', ''),
                    status=scheme.get('status', 'active'),
                    last_updated=scheme.get('last_updated', '')
                )

            for scheme in schemes:
                for related_id in scheme.get('related_schemes', []):
                    session.run(
                        """
                        MATCH (a:Scheme {scheme_id: $from_id})
                        MATCH (b:Scheme {scheme_id: $to_id})
                        MERGE (a)-[:RELATED_TO]->(b)
                        """,
                        from_id=scheme['scheme_id'],
                        to_id=related_id
                    )

            count = session.run("MATCH (s:Scheme) RETURN count(s) as count").single()['count']
            logger.info(f"Seeded {count} schemes into Neo4j")

        driver.close()
        return True
    except Exception as e:
        logger.error(f"Failed to seed Neo4j: {e}")
        return False


def print_summary(schemes: List[Dict[str, Any]]):
    """Print a summary of loaded schemes."""
    categories = {}
    for s in schemes:
        cat = s.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n{'='*60}")
    print(f"  Gram Sahayak — Scheme Seed Data Summary")
    print(f"{'='*60}")
    print(f"  Total schemes: {len(schemes)}")
    print(f"\n  By category:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat:.<30} {count}")
    print(f"\n  Sample schemes:")
    for s in schemes[:5]:
        print(f"    • {s['scheme_id']}: {s['name']}")
    if len(schemes) > 5:
        print(f"    ... and {len(schemes) - 5} more")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Seed Gram Sahayak scheme data')
    parser.add_argument('--neo4j-uri', help='Neo4j connection URI (e.g., bolt://localhost:7687)')
    parser.add_argument('--neo4j-user', default='neo4j', help='Neo4j username')
    parser.add_argument('--neo4j-password', default='password', help='Neo4j password')
    args = parser.parse_args()

    raw_schemes = load_schemes_from_json()
    if not raw_schemes:
        logger.error("No schemes found. Ensure seed-data/schemes/ contains JSON files.")
        sys.exit(1)

    matcher_schemes = [transform_to_matcher_format(s) for s in raw_schemes]
    matcher_schemes = build_scheme_relationships(matcher_schemes)

    print_summary(matcher_schemes)

    if args.neo4j_uri:
        success = seed_neo4j(matcher_schemes, args.neo4j_uri, args.neo4j_user, args.neo4j_password)
        if success:
            print("✅ Schemes seeded into Neo4j successfully")
        else:
            print("❌ Failed to seed Neo4j")
            sys.exit(1)
    else:
        print("ℹ️  No Neo4j URI provided. Use --neo4j-uri to seed into Neo4j.")
        print("   Schemes are loaded and ready for in-memory use.")


if __name__ == '__main__':
    main()
