# Scheme Matcher Service

The Scheme Matcher Service is a core component of the Gram Sahayak system that matches rural citizens with eligible government welfare schemes. It implements intelligent eligibility evaluation, priority ranking, and alternative scheme suggestions.

## Features

### 1. Graph Database for Scheme Relationships (Task 5.1)
- **Neo4j Integration**: Optional graph database support for complex scheme relationships
- **Relationship Mapping**: Tracks related schemes for better alternative suggestions
- **Fallback Support**: Works with in-memory database when Neo4j is unavailable

### 2. Multi-Criteria Eligibility Evaluation (Task 5.2)
Evaluates eligibility based on multiple criteria as per Requirement 3.2:
- **Income**: Annual income limits
- **Caste**: SC/ST/OBC/General categories
- **Age**: Minimum and maximum age requirements
- **Gender**: Gender-specific schemes
- **Occupation**: Farmer, laborer, student, etc.
- **Location**: State/district-specific schemes
- **Land Ownership**: Agricultural land requirements
- **Marital Status**: Widow, married, etc.

### 3. Scheme Database Management (Task 5.4)
- **Real-time Updates**: Update scheme information dynamically (Requirement 3.4)
- **Update Tracking**: Logs all scheme changes with timestamps
- **New Scheme Addition**: Add new schemes to the database
- **Update Status Monitoring**: Track recent updates and database freshness

### 4. Alternative Scheme Suggestions (Task 5.6)
When users are ineligible for requested schemes (Requirement 3.5):
- **Category-based Matching**: Suggests schemes in the same category
- **Relationship-based Matching**: Uses graph relationships to find related schemes
- **Eligibility-aware**: Only suggests schemes the user qualifies for
- **Reason Explanation**: Provides clear reasons for each suggestion

### 5. Priority Ranking (Requirement 3.3)
Ranks schemes by:
- **Benefit Amount**: Higher financial benefits ranked higher
- **Application Ease**: Easy applications prioritized over complex ones
- **Match Score**: Confidence in eligibility match
- **User Preferences**: Customizable ranking based on user priorities

## Database Schema

### In-Memory Scheme Structure
```python
{
    "scheme_id": "PM-KISAN",
    "name": "PM-KISAN",
    "description": "Direct income support to farmers",
    "eligibility": {
        "occupation": ["farmer"],
        "land_ownership": True,
        "max_income": 200000
    },
    "benefit_amount": 6000,
    "difficulty": "easy",
    "category": "agriculture",
    "related_schemes": ["MGNREGA", "PM-FASAL-BIMA"],
    "last_updated": "2024-01-01T00:00:00"
}
```

### Neo4j Graph Structure (Optional)
- **Nodes**: Scheme nodes with properties
- **Relationships**: `RELATED_TO` edges between schemes
- **Queries**: Cypher queries for relationship traversal

## API Endpoints

### Find Eligible Schemes
```
POST /schemes/find
Body: UserProfile
Returns: List[SchemeMatch]
```

### Evaluate Eligibility
```
POST /schemes/{scheme_id}/eligibility
Body: UserProfile
Returns: EligibilityResult
```

### Get Priority Ranking
```
POST /schemes/rank
Body: { schemes: List[SchemeMatch], preferences: UserPreferences }
Returns: List[RankedScheme]
```

### Suggest Alternatives
```
POST /schemes/{scheme_id}/alternatives
Body: UserProfile
Returns: List[SchemeMatch]
```

### Update Scheme Database
```
POST /schemes/update
Body: List[SchemeUpdate]
Returns: { status: "success", updated_count: number }
```

### Get Update Status
```
GET /schemes/status
Returns: { last_update_time, total_schemes, recent_updates, update_log }
```

## Installation

```bash
cd services/scheme-matcher
pip install -r requirements.txt
```

### Optional: Neo4j Setup
```bash
# Install Neo4j (optional)
# Configure connection in environment variables:
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
```

## Running the Service

```bash
# Development mode
uvicorn main:app --reload --port 8002

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8002
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scheme_matcher_comprehensive.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Current Scheme Database

The service includes 7 pre-configured government schemes:

1. **PM-KISAN**: Direct income support for farmers (₹6,000/year)
2. **MGNREGA**: Employment guarantee scheme (₹8,000/year)
3. **PM-FASAL-BIMA**: Crop insurance scheme (₹15,000/year)
4. **Widow Pension**: Financial support for widows (₹3,000/year)
5. **Old Age Pension**: Pension for senior citizens (₹2,400/year)
6. **SC/ST Scholarship**: Educational support for SC/ST students (₹12,000/year)
7. **OBC Scholarship**: Educational support for OBC students (₹10,000/year)

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 3.1**: Identifies all potentially eligible schemes based on demographic information
- **Requirement 3.2**: Multi-criteria evaluation (income, caste, age, gender, occupation, location)
- **Requirement 3.3**: Priority ranking by benefit amount and application ease
- **Requirement 3.4**: Scheme database updates within 24 hours (tracked via update logs)
- **Requirement 3.5**: Alternative scheme suggestions for ineligible users

## Architecture Notes

### Design Decisions

1. **Hybrid Database Approach**: Supports both in-memory and Neo4j graph database for flexibility
2. **Async/Await Pattern**: All methods are async for better scalability
3. **Confidence Scoring**: Provides confidence levels for eligibility matches
4. **Missing Information Detection**: Identifies incomplete user profiles
5. **Update Logging**: Tracks all scheme changes for audit and monitoring

### Performance Considerations

- In-memory database for fast lookups
- Graph database for complex relationship queries
- Efficient filtering and ranking algorithms
- Minimal external dependencies

### Future Enhancements

- Integration with myScheme API for real-time government data
- Machine learning for benefit prediction
- Advanced similarity matching for alternatives
- Multi-language scheme descriptions
- Document requirement mapping
- Application difficulty scoring based on historical data

## License

Part of the Gram Sahayak project - Voice-first AI assistant for rural India.
