import time
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from continuous_learning import ContinuousLearningSystem


class AcousticModel:
    """
    Acoustic feature-based dialect detection model
    Analyzes prosody, phonetics, and acoustic patterns
    """
    
    def __init__(self):
        # Simulates a trained acoustic model
        self.model_weights = self._initialize_weights()
    
    def _initialize_weights(self) -> Dict[str, float]:
        """Initialize model weights for different dialects"""
        return {
            "hi-IN": 1.0, "hi-UP": 0.9, "hi-MP": 0.85,
            "bn-IN": 1.0, "bn-WB": 0.9,
            "te-IN": 1.0, "te-AP": 0.9,
            "ta-IN": 1.0, "ta-TN": 0.9,
            "mr-IN": 1.0, "mr-MH": 0.9,
            "gu-IN": 1.0, "gu-GJ": 0.9,
            "kn-IN": 1.0, "kn-KA": 0.9,
            "ml-IN": 1.0, "ml-KL": 0.9,
            "pa-IN": 1.0, "pa-PB": 0.9
        }
    
    def predict(self, audio_features: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict dialect probabilities based on acoustic features
        Returns: Dict mapping dialect codes to confidence scores
        """
        # Simulate acoustic analysis based on audio features
        sample_rate = audio_features.get("sample_rate", 16000)
        duration = audio_features.get("duration", 1.0)
        
        # Simulate feature extraction and prediction
        # In production, this would use actual acoustic models
        scores = {}
        for dialect, weight in self.model_weights.items():
            # Simulate confidence based on audio quality
            base_score = weight * min(1.0, duration / 3.0)
            noise_factor = 1.0 - (abs(sample_rate - 16000) / 48000)
            scores[dialect] = base_score * noise_factor
        
        return scores


class LinguisticModel:
    """
    Linguistic feature-based dialect detection model
    Analyzes vocabulary, grammar, and language patterns
    """
    
    def __init__(self):
        self.language_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize linguistic patterns for different dialects"""
        return {
            "hi-IN": ["है", "हैं", "था", "थी"],
            "hi-UP": ["बा", "बानी", "रहल"],
            "hi-MP": ["हवे", "हवय", "रहे"],
            "bn-IN": ["আছে", "ছিল", "হয়"],
            "te-IN": ["ఉంది", "ఉన్నాడు", "ఉన్నారు"],
            "ta-IN": ["இருக்கிறது", "இருந்தது", "உள்ளது"],
            "mr-IN": ["आहे", "होते", "होता"],
            "gu-IN": ["છે", "હતું", "હતો"],
            "kn-IN": ["ಇದೆ", "ಇತ್ತು", "ಇದ್ದಾರೆ"],
            "ml-IN": ["ഉണ്ട്", "ഉണ്ടായിരുന്നു", "ആണ്"],
            "pa-IN": ["ਹੈ", "ਸੀ", "ਹਨ"]
        }
    
    def predict(self, audio_features: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict dialect probabilities based on linguistic features
        Returns: Dict mapping dialect codes to confidence scores
        """
        # Simulate linguistic analysis
        # In production, this would analyze transcribed text
        scores = {}
        duration = audio_features.get("duration", 1.0)
        
        for dialect in self.language_patterns.keys():
            # Simulate linguistic confidence
            base_score = min(0.95, duration / 3.0)
            scores[dialect] = base_score * np.random.uniform(0.7, 1.0)
        
        return scores


class CodeSwitchingDetector:
    """
    Detects and handles code-switching between languages
    Maintains context and semantic understanding across language switches
    Validates: Requirement 2.3
    """
    
    def __init__(self):
        self.switch_threshold = 0.3  # Minimum confidence difference to detect switch
        self.context_window = 5  # Number of previous segments to maintain
        self.language_history: List[Dict[str, Any]] = []
    
    def detect_code_switching(
        self,
        current_scores: Dict[str, float],
        previous_dialect: Optional[str] = None,
        segment_index: int = 0
    ) -> Dict[str, Any]:
        """
        Detect if code-switching occurred between languages
        Returns: Dict with switching information and context
        """
        # Get current top languages
        sorted_scores = sorted(current_scores.items(), key=lambda x: x[1], reverse=True)
        current_primary = sorted_scores[0][0] if sorted_scores else "unknown"
        current_primary_lang = self._extract_language(current_primary)
        
        # Update language history FIRST (before checking for switches)
        self._update_history(current_primary_lang, segment_index, current_scores)
        
        if not previous_dialect:
            # First segment, no switching possible
            # But still detect secondary language
            secondary_language = None
            if len(sorted_scores) > 1:
                secondary_lang = self._extract_language(sorted_scores[1][0])
                if secondary_lang != current_primary_lang and sorted_scores[1][1] > 0.3:
                    secondary_language = secondary_lang
            
            return {
                "code_switching_detected": False,
                "primary_language": current_primary_lang,
                "secondary_language": secondary_language,
                "switch_points": [],
                "context_preserved": True,
                "language_distribution": self._get_language_distribution()
            }
        
        previous_primary_lang = self._extract_language(previous_dialect)
        
        # Check if language changed
        language_switched = current_primary_lang != previous_primary_lang
        
        # Check confidence difference to confirm switch
        if language_switched and len(sorted_scores) > 1:
            confidence_diff = sorted_scores[0][1] - sorted_scores[1][1]
            is_confident_switch = confidence_diff >= self.switch_threshold
        else:
            is_confident_switch = language_switched  # If only one score, trust it
        
        # Detect secondary language (for mixed speech)
        secondary_language = None
        if len(sorted_scores) > 1:
            secondary_lang = self._extract_language(sorted_scores[1][0])
            if secondary_lang != current_primary_lang and sorted_scores[1][1] > 0.3:
                secondary_language = secondary_lang
        
        result = {
            "code_switching_detected": language_switched and is_confident_switch,
            "primary_language": current_primary_lang,
            "secondary_language": secondary_language,
            "switch_points": self._get_switch_points(),
            "context_preserved": True,  # Always maintain context
            "language_distribution": self._get_language_distribution()
        }
        
        return result
    
    def _extract_language(self, dialect_code: str) -> str:
        """Extract language code from dialect code"""
        return dialect_code.split("-")[0]
    
    def _get_primary_language(self, scores: Dict[str, float]) -> str:
        """Get primary language from scores"""
        if not scores:
            return "unknown"
        primary_dialect = max(scores.items(), key=lambda x: x[1])[0]
        return self._extract_language(primary_dialect)
    
    def _update_history(self, language: str, segment_index: int, scores: Dict[str, float]) -> None:
        """Update language history for context preservation"""
        self.language_history.append({
            "language": language,
            "segment_index": segment_index,
            "scores": scores.copy(),
            "timestamp": segment_index
        })
        
        # Keep only recent history (context window)
        if len(self.language_history) > self.context_window:
            self.language_history = self.language_history[-self.context_window:]
    
    def _get_switch_points(self) -> List[int]:
        """Identify points where language switching occurred"""
        switch_points = []
        for i in range(1, len(self.language_history)):
            if self.language_history[i]["language"] != self.language_history[i-1]["language"]:
                switch_points.append(self.language_history[i]["segment_index"])
        return switch_points
    
    def _get_language_distribution(self) -> Dict[str, float]:
        """Get distribution of languages in recent history"""
        if not self.language_history:
            return {}
        
        language_counts: Dict[str, int] = {}
        for entry in self.language_history:
            lang = entry["language"]
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        total = len(self.language_history)
        return {lang: count / total for lang, count in language_counts.items()}
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get preserved context across language switches
        Maintains semantic understanding by tracking language patterns
        """
        return {
            "language_history": self.language_history.copy(),
            "dominant_language": self._get_dominant_language(),
            "switch_frequency": len(self._get_switch_points()),
            "context_window_size": len(self.language_history)
        }
    
    def _get_dominant_language(self) -> Optional[str]:
        """Get the most frequently used language in context"""
        distribution = self._get_language_distribution()
        if not distribution:
            return None
        return max(distribution.items(), key=lambda x: x[1])[0]
    
    def reset_context(self) -> None:
        """Reset context for new conversation"""
        self.language_history.clear()


class EnsembleDialectDetector:
    """
    Multi-model ensemble combining acoustic and linguistic features
    Implements the core detection logic with confidence scoring
    """
    
    def __init__(self):
        self.acoustic_model = AcousticModel()
        self.linguistic_model = LinguisticModel()
        self.confidence_threshold = 0.7  # Requirement 2.4: Low confidence threshold
        self.acoustic_weight = 0.4
        self.linguistic_weight = 0.6
        self.code_switching_detector = CodeSwitchingDetector()  # Task 3.3
    
    def detect(self, audio_features: Dict[str, Any]) -> Tuple[str, float, List[Dict[str, Any]]]:
        """
        Detect dialect using ensemble approach
        Returns: (primary_dialect, confidence, alternative_dialects)
        """
        # Get predictions from both models
        acoustic_scores = self.acoustic_model.predict(audio_features)
        linguistic_scores = self.linguistic_model.predict(audio_features)
        
        # Combine scores using weighted ensemble
        combined_scores = {}
        all_dialects = set(acoustic_scores.keys()) | set(linguistic_scores.keys())
        
        for dialect in all_dialects:
            acoustic_score = acoustic_scores.get(dialect, 0.0)
            linguistic_score = linguistic_scores.get(dialect, 0.0)
            combined_scores[dialect] = (
                self.acoustic_weight * acoustic_score +
                self.linguistic_weight * linguistic_score
            )
        
        # Sort by confidence
        sorted_dialects = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Extract primary and alternatives
        primary_dialect, primary_confidence = sorted_dialects[0]
        alternative_dialects = [
            {"dialect": dialect, "confidence": round(conf, 3)}
            for dialect, conf in sorted_dialects[1:4]
        ]
        
        return primary_dialect, round(primary_confidence, 3), alternative_dialects


class DialectDetectorService:
    """
    Dialect Detector Service Implementation
    Multi-model ensemble approach with real-time detection and fallback handling
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """

    def __init__(self):
        self.supported_dialects = self._initialize_dialects()
        self.feedback_store: Dict[str, List[Dict]] = {}
        self.ensemble_detector = EnsembleDialectDetector()
        self.confidence_threshold = 0.7  # Requirement 2.4
        self.max_detection_time = 3.0  # Requirement 2.1: 3 seconds max
        self.session_contexts: Dict[str, CodeSwitchingDetector] = {}  # Task 3.3: Session-based context
        self.continuous_learning = ContinuousLearningSystem()  # Task 3.4: Continuous learning
        self._learning_initialized = False

    def _initialize_dialects(self) -> List[Dict[str, Any]]:
        """Initialize supported Indian dialects"""
        return [
            {
                "dialect_code": "hi-IN",
                "language_code": "hi",
                "name": "Hindi (Standard)",
                "region": "North India",
                "speakers": 500000000,
                "is_supported": True
            },
            {
                "dialect_code": "hi-UP",
                "language_code": "hi",
                "name": "Hindi (Uttar Pradesh)",
                "region": "Uttar Pradesh",
                "speakers": 200000000,
                "is_supported": True
            },
            {
                "dialect_code": "hi-MP",
                "language_code": "hi",
                "name": "Hindi (Madhya Pradesh)",
                "region": "Madhya Pradesh",
                "speakers": 80000000,
                "is_supported": True
            },
            {
                "dialect_code": "bn-IN",
                "language_code": "bn",
                "name": "Bengali (Standard)",
                "region": "West Bengal",
                "speakers": 100000000,
                "is_supported": True
            },
            {
                "dialect_code": "bn-WB",
                "language_code": "bn",
                "name": "Bengali (West Bengal)",
                "region": "West Bengal",
                "speakers": 90000000,
                "is_supported": True
            },
            {
                "dialect_code": "te-IN",
                "language_code": "te",
                "name": "Telugu (Standard)",
                "region": "Andhra Pradesh & Telangana",
                "speakers": 80000000,
                "is_supported": True
            },
            {
                "dialect_code": "te-AP",
                "language_code": "te",
                "name": "Telugu (Andhra Pradesh)",
                "region": "Andhra Pradesh",
                "speakers": 40000000,
                "is_supported": True
            },
            {
                "dialect_code": "ta-IN",
                "language_code": "ta",
                "name": "Tamil (Standard)",
                "region": "Tamil Nadu",
                "speakers": 75000000,
                "is_supported": True
            },
            {
                "dialect_code": "mr-IN",
                "language_code": "mr",
                "name": "Marathi",
                "region": "Maharashtra",
                "speakers": 83000000,
                "is_supported": True
            },
            {
                "dialect_code": "gu-IN",
                "language_code": "gu",
                "name": "Gujarati",
                "region": "Gujarat",
                "speakers": 56000000,
                "is_supported": True
            },
            {
                "dialect_code": "kn-IN",
                "language_code": "kn",
                "name": "Kannada",
                "region": "Karnataka",
                "speakers": 44000000,
                "is_supported": True
            },
            {
                "dialect_code": "ml-IN",
                "language_code": "ml",
                "name": "Malayalam",
                "region": "Kerala",
                "speakers": 38000000,
                "is_supported": True
            },
            {
                "dialect_code": "pa-IN",
                "language_code": "pa",
                "name": "Punjabi",
                "region": "Punjab",
                "speakers": 33000000,
                "is_supported": True
            }
        ]

    def _extract_language_code(self, dialect_code: str) -> str:
        """Extract language code from dialect code"""
        return dialect_code.split("-")[0]

    def _should_ask_clarification(self, confidence: float) -> bool:
        """
        Determine if clarification is needed based on confidence
        Requirement 2.4: Ask clarifying questions when confidence is low
        """
        return confidence < self.confidence_threshold

    def _generate_clarification_prompt(self, primary_dialect: str, alternatives: List[Dict]) -> str:
        """
        Generate clarifying question in detected primary language
        Requirement 2.4: Ask in detected primary language
        """
        language_code = self._extract_language_code(primary_dialect)
        
        # Clarification prompts in different languages
        prompts = {
            "hi": "क्या आप हिंदी बोल रहे हैं? कृपया पुष्टि करें।",
            "bn": "আপনি কি বাংলা বলছেন? দয়া করে নিশ্চিত করুন।",
            "te": "మీరు తెలుగు మాట్లాడుతున్నారా? దయచేసి నిర్ధారించండి.",
            "ta": "நீங்கள் தமிழ் பேசுகிறீர்களா? தயவுசெய்து உறுதிப்படுத்தவும்.",
            "mr": "तुम्ही मराठी बोलत आहात का? कृपया पुष्टी करा.",
            "gu": "શું તમે ગુજરાતી બોલો છો? કૃપા કરીને પુષ્ટિ કરો.",
            "kn": "ನೀವು ಕನ್ನಡ ಮಾತನಾಡುತ್ತಿದ್ದೀರಾ? ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ.",
            "ml": "നിങ്ങൾ മലയാളം സംസാരിക്കുന്നുണ്ടോ? ദയവായി സ്ഥിരീകരിക്കുക.",
            "pa": "ਕੀ ਤੁਸੀਂ ਪੰਜਾਬੀ ਬੋਲ ਰਹੇ ਹੋ? ਕਿਰਪਾ ਕਰਕੇ ਪੁਸ਼ਟੀ ਕਰੋ।"
        }
        
        return prompts.get(language_code, "Please confirm your language.")

    async def detect_dialect(
        self,
        audio_features: Dict[str, Any],
        session_id: Optional[str] = None,
        segment_index: int = 0
    ) -> Dict[str, Any]:
        """
        Detect dialect from audio features using multi-model ensemble
        Must complete within 3 seconds (Requirement 2.1)
        Handles low confidence with fallback (Requirement 2.4)
        Detects code-switching for mixed-language speech (Requirement 2.3, Task 3.3)
        
        Args:
            audio_features: Audio characteristics for detection
            session_id: Optional session ID for context preservation
            segment_index: Index of current segment in conversation
        """
        # Initialize continuous learning system if needed
        if not self._learning_initialized:
            await self.continuous_learning.initialize()
            self._learning_initialized = True
        
        start_time = time.time()

        # Use ensemble detector for multi-model approach
        primary_dialect, confidence, alternative_dialects = self.ensemble_detector.detect(
            audio_features
        )
        
        # Extract primary language
        primary_language = self._extract_language_code(primary_dialect)
        
        # Get or create code-switching detector for session
        code_switching_info = {"code_switching_detected": False}
        context_info = {}
        
        if session_id:
            if session_id not in self.session_contexts:
                self.session_contexts[session_id] = CodeSwitchingDetector()
            
            cs_detector = self.session_contexts[session_id]
            
            # Get previous dialect from context
            previous_dialect = None
            if cs_detector.language_history:
                previous_dialect = cs_detector.language_history[-1].get("language")
                if previous_dialect:
                    # Convert language code back to dialect code for comparison
                    previous_dialect = f"{previous_dialect}-IN"
            
            # Detect code-switching
            all_scores = {}
            acoustic_scores = self.ensemble_detector.acoustic_model.predict(audio_features)
            linguistic_scores = self.ensemble_detector.linguistic_model.predict(audio_features)
            
            # Combine scores for code-switching detection
            all_dialects = set(acoustic_scores.keys()) | set(linguistic_scores.keys())
            for dialect in all_dialects:
                acoustic_score = acoustic_scores.get(dialect, 0.0)
                linguistic_score = linguistic_scores.get(dialect, 0.0)
                all_scores[dialect] = (
                    self.ensemble_detector.acoustic_weight * acoustic_score +
                    self.ensemble_detector.linguistic_weight * linguistic_score
                )
            
            code_switching_info = cs_detector.detect_code_switching(
                all_scores,
                previous_dialect,
                segment_index
            )
            
            # Get preserved context
            context_info = cs_detector.get_context()
        
        # Check detection time (Requirement 2.1: within 3 seconds)
        detection_time = (time.time() - start_time) * 1000
        if detection_time > self.max_detection_time * 1000:
            # Log warning but continue
            print(f"Warning: Detection took {detection_time}ms, exceeds {self.max_detection_time}s threshold")
        
        # Determine if clarification is needed (Requirement 2.4)
        needs_clarification = self._should_ask_clarification(confidence)
        clarification_prompt = None
        if needs_clarification:
            clarification_prompt = self._generate_clarification_prompt(
                primary_dialect, alternative_dialects
            )
        
        result = {
            "primary_dialect": primary_dialect,
            "primary_language": primary_language,
            "confidence": confidence,
            "alternative_dialects": alternative_dialects,
            "detection_time": round(detection_time, 2),
            "code_switching_detected": code_switching_info.get("code_switching_detected", False),
            "secondary_language": code_switching_info.get("secondary_language"),
            "switch_points": code_switching_info.get("switch_points", []),
            "language_distribution": code_switching_info.get("language_distribution", {}),
            "context_preserved": code_switching_info.get("context_preserved", True),
            "needs_clarification": needs_clarification,
            "clarification_prompt": clarification_prompt,
            "model_version": self.continuous_learning.model_pipeline.get_active_version()  # Task 3.4
        }
        
        # Add context information (always include for consistent result structure)
        result["context"] = context_info if context_info else {}

        return result

    async def update_confidence(self, session_id: str, feedback: Dict[str, Any]) -> None:
        """
        Update confidence scores based on user feedback
        Supports continuous learning (Requirement 2.5, Task 3.4)
        """
        if session_id not in self.feedback_store:
            self.feedback_store[session_id] = []
        
        # Store feedback with timestamp
        feedback_entry = {
            **feedback,
            "timestamp": time.time()
        }
        self.feedback_store[session_id].append(feedback_entry)
        
        # Integrate with continuous learning system (Task 3.4)
        await self.continuous_learning.collect_feedback(
            session_id=session_id,
            detected_dialect=feedback.get("detected_dialect", ""),
            confidence=feedback.get("confidence", 0.0),
            user_correction=feedback.get("correct_dialect"),
            user_satisfaction=feedback.get("user_satisfaction"),
            audio_features=feedback.get("audio_features", {}),
            context=feedback.get("context", {})
        )
        
        # Legacy threshold adjustment (kept for backward compatibility)
        if feedback.get("correct_dialect"):
            # User provided correction - adjust confidence threshold
            if feedback.get("user_satisfaction", 3) < 3:
                # Low satisfaction - be more conservative
                self.confidence_threshold = min(0.85, self.confidence_threshold + 0.05)
            elif feedback.get("user_satisfaction", 3) > 4:
                # High satisfaction - can be more aggressive
                self.confidence_threshold = max(0.6, self.confidence_threshold - 0.02)

    async def get_supported_dialects(self) -> List[Dict[str, Any]]:
        """Get list of all supported dialects"""
        return self.supported_dialects

    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get preserved context for a session
        Maintains semantic understanding across language switches (Task 3.3)
        """
        if session_id not in self.session_contexts:
            return None
        
        return self.session_contexts[session_id].get_context()
    
    def reset_session_context(self, session_id: str) -> None:
        """
        Reset context for a session
        Useful when starting a new conversation topic
        """
        if session_id in self.session_contexts:
            self.session_contexts[session_id].reset_context()
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear all data for a session
        Removes context and feedback data
        """
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
        if session_id in self.feedback_store:
            del self.feedback_store[session_id]
    
    async def deploy_model_update(
        self,
        version: str,
        model_data: Optional[Dict[str, Any]] = None,
        gradual_rollout: bool = True
    ) -> Dict[str, Any]:
        """
        Deploy a new model version without service interruption
        Task 3.4: Model update pipeline
        Requirement 2.5: Update without service interruption
        
        Args:
            version: Version identifier
            model_data: Model weights and configuration
            gradual_rollout: Whether to gradually roll out the new version
        
        Returns:
            Deployment status and details
        """
        success = await self.continuous_learning.deploy_new_model(
            version=version,
            model_data=model_data,
            gradual_rollout=gradual_rollout
        )
        
        return {
            "success": success,
            "version": version,
            "active_version": self.continuous_learning.model_pipeline.get_active_version(),
            "gradual_rollout": gradual_rollout
        }
    
    async def start_model_ab_test(
        self,
        test_id: str,
        candidate_version: str,
        candidate_model_data: Optional[Dict[str, Any]] = None,
        traffic_split: float = 0.1,
        min_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Start an A/B test with a candidate model version
        Task 3.4: A/B testing for model versions
        Requirement 2.5: Test new models without disruption
        
        Args:
            test_id: Unique test identifier
            candidate_version: Candidate model version to test
            candidate_model_data: Model weights and configuration
            traffic_split: Percentage of traffic for candidate (0.0-1.0)
            min_samples: Minimum samples for statistical significance
        
        Returns:
            Test creation status and details
        """
        success = await self.continuous_learning.start_ab_test(
            test_id=test_id,
            candidate_version=candidate_version,
            candidate_model_data=candidate_model_data,
            traffic_split=traffic_split,
            min_samples=min_samples
        )
        
        return {
            "success": success,
            "test_id": test_id,
            "candidate_version": candidate_version,
            "traffic_split": traffic_split,
            "min_samples": min_samples
        }
    
    def get_ab_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results for an A/B test
        Task 3.4: A/B testing results
        
        Args:
            test_id: Test identifier
        
        Returns:
            Test results including metrics for both versions
        """
        return self.continuous_learning.ab_testing.get_test_results(test_id)
    
    def stop_ab_test(self, test_id: str) -> bool:
        """
        Stop an active A/B test
        Task 3.4: A/B testing management
        
        Args:
            test_id: Test identifier
        
        Returns:
            True if test stopped successfully
        """
        return self.continuous_learning.ab_testing.stop_test(test_id)
    
    def get_learning_system_status(self) -> Dict[str, Any]:
        """
        Get status of the continuous learning system
        Task 3.4: System monitoring
        
        Returns:
            System status including active version, tests, and metrics
        """
        return self.continuous_learning.get_system_status()
    
    async def rollback_model_version(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Rollback to a previous model version
        Task 3.4: Model rollback capability
        
        Args:
            target_version: Version to rollback to (defaults to most recent inactive)
        
        Returns:
            Rollback status and details
        """
        success = await self.continuous_learning.model_pipeline.rollback_version(target_version)
        
        return {
            "success": success,
            "active_version": self.continuous_learning.model_pipeline.get_active_version(),
            "target_version": target_version
        }

