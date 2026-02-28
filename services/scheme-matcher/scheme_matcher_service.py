from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import os

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    Driver = None

try:
    from external_api_integration import ExternalAPIIntegration
    API_INTEGRATION_AVAILABLE = True
except ImportError:
    API_INTEGRATION_AVAILABLE = False
    ExternalAPIIntegration = None

try:
    from data_freshness_monitor import DataFreshnessMonitor, FreshnessAlert
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    DataFreshnessMonitor = None
    FreshnessAlert = None

logger = logging.getLogger(__name__)


class SchemeMatcherService:
    """
    Scheme Matcher Service Implementation
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    
    Features:
    - Graph database for complex scheme relationships
    - Multi-criteria eligibility evaluation
    - Real-time scheme database updates
    - Alternative scheme suggestions
    """

    def __init__(self, neo4j_uri: Optional[str] = None, neo4j_user: Optional[str] = None, neo4j_password: Optional[str] = None):
        self.schemes_db = self._initialize_schemes()
        self.scheme_updates_log = []
        self.last_update_time = datetime.now()
        
        # Initialize Neo4j connection if available
        self.neo4j_driver: Optional[Driver] = None
        if NEO4J_AVAILABLE and neo4j_uri:
            try:
                self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                self._initialize_graph_database()
                logger.info("Neo4j graph database initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4j: {e}. Using in-memory database.")
                self.neo4j_driver = None  # Ensure driver is None on failure
        else:
            logger.info("Using in-memory scheme database")
        
        # Initialize external API integration (Requirement 3.4)
        self.api_integration: Optional[ExternalAPIIntegration] = None
        if API_INTEGRATION_AVAILABLE:
            self.api_integration = ExternalAPIIntegration()
            logger.info("External API integration initialized")
        
        # Initialize data freshness monitor (Requirement 3.4)
        self.freshness_monitor: Optional[DataFreshnessMonitor] = None
        if MONITORING_AVAILABLE:
            self.freshness_monitor = DataFreshnessMonitor()
            # Register default alert callback
            self.freshness_monitor.register_alert_callback(self._handle_freshness_alert)
            logger.info("Data freshness monitoring initialized")

    def _initialize_schemes(self) -> List[Dict[str, Any]]:
        """Initialize government schemes database.
        
        Loads from seed-data/schemes/ JSON files when LOAD_SEED_DATA env var is set,
        otherwise uses the built-in sample schemes for backward compatibility.
        """
        if os.environ.get('LOAD_SEED_DATA', '').lower() in ('1', 'true', 'yes'):
            seed_schemes = self._load_seed_data()
            if seed_schemes:
                logger.info(f"Loaded {len(seed_schemes)} schemes from seed data")
                return seed_schemes
        
        return self._builtin_schemes()

    def _builtin_schemes(self) -> List[Dict[str, Any]]:
        """Built-in sample schemes for development and testing."""
        return [
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
                "last_updated": datetime.now().isoformat()
            },
            {
                "scheme_id": "MGNREGA",
                "name": "MGNREGA",
                "description": "Employment guarantee scheme",
                "eligibility": {
                    "occupation": ["laborer", "farmer", "unemployed"],
                    "min_age": 18
                },
                "benefit_amount": 8000,
                "difficulty": "medium",
                "category": "employment",
                "related_schemes": ["PM-KISAN"],
                "last_updated": datetime.now().isoformat()
            },
            {
                "scheme_id": "PM-FASAL-BIMA",
                "name": "PM-FASAL-BIMA",
                "description": "Crop insurance scheme",
                "eligibility": {
                    "occupation": ["farmer"],
                    "land_ownership": True
                },
                "benefit_amount": 15000,
                "difficulty": "medium",
                "category": "agriculture",
                "related_schemes": ["PM-KISAN"],
                "last_updated": datetime.now().isoformat()
            },
            {
                "scheme_id": "WIDOW-PENSION",
                "name": "Widow Pension Scheme",
                "description": "Financial support for widows",
                "eligibility": {
                    "gender": ["female"],
                    "marital_status": ["widow"],
                    "max_income": 100000
                },
                "benefit_amount": 3000,
                "difficulty": "easy",
                "category": "social_welfare",
                "related_schemes": ["OLD-AGE-PENSION"],
                "last_updated": datetime.now().isoformat()
            },
            {
                "scheme_id": "OLD-AGE-PENSION",
                "name": "Old Age Pension",
                "description": "Pension for senior citizens",
                "eligibility": {
                    "min_age": 60,
                    "max_income": 120000
                },
                "benefit_amount": 2400,
                "difficulty": "easy",
                "category": "social_welfare",
                "related_schemes": ["WIDOW-PENSION"],
                "last_updated": datetime.now().isoformat()
            },
            {
                "scheme_id": "SC-ST-SCHOLARSHIP",
                "name": "SC/ST Scholarship",
                "description": "Educational support for SC/ST students",
                "eligibility": {
                    "caste": ["sc", "st"],
                    "occupation": ["student"],
                    "max_age": 30
                },
                "benefit_amount": 12000,
                "difficulty": "medium",
                "category": "education",
                "related_schemes": ["OBC-SCHOLARSHIP"],
                "last_updated": datetime.now().isoformat()
            },
            {
                "scheme_id": "OBC-SCHOLARSHIP",
                "name": "OBC Scholarship",
                "description": "Educational support for OBC students",
                "eligibility": {
                    "caste": ["obc"],
                    "occupation": ["student"],
                    "max_age": 30,
                    "max_income": 150000
                },
                "benefit_amount": 10000,
                "difficulty": "medium",
                "category": "education",
                "related_schemes": ["SC-ST-SCHOLARSHIP"],
                "last_updated": datetime.now().isoformat()
            }
        ]

    def _load_seed_data(self) -> Optional[List[Dict[str, Any]]]:
        """Load scheme data from seed-data/schemes/ JSON files."""
        import re
        
        # Look for seed-data relative to service dir or project root
        service_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(service_dir, '..', '..', 'seed-data', 'schemes'),
            os.path.join(os.getcwd(), 'seed-data', 'schemes'),
        ]
        
        seed_dir = None
        for path in possible_paths:
            resolved = os.path.realpath(path)
            if os.path.isdir(resolved):
                seed_dir = resolved
                break
        
        if not seed_dir:
            return None
        
        schemes = []
        for filename in sorted(os.listdir(seed_dir)):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(seed_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        transformed = self._transform_seed_scheme(item)
                        schemes.append(transformed)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load {filename}: {e}")
        
        if not schemes:
            return None
        
        # Build category-based relationships
        by_category: Dict[str, List[str]] = {}
        for s in schemes:
            by_category.setdefault(s.get('category', ''), []).append(s['scheme_id'])
        for s in schemes:
            cat = s.get('category', '')
            s['related_schemes'] = [sid for sid in by_category.get(cat, []) if sid != s['scheme_id']][:5]
        
        return schemes

    def _transform_seed_scheme(self, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a seed-data JSON scheme into matcher format."""
        import re
        eligibility = scheme.get('eligibility', {})
        
        matcher_elig: Dict[str, Any] = {}
        if eligibility.get('occupation'):
            matcher_elig['occupation'] = eligibility['occupation']
        if eligibility.get('income_limit') is not None:
            matcher_elig['max_income'] = eligibility['income_limit']
        if eligibility.get('age_min') is not None:
            matcher_elig['min_age'] = eligibility['age_min']
        if eligibility.get('age_max') is not None:
            matcher_elig['max_age'] = eligibility['age_max']
        if eligibility.get('gender') and eligibility['gender'] != 'all':
            matcher_elig['gender'] = [eligibility['gender']]
        if eligibility.get('category'):
            caste_cats = [c for c in eligibility['category'] if c in ('sc', 'st', 'obc')]
            if caste_cats and len(caste_cats) < 6:
                matcher_elig['caste'] = caste_cats
        if eligibility.get('area') and eligibility['area'] != 'both':
            matcher_elig['area'] = eligibility['area']
        
        benefits = scheme.get('benefits', {})
        benefit_amount = 0
        amount_str = benefits.get('amount', '')
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
            'eligibility': matcher_elig,
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
    
    def _initialize_graph_database(self):
        """Initialize Neo4j graph database with scheme relationships"""
        if not self.neo4j_driver:
            return
        
        with self.neo4j_driver.session() as session:
            # Create scheme nodes
            for scheme in self.schemes_db:
                session.run(
                    """
                    MERGE (s:Scheme {scheme_id: $scheme_id})
                    SET s.name = $name,
                        s.description = $description,
                        s.benefit_amount = $benefit_amount,
                        s.difficulty = $difficulty,
                        s.category = $category,
                        s.last_updated = $last_updated
                    """,
                    scheme_id=scheme["scheme_id"],
                    name=scheme["name"],
                    description=scheme["description"],
                    benefit_amount=scheme["benefit_amount"],
                    difficulty=scheme["difficulty"],
                    category=scheme["category"],
                    last_updated=scheme["last_updated"]
                )
            
            # Create relationships between related schemes
            for scheme in self.schemes_db:
                for related_id in scheme.get("related_schemes", []):
                    session.run(
                        """
                        MATCH (s1:Scheme {scheme_id: $scheme_id})
                        MATCH (s2:Scheme {scheme_id: $related_id})
                        MERGE (s1)-[:RELATED_TO]->(s2)
                        """,
                        scheme_id=scheme["scheme_id"],
                        related_id=related_id
                    )

    async def find_eligible_schemes(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find all schemes user is potentially eligible for
        Validates: Requirements 3.1, 3.2, 3.3
        """
        eligible_schemes = []

        for scheme in self.schemes_db:
            eligibility = await self.evaluate_eligibility(scheme["scheme_id"], user_profile)
            if eligibility["is_eligible"]:
                eligible_schemes.append({
                    "scheme_id": scheme["scheme_id"],
                    "name": scheme["name"],
                    "description": scheme.get("description", ""),
                    "match_score": eligibility["confidence"],
                    "eligibility_status": "eligible",
                    "estimated_benefit": scheme["benefit_amount"],
                    "application_difficulty": scheme["difficulty"],
                    "category": scheme.get("category", "general"),
                    "matched_criteria": eligibility["matched_criteria"],
                    "reason": f"Matches {len(eligibility['matched_criteria'])} criteria: {', '.join(eligibility['matched_criteria'])}"
                })

        return eligible_schemes

    async def evaluate_eligibility(self, scheme_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate eligibility for a specific scheme with multi-criteria matching
        Validates: Requirements 3.2 (income, caste, age, gender, occupation, location)
        """
        scheme = next((s for s in self.schemes_db if s["scheme_id"] == scheme_id), None)
        if not scheme:
            return {
                "is_eligible": False,
                "confidence": 0.0,
                "matched_criteria": [],
                "unmatched_criteria": [],
                "missing_information": [],
                "recommendations": ["Scheme not found in database"]
            }

        matched = []
        unmatched = []
        missing = []
        recommendations = []
        
        eligibility_criteria = scheme["eligibility"]

        # Check occupation (Requirement 3.2)
        if "occupation" in eligibility_criteria:
            user_occupation = user_profile.get("economic", {}).get("occupation")
            if user_occupation:
                if user_occupation in eligibility_criteria["occupation"]:
                    matched.append("occupation")
                else:
                    unmatched.append("occupation")
                    recommendations.append(f"Scheme requires occupation: {', '.join(eligibility_criteria['occupation'])}")
            else:
                missing.append("occupation")

        # Check land ownership
        if "land_ownership" in eligibility_criteria:
            land_data = user_profile.get("economic", {}).get("land_ownership", {})
            has_land = land_data.get("has_land", False) if isinstance(land_data, dict) else land_data
            if eligibility_criteria["land_ownership"] == has_land:
                matched.append("land_ownership")
            else:
                unmatched.append("land_ownership")
                recommendations.append("Scheme requires land ownership")

        # Check income (Requirement 3.2)
        if "max_income" in eligibility_criteria:
            user_income = user_profile.get("economic", {}).get("annual_income")
            if user_income is not None:
                if user_income <= eligibility_criteria["max_income"]:
                    matched.append("income")
                else:
                    unmatched.append("income")
                    recommendations.append(f"Income exceeds maximum limit of {eligibility_criteria['max_income']}")
            else:
                missing.append("income")

        # Check age (Requirement 3.2)
        if "min_age" in eligibility_criteria:
            user_age = user_profile.get("personal_info", {}).get("age")
            if user_age is not None:
                if user_age >= eligibility_criteria["min_age"]:
                    matched.append("age")
                else:
                    unmatched.append("age")
                    recommendations.append(f"Minimum age requirement: {eligibility_criteria['min_age']}")
            else:
                missing.append("age")
        
        if "max_age" in eligibility_criteria:
            user_age = user_profile.get("personal_info", {}).get("age")
            if user_age is not None:
                if user_age <= eligibility_criteria["max_age"]:
                    matched.append("age_limit")
                else:
                    unmatched.append("age_limit")
                    recommendations.append(f"Maximum age limit: {eligibility_criteria['max_age']}")
            else:
                if "age" not in missing:
                    missing.append("age")

        # Check gender (Requirement 3.2)
        if "gender" in eligibility_criteria:
            user_gender = user_profile.get("personal_info", {}).get("gender")
            if user_gender:
                if user_gender in eligibility_criteria["gender"]:
                    matched.append("gender")
                else:
                    unmatched.append("gender")
                    recommendations.append(f"Scheme is for: {', '.join(eligibility_criteria['gender'])}")
            else:
                missing.append("gender")

        # Check caste (Requirement 3.2)
        if "caste" in eligibility_criteria:
            user_caste = user_profile.get("demographics", {}).get("caste")
            if user_caste:
                if user_caste in eligibility_criteria["caste"]:
                    matched.append("caste")
                else:
                    unmatched.append("caste")
                    recommendations.append(f"Scheme is for: {', '.join(eligibility_criteria['caste'])} categories")
            else:
                missing.append("caste")

        # Check location (Requirement 3.2)
        if "state" in eligibility_criteria:
            user_state = user_profile.get("demographics", {}).get("state")
            if user_state:
                if user_state in eligibility_criteria["state"]:
                    matched.append("location")
                else:
                    unmatched.append("location")
                    recommendations.append(f"Scheme available in: {', '.join(eligibility_criteria['state'])}")
            else:
                missing.append("location")

        # Check marital status
        if "marital_status" in eligibility_criteria:
            user_marital_status = user_profile.get("personal_info", {}).get("marital_status")
            if user_marital_status:
                if user_marital_status in eligibility_criteria["marital_status"]:
                    matched.append("marital_status")
                else:
                    unmatched.append("marital_status")
            else:
                missing.append("marital_status")

        # Calculate confidence score
        total_criteria = len(matched) + len(unmatched)
        confidence = len(matched) / total_criteria if total_criteria > 0 else 0.0
        
        # Determine eligibility
        is_eligible = len(matched) > 0 and len(unmatched) == 0 and len(missing) == 0

        if missing:
            recommendations.append(f"Please provide: {', '.join(missing)}")

        return {
            "is_eligible": is_eligible,
            "confidence": confidence,
            "matched_criteria": matched,
            "unmatched_criteria": unmatched,
            "missing_information": missing,
            "recommendations": recommendations
        }

    async def update_scheme_database(self, schemes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update scheme database with new information
        Validates: Requirement 3.4 (updates within 24 hours)
        
        Returns:
            Dictionary with update results including success status and updated schemes
        """
        updated_schemes = []
        
        for update in schemes:
            scheme_id = update["scheme_id"]
            update_time = datetime.now()
            
            # Log the update
            self.scheme_updates_log.append({
                "scheme_id": scheme_id,
                "update_time": update_time,
                "changes": update.get("changes", {})
            })
            
            # Update in-memory database
            scheme_found = False
            for i, scheme in enumerate(self.schemes_db):
                if scheme["scheme_id"] == scheme_id:
                    # Update eligibility fields if they're in changes
                    changes = update.get("changes", {})
                    for key, value in changes.items():
                        if key in ["max_income", "min_age", "max_age", "occupation", "gender", "caste", "state"]:
                            # These go in eligibility dict
                            if "eligibility" not in self.schemes_db[i]:
                                self.schemes_db[i]["eligibility"] = {}
                            self.schemes_db[i]["eligibility"][key] = value
                        else:
                            # Top-level fields
                            self.schemes_db[i][key] = value
                    
                    self.schemes_db[i]["last_updated"] = update_time.isoformat()
                    updated_schemes.append(scheme_id)
                    scheme_found = True
                    break
            
            if not scheme_found:
                # New scheme - add to database
                new_scheme = {
                    "scheme_id": scheme_id,
                    "name": update.get("changes", {}).get("name", scheme_id),
                    "description": update.get("changes", {}).get("description", ""),
                    "eligibility": {},
                    "benefit_amount": update.get("changes", {}).get("benefit_amount", 0),
                    "difficulty": update.get("changes", {}).get("difficulty", "medium"),
                    "category": update.get("changes", {}).get("category", "general"),
                    "related_schemes": [],
                    "last_updated": update_time.isoformat()
                }
                # Apply all changes
                for key, value in update.get("changes", {}).items():
                    if key in ["max_income", "min_age", "max_age", "occupation", "gender", "caste", "state"]:
                        new_scheme["eligibility"][key] = value
                    else:
                        new_scheme[key] = value
                
                self.schemes_db.append(new_scheme)
                updated_schemes.append(scheme_id)
            
            # Update graph database if available
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    changes = update.get("changes", {})
                    session.run(
                        """
                        MERGE (s:Scheme {scheme_id: $scheme_id})
                        SET s += $changes,
                            s.last_updated = $last_updated
                        """,
                        scheme_id=scheme_id,
                        changes=changes,
                        last_updated=update_time.isoformat()
                    )
        
        self.last_update_time = datetime.now()
        
        return {
            "success": True,
            "updated_count": len(updated_schemes),
            "updated_schemes": updated_schemes,
            "timestamp": self.last_update_time.isoformat()
        }

    async def get_priority_ranking(
        self,
        schemes: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get priority-ranked list of schemes
        Validates: Requirement 3.3 (prioritize by benefit amount and application ease)
        """
        ranked_schemes = []

        for scheme in schemes:
            priority_score = scheme.get("match_score", 0.5)

            # Prioritize by benefit amount (Requirement 3.3)
            if preferences.get("prioritize_benefit"):
                benefit_weight = scheme.get("estimated_benefit", 0) / 10000
                priority_score += benefit_weight

            # Prioritize by application ease (Requirement 3.3)
            if preferences.get("prioritize_ease"):
                difficulty_scores = {"easy": 1.0, "medium": 0.5, "hard": 0.0}
                ease_weight = difficulty_scores.get(scheme.get("application_difficulty", "medium"), 0.5)
                priority_score += ease_weight

            ranked_schemes.append({
                **scheme,
                "priority_score": priority_score
            })

        # Sort by priority score (highest first)
        ranked_schemes.sort(key=lambda x: x["priority_score"], reverse=True)

        # Assign ranks
        for i, scheme in enumerate(ranked_schemes):
            scheme["rank"] = i + 1

        return ranked_schemes

    async def suggest_alternative_schemes(
        self,
        user_profile: Dict[str, Any],
        requested_scheme_id: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative schemes when user is ineligible for requested scheme
        Includes user preference learning and adaptation based on application history
        Validates: Requirement 3.5
        """
        # Get the requested scheme
        requested_scheme = next((s for s in self.schemes_db if s["scheme_id"] == requested_scheme_id), None)
        if not requested_scheme:
            return []

        # Find all eligible schemes
        all_eligible = await self.find_eligible_schemes(user_profile)

        # If user is eligible for requested scheme, no alternatives needed
        if any(s["scheme_id"] == requested_scheme_id for s in all_eligible):
            return []

        # Find schemes in the same category
        category_matches = [
            s for s in all_eligible
            if s.get("category") == requested_scheme.get("category")
        ]

        # Find related schemes using graph database or in-memory relationships
        related_matches = []
        if self.neo4j_driver:
            related_matches = await self._get_related_schemes_from_graph(requested_scheme_id, user_profile)
        else:
            # Use in-memory related schemes
            related_scheme_ids = requested_scheme.get("related_schemes", [])
            for scheme in all_eligible:
                if scheme["scheme_id"] in related_scheme_ids:
                    related_matches.append(scheme)

        # Combine and deduplicate alternatives
        alternatives = {}
        for scheme in category_matches + related_matches:
            scheme_id = scheme["scheme_id"]
            if scheme_id not in alternatives:
                alternatives[scheme_id] = scheme
                alternatives[scheme_id]["suggestion_reason"] = []

            if scheme in category_matches:
                alternatives[scheme_id]["suggestion_reason"].append(
                    f"Similar category: {scheme.get('category', 'general')}"
                )
            if scheme in related_matches:
                alternatives[scheme_id]["suggestion_reason"].append(
                    f"Related to {requested_scheme['name']}"
                )

        # Learn from user's application history and adapt suggestions
        learned_preferences = self._learn_user_preferences(user_profile.get("application_history", []))

        # Apply learned preferences to boost relevant schemes
        for scheme in alternatives.values():
            scheme["match_score"] = self._adapt_score_with_preferences(
                scheme,
                learned_preferences
            )

        # Format suggestion reasons
        result = []
        for scheme in alternatives.values():
            scheme["suggestion_reason"] = " | ".join(scheme["suggestion_reason"])

            # Add preference-based reason if applicable
            if learned_preferences.get("preferred_categories") and scheme.get("category") in learned_preferences["preferred_categories"]:
                scheme["suggestion_reason"] += " | Based on your past interests"

            result.append(scheme)

        # Sort by adapted match score
        result.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        return result


    async def _get_related_schemes_from_graph(
        self,
        scheme_id: str,
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get related schemes from Neo4j graph database"""
        if not self.neo4j_driver:
            return []

        related_schemes = []
        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (s1:Scheme {scheme_id: $scheme_id})-[:RELATED_TO]->(s2:Scheme)
                RETURN s2.scheme_id as scheme_id
                """,
                scheme_id=scheme_id
            )
            
            for record in result:
                related_id = record["scheme_id"]
                eligibility = await self.evaluate_eligibility(related_id, user_profile)
                if eligibility["is_eligible"]:
                    scheme = next((s for s in self.schemes_db if s["scheme_id"] == related_id), None)
                    if scheme:
                        related_schemes.append({
                            "scheme_id": scheme["scheme_id"],
                            "name": scheme["name"],
                            "description": scheme.get("description", ""),
                            "match_score": eligibility["confidence"],
                            "eligibility_status": "eligible",
                            "estimated_benefit": scheme["benefit_amount"],
                            "application_difficulty": scheme["difficulty"],
                            "category": scheme.get("category", "general"),
                            "matched_criteria": eligibility["matched_criteria"]
                        })

        return related_schemes

    def get_scheme_update_status(self) -> Dict[str, Any]:
        """Get information about recent scheme updates"""
        status = {
            "last_update_time": self.last_update_time.isoformat(),
            "total_schemes": len(self.schemes_db),
            "recent_updates": len([
                u for u in self.scheme_updates_log
                if datetime.fromisoformat(u["update_time"].isoformat()) > datetime.now() - timedelta(hours=24)
            ]),
            "update_log": self.scheme_updates_log[-10:]  # Last 10 updates
        }
        
        # Add freshness monitoring data if available
        if self.freshness_monitor:
            freshness_data = self.freshness_monitor.check_database_freshness(self.schemes_db)
            status["freshness"] = freshness_data
        
        return status

    async def sync_with_external_apis(self) -> Dict[str, Any]:
        """
        Sync scheme database with external APIs (myScheme and e-Shram)
        Validates: Requirement 3.4 - Integration with myScheme API and e-Shram platform
        
        Returns:
            Dictionary with sync results
        """
        if not self.api_integration:
            return {
                "success": False,
                "message": "External API integration not available",
                "schemes_updated": 0
            }
        
        try:
            # Fetch updates from external APIs
            updates = await self.api_integration.fetch_scheme_updates()
            
            if not updates:
                return {
                    "success": True,
                    "message": "No updates available from external APIs",
                    "schemes_updated": 0
                }
            
            # Transform to update format
            update_list = []
            for scheme in updates:
                update_list.append({
                    "scheme_id": scheme["scheme_id"],
                    "changes": scheme
                })
            
            # Apply updates to database
            await self.update_scheme_database(update_list)
            
            logger.info(f"Successfully synced {len(updates)} schemes from external APIs")
            
            return {
                "success": True,
                "message": f"Successfully synced {len(updates)} schemes",
                "schemes_updated": len(updates),
                "sources": list(set(s.get("source") for s in updates if s.get("source")))
            }
            
        except Exception as e:
            logger.error(f"Error syncing with external APIs: {e}")
            return {
                "success": False,
                "message": f"Error syncing: {str(e)}",
                "schemes_updated": 0
            }

    def check_data_freshness(self) -> Dict[str, Any]:
        """
        Check data freshness and generate alerts if needed
        Validates: Requirement 3.4 - Data freshness monitoring and alerts
        
        Returns:
            Dictionary with freshness status and alerts
        """
        if not self.freshness_monitor:
            return {
                "status": "monitoring_unavailable",
                "message": "Data freshness monitoring not available"
            }
        
        return self.freshness_monitor.check_database_freshness(self.schemes_db)

    def get_stale_schemes(self) -> List[Dict[str, Any]]:
        """
        Get list of schemes that need updating
        Validates: Requirement 3.4
        
        Returns:
            List of stale schemes
        """
        if not self.freshness_monitor:
            return []
        
        return self.freshness_monitor.get_stale_schemes(self.schemes_db)

    def get_freshness_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent freshness alerts
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent alerts
        """
        if not self.freshness_monitor:
            return []
        
        return self.freshness_monitor.get_recent_alerts(hours=hours)

    def _handle_freshness_alert(self, alert: Any):
        """
        Handle freshness alerts (default callback)
        
        Args:
            alert: FreshnessAlert object
        """
        # Log the alert
        if alert.severity == "error":
            logger.error(f"Freshness Alert: {alert.message}")
        elif alert.severity == "warning":
            logger.warning(f"Freshness Alert: {alert.message}")
        else:
            logger.info(f"Freshness Alert: {alert.message}")
        
        # Could trigger additional actions here:
        # - Send notifications
        # - Trigger automatic sync
        # - Update monitoring dashboard

    def _learn_user_preferences(self, application_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Learn user preferences from application history
        Analyzes past applications to identify patterns and preferences
        
        Args:
            application_history: List of past application records
            
        Returns:
            Dictionary containing learned preferences
        """
        if not application_history:
            return {
                "preferred_categories": [],
                "preferred_benefit_range": None,
                "preferred_difficulty": None,
                "application_count": 0
            }
        
        # Analyze categories from past applications
        category_counts = {}
        benefit_amounts = []
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}
        
        for app in application_history:
            # Count category preferences
            category = app.get("scheme_category", "general")
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Track benefit amounts
            if "benefit_amount" in app:
                benefit_amounts.append(app["benefit_amount"])
            
            # Track difficulty preferences (schemes they actually applied to)
            difficulty = app.get("application_difficulty", "medium")
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1
        
        # Identify preferred categories (top 3)
        preferred_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        preferred_categories = [cat for cat, _ in preferred_categories]
        
        # Calculate preferred benefit range
        preferred_benefit_range = None
        if benefit_amounts:
            avg_benefit = sum(benefit_amounts) / len(benefit_amounts)
            preferred_benefit_range = {
                "min": min(benefit_amounts),
                "max": max(benefit_amounts),
                "average": avg_benefit
            }
        
        # Identify preferred difficulty
        preferred_difficulty = max(difficulty_counts.items(), key=lambda x: x[1])[0]
        
        return {
            "preferred_categories": preferred_categories,
            "preferred_benefit_range": preferred_benefit_range,
            "preferred_difficulty": preferred_difficulty,
            "application_count": len(application_history)
        }
    
    def _adapt_score_with_preferences(
        self,
        scheme: Dict[str, Any],
        learned_preferences: Dict[str, Any]
    ) -> float:
        """
        Adapt scheme match score based on learned user preferences
        
        Args:
            scheme: Scheme information dictionary
            learned_preferences: Learned preferences from application history
            
        Returns:
            Adapted match score
        """
        base_score = scheme.get("match_score", 0.5)
        
        # If no learning data, return base score
        if learned_preferences["application_count"] == 0:
            return base_score
        
        # Boost score for preferred categories
        if scheme.get("category") in learned_preferences["preferred_categories"]:
            category_boost = 0.2
            # Higher boost for top preference
            if learned_preferences["preferred_categories"][0] == scheme.get("category"):
                category_boost = 0.3
            base_score += category_boost
        
        # Boost score for schemes with similar benefit amounts
        if learned_preferences["preferred_benefit_range"]:
            scheme_benefit = scheme.get("estimated_benefit", 0)
            avg_benefit = learned_preferences["preferred_benefit_range"]["average"]
            
            # If scheme benefit is within 50% of average preferred benefit, boost it
            if avg_benefit > 0:
                benefit_ratio = scheme_benefit / avg_benefit
                if 0.5 <= benefit_ratio <= 1.5:
                    base_score += 0.15
        
        # Boost score for preferred difficulty level
        if scheme.get("application_difficulty") == learned_preferences["preferred_difficulty"]:
            base_score += 0.1
        
        # Cap the score at 1.0
        return min(base_score, 1.0)

    async def close(self):
        """Close database connections and cleanup. Idempotent — safe to call multiple times."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            self.neo4j_driver = None
        
        if self.api_integration:
            await self.api_integration.close()
            self.api_integration = None
