from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from acquisition_data import (
    get_acquisition_guidance,
    get_authority_contacts,
    get_document_templates
)

logger = logging.getLogger(__name__)


class DocumentGuideService:
    """
    Document Guidance Service Implementation
    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
    
    Features:
    - Multilingual document requirement database
    - Scheme-specific document mapping
    - Alternative document suggestion engine
    - Step-by-step document acquisition guidance
    - Authority contact information system
    - Document templates and examples
    """

    def __init__(self):
        self.documents_db = self._initialize_documents()
        self.scheme_documents_map = self._initialize_scheme_documents()
        self.document_alternatives = self._initialize_alternatives()
        self.acquisition_guidance = get_acquisition_guidance()
        self.authority_contacts = get_authority_contacts()
        self.document_templates = get_document_templates()
        logger.info("Document Guide Service initialized with acquisition guidance")

    def _initialize_documents(self) -> Dict[str, Dict[str, Any]]:
        """Initialize document database with multilingual descriptions"""
        return {
            "AADHAAR": {
                "document_id": "AADHAAR",
                "names": {
                    "en": "Aadhaar Card",
                    "hi": "आधार कार्ड",
                    "ta": "ஆதார் அட்டை",
                    "te": "ఆధార్ కార్డ్",
                    "bn": "আধার কার্ড",
                    "mr": "आधार कार्ड",
                    "gu": "આધાર કાર્ડ",
                    "kn": "ಆಧಾರ್ ಕಾರ್ಡ್",
                    "ml": "ആധാർ കാർഡ്",
                    "pa": "ਆਧਾਰ ਕਾਰਡ"
                },
                "descriptions": {
                    "en": "12-digit unique identification number issued by UIDAI",
                    "hi": "यूआईडीएआई द्वारा जारी 12 अंकों की विशिष्ट पहचान संख्या",
                    "ta": "UIDAI வழங்கும் 12 இலக்க தனித்துவ அடையாள எண்",
                    "te": "UIDAI జారీ చేసిన 12 అంకెల ప్రత్యేక గుర్తింపు సంఖ్య"
                },
                "category": "identity"
            },
            "VOTER_ID": {
                "document_id": "VOTER_ID",
                "names": {
                    "en": "Voter ID Card",
                    "hi": "मतदाता पहचान पत्र",
                    "ta": "வாக்காளர் அடையாள அட்டை",
                    "te": "ఓటరు గుర్తింపు కార్డు",
                    "bn": "ভোটার আইডি কার্ড",
                    "mr": "मतदार ओळखपत्र",
                    "gu": "મતદાર ઓળખ કાર્ડ",
                    "kn": "ಮತದಾರ ಗುರುತಿನ ಚೀಟಿ",
                    "ml": "വോട്ടർ ഐഡി കാർഡ്",
                    "pa": "ਵੋਟਰ ਆਈਡੀ ਕਾਰਡ"
                },
                "descriptions": {
                    "en": "Identity card issued by Election Commission of India",
                    "hi": "भारत निर्वाचन आयोग द्वारा जारी पहचान पत्र",
                    "ta": "இந்திய தேர்தல் ஆணையம் வழங்கும் அடையாள அட்டை",
                    "te": "భారత ఎన్నికల సంఘం జారీ చేసిన గుర్తింపు కార్డు"
                },
                "category": "identity"
            },
            "RATION_CARD": {
                "document_id": "RATION_CARD",
                "names": {
                    "en": "Ration Card",
                    "hi": "राशन कार्ड",
                    "ta": "ரேஷன் அட்டை",
                    "te": "రేషన్ కార్డు",
                    "bn": "রেশন কার্ড",
                    "mr": "रेशन कार्ड",
                    "gu": "રેશન કાર્ડ",
                    "kn": "ಪಡಿತರ ಚೀಟಿ",
                    "ml": "റേഷൻ കാർഡ്",
                    "pa": "ਰਾਸ਼ਨ ਕਾਰਡ"
                },
                "descriptions": {
                    "en": "Card for subsidized food grains, also serves as address and income proof",
                    "hi": "सब्सिडी वाले खाद्यान्न के लिए कार्ड, पता और आय प्रमाण के रूप में भी काम करता है",
                    "ta": "மானிய உணவு தானியங்களுக்கான அட்டை, முகவரி மற்றும் வருமான சான்றாகவும் செயல்படுகிறது",
                    "te": "సబ్సిడీ ఆహార ధాన్యాల కోసం కార్డు, చిరునామా మరియు ఆదాయ రుజువుగా కూడా పనిచేస్తుంది"
                },
                "category": "identity_income"
            },
            "BANK_PASSBOOK": {
                "document_id": "BANK_PASSBOOK",
                "names": {
                    "en": "Bank Passbook",
                    "hi": "बैंक पासबुक",
                    "ta": "வங்கி பாஸ்புக்",
                    "te": "బ్యాంక్ పాస్‌బుక్",
                    "bn": "ব্যাংক পাসবুক",
                    "mr": "बँक पासबुक",
                    "gu": "બેંક પાસબુક",
                    "kn": "ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್",
                    "ml": "ബാങ്ക് പാസ്ബുക്ക്",
                    "pa": "ਬੈਂਕ ਪਾਸਬੁੱਕ"
                },
                "descriptions": {
                    "en": "Bank account statement showing account details and transactions",
                    "hi": "खाता विवरण और लेनदेन दिखाने वाला बैंक खाता विवरण",
                    "ta": "கணக்கு விவரங்கள் மற்றும் பரிவர்த்தனைகளைக் காட்டும் வங்கி கணக்கு அறிக்கை",
                    "te": "ఖాతా వివరాలు మరియు లావాదేవీలను చూపించే బ్యాంక్ ఖాతా స్టేట్‌మెంట్"
                },
                "category": "financial"
            },
            "LAND_RECORDS": {
                "document_id": "LAND_RECORDS",
                "names": {
                    "en": "Land Records / Land Ownership Certificate",
                    "hi": "भूमि अभिलेख / भूमि स्वामित्व प्रमाण पत्र",
                    "ta": "நில பதிவுகள் / நில உரிமை சான்றிதழ்",
                    "te": "భూమి రికార్డులు / భూమి యాజమాన్య ధృవీకరణ పత్రం",
                    "bn": "ভূমি রেকর্ড / জমির মালিকানা শংসাপত্র",
                    "mr": "जमीन नोंदी / जमीन मालकी प्रमाणपत्र",
                    "gu": "જમીન રેકોર્ડ / જમીન માલિકી પ્રમાણપત્ર",
                    "kn": "ಭೂಮಿ ದಾಖಲೆಗಳು / ಭೂಮಿ ಮಾಲೀಕತ್ವ ಪ್ರಮಾಣಪತ್ರ",
                    "ml": "ഭൂമി രേഖകൾ / ഭൂമി ഉടമസ്ഥാവകാശ സർട്ടിഫിക്കറ്റ്",
                    "pa": "ਜ਼ਮੀਨ ਰਿਕਾਰਡ / ਜ਼ਮੀਨ ਮਾਲਕੀ ਸਰਟੀਫਿਕੇਟ"
                },
                "descriptions": {
                    "en": "Official documents proving land ownership (7/12, 8A, Patta, Khatiyan)",
                    "hi": "भूमि स्वामित्व साबित करने वाले आधिकारिक दस्तावेज (7/12, 8ए, पट्टा, खतियान)",
                    "ta": "நில உரிமையை நிரூபிக்கும் அதிகாரப்பூர்வ ஆவணங்கள் (7/12, 8A, பட்டா, கதியான்)",
                    "te": "భూమి యాజమాన్యాన్ని రుజువు చేసే అధికారిక పత్రాలు (7/12, 8A, పట్టా, ఖతియాన్)"
                },
                "category": "property"
            },
            "INCOME_CERTIFICATE": {
                "document_id": "INCOME_CERTIFICATE",
                "names": {
                    "en": "Income Certificate",
                    "hi": "आय प्रमाण पत्र",
                    "ta": "வருமான சான்றிதழ்",
                    "te": "ఆదాయ ధృవీకరణ పత్రం",
                    "bn": "আয় শংসাপত্র",
                    "mr": "उत्पन्न प्रमाणपत्र",
                    "gu": "આવક પ્રમાણપત્ર",
                    "kn": "ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ",
                    "ml": "വരുമാന സർട്ടിഫിക്കറ്റ്",
                    "pa": "ਆਮਦਨ ਸਰਟੀਫਿਕੇਟ"
                },
                "descriptions": {
                    "en": "Certificate issued by revenue authorities stating annual family income",
                    "hi": "राजस्व अधिकारियों द्वारा जारी वार्षिक पारिवारिक आय बताने वाला प्रमाण पत्र",
                    "ta": "வருவாய் அதிகாரிகளால் வழங்கப்படும் வருடாந்திர குடும்ப வருமானத்தைக் குறிப்பிடும் சான்றிதழ்",
                    "te": "వార్షిక కుటుంబ ఆదాయాన్ని పేర్కొనే రెవిన్యూ అధికారులు జారీ చేసిన ధృవీకరణ పత్రం"
                },
                "category": "income"
            },
            "CASTE_CERTIFICATE": {
                "document_id": "CASTE_CERTIFICATE",
                "names": {
                    "en": "Caste Certificate",
                    "hi": "जाति प्रमाण पत्र",
                    "ta": "சாதி சான்றிதழ்",
                    "te": "కులం ధృవీకరణ పత్రం",
                    "bn": "জাতি শংসাপত্র",
                    "mr": "जात प्रमाणपत्र",
                    "gu": "જાતિ પ્રમાણપત્ર",
                    "kn": "ಜಾತಿ ಪ್ರಮಾಣಪತ್ರ",
                    "ml": "ജാതി സർട്ടിഫിക്കറ്റ്",
                    "pa": "ਜਾਤੀ ਸਰਟੀਫਿਕੇਟ"
                },
                "descriptions": {
                    "en": "Certificate issued by competent authority stating caste category (SC/ST/OBC)",
                    "hi": "सक्षम प्राधिकारी द्वारा जारी जाति श्रेणी (एससी/एसटी/ओबीसी) बताने वाला प्रमाण पत्र",
                    "ta": "சாதி வகையை (SC/ST/OBC) குறிப்பிடும் தகுதியான அதிகாரியால் வழங்கப்படும் சான்றிதழ்",
                    "te": "కులం వర్గాన్ని (SC/ST/OBC) పేర్కొనే సమర్థ అధికారి జారీ చేసిన ధృవీకరణ పత్రం"
                },
                "category": "identity"
            },
            "PASSPORT_PHOTO": {
                "document_id": "PASSPORT_PHOTO",
                "names": {
                    "en": "Passport Size Photograph",
                    "hi": "पासपोर्ट साइज फोटो",
                    "ta": "பாஸ்போர்ட் அளவு புகைப்படம்",
                    "te": "పాస్‌పోర్ట్ సైజ్ ఫోటో",
                    "bn": "পাসপোর্ট সাইজ ছবি",
                    "mr": "पासपोर्ट आकाराचा फोटो",
                    "gu": "પાસપોર્ટ સાઇઝ ફોટો",
                    "kn": "ಪಾಸ್‌ಪೋರ್ಟ್ ಗಾತ್ರದ ಫೋಟೋ",
                    "ml": "പാസ്പോർട്ട് സൈസ് ഫോട്ടോ",
                    "pa": "ਪਾਸਪੋਰਟ ਸਾਈਜ਼ ਫੋਟੋ"
                },
                "descriptions": {
                    "en": "Recent passport-sized photograph (usually 2-4 copies required)",
                    "hi": "हाल का पासपोर्ट आकार का फोटोग्राफ (आमतौर पर 2-4 प्रतियां आवश्यक)",
                    "ta": "சமீபத்திய பாஸ்போர்ட் அளவு புகைப்படம் (பொதுவாக 2-4 நகல்கள் தேவை)",
                    "te": "ఇటీవలి పాస్‌పోర్ట్ సైజ్ ఫోటో (సాధారణంగా 2-4 కాపీలు అవసరం)"
                },
                "category": "supporting"
            }
        }

    def _initialize_scheme_documents(self) -> Dict[str, List[str]]:
        """Map schemes to required documents"""
        return {
            "PM-KISAN": ["AADHAAR", "LAND_RECORDS", "BANK_PASSBOOK"],
            "MGNREGA": ["AADHAAR", "BANK_PASSBOOK", "PASSPORT_PHOTO"],
            "PM-FASAL-BIMA": ["AADHAAR", "LAND_RECORDS", "BANK_PASSBOOK"],
            "WIDOW-PENSION": ["AADHAAR", "BANK_PASSBOOK", "INCOME_CERTIFICATE", "PASSPORT_PHOTO"],
            "OLD-AGE-PENSION": ["AADHAAR", "BANK_PASSBOOK", "INCOME_CERTIFICATE", "PASSPORT_PHOTO"],
            "SC-ST-SCHOLARSHIP": ["AADHAAR", "CASTE_CERTIFICATE", "BANK_PASSBOOK", "INCOME_CERTIFICATE", "PASSPORT_PHOTO"],
            "OBC-SCHOLARSHIP": ["AADHAAR", "CASTE_CERTIFICATE", "BANK_PASSBOOK", "INCOME_CERTIFICATE", "PASSPORT_PHOTO"]
        }

    def _initialize_alternatives(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize alternative document suggestions"""
        return {
            "AADHAAR": [
                {
                    "documents": ["VOTER_ID", "RATION_CARD"],
                    "explanation": {
                        "en": "If Aadhaar is not available, you can use Voter ID along with Ration Card",
                        "hi": "यदि आधार उपलब्ध नहीं है, तो आप राशन कार्ड के साथ मतदाता पहचान पत्र का उपयोग कर सकते हैं",
                        "ta": "ஆதார் கிடைக்கவில்லை என்றால், ரேஷன் அட்டையுடன் வாக்காளர் அடையாள அட்டையைப் பயன்படுத்தலாம்",
                        "te": "ఆధార్ అందుబాటులో లేకుంటే, మీరు రేషన్ కార్డుతో పాటు ఓటరు గుర్తింపు కార్డును ఉపయోగించవచ్చు"
                    }
                }
            ],
            "LAND_RECORDS": [
                {
                    "documents": ["RATION_CARD"],
                    "explanation": {
                        "en": "If land records are not available, Ration Card showing land ownership may be accepted",
                        "hi": "यदि भूमि अभिलेख उपलब्ध नहीं हैं, तो भूमि स्वामित्व दिखाने वाला राशन कार्ड स्वीकार किया जा सकता है",
                        "ta": "நில பதிவுகள் கிடைக்கவில்லை என்றால், நில உரிமையைக் காட்டும் ரேஷன் அட்டை ஏற்றுக்கொள்ளப்படலாம்",
                        "te": "భూమి రికార్డులు అందుబాటులో లేకుంటే, భూమి యాజమాన్యాన్ని చూపించే రేషన్ కార్డు అంగీకరించబడవచ్చు"
                    }
                }
            ],
            "INCOME_CERTIFICATE": [
                {
                    "documents": ["RATION_CARD"],
                    "explanation": {
                        "en": "Ration Card (BPL/APL category) can serve as income proof in some cases",
                        "hi": "राशन कार्ड (बीपीएल/एपीएल श्रेणी) कुछ मामलों में आय प्रमाण के रूप में काम कर सकता है",
                        "ta": "ரேஷன் அட்டை (BPL/APL வகை) சில சந்தர்ப்பங்களில் வருமான சான்றாக செயல்படலாம்",
                        "te": "రేషన్ కార్డు (BPL/APL వర్గం) కొన్ని సందర్భాల్లో ఆదాయ రుజువుగా పనిచేయవచ్చు"
                    }
                }
            ],
            "CASTE_CERTIFICATE": [
                {
                    "documents": ["RATION_CARD"],
                    "explanation": {
                        "en": "Ration Card showing caste category may be accepted as temporary proof",
                        "hi": "जाति श्रेणी दिखाने वाला राशन कार्ड अस्थायी प्रमाण के रूप में स्वीकार किया जा सकता है",
                        "ta": "சாதி வகையைக் காட்டும் ரேஷன் அட்டை தற்காலிக சான்றாக ஏற்றுக்கொள்ளப்படலாம்",
                        "te": "కులం వర్గాన్ని చూపించే రేషన్ కార్డు తాత్కాలిక రుజువుగా అంగీకరించబడవచ్చు"
                    }
                }
            ]
        }

    async def get_scheme_documents(
        self,
        scheme_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get complete list of required documents for a scheme in user's language
        Validates: Requirement 5.1
        """
        if scheme_id not in self.scheme_documents_map:
            return {
                "scheme_id": scheme_id,
                "documents": [],
                "error": "Scheme not found"
            }

        required_doc_ids = self.scheme_documents_map[scheme_id]
        documents = []

        for doc_id in required_doc_ids:
            if doc_id in self.documents_db:
                doc = self.documents_db[doc_id]
                documents.append({
                    "document_id": doc_id,
                    "name": doc["names"].get(language, doc["names"]["en"]),
                    "description": doc["descriptions"].get(language, doc["descriptions"]["en"]),
                    "category": doc["category"]
                })

        return {
            "scheme_id": scheme_id,
            "language": language,
            "documents": documents,
            "total_documents": len(documents)
        }

    async def get_document_alternatives(
        self,
        document_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get acceptable alternative documents for a specific document
        Validates: Requirement 5.2
        """
        if document_id not in self.document_alternatives:
            return {
                "document_id": document_id,
                "alternatives": [],
                "message": "No alternatives available for this document"
            }

        alternatives = []
        for alt in self.document_alternatives[document_id]:
            alt_docs = []
            for alt_doc_id in alt["documents"]:
                if alt_doc_id in self.documents_db:
                    doc = self.documents_db[alt_doc_id]
                    alt_docs.append({
                        "document_id": alt_doc_id,
                        "name": doc["names"].get(language, doc["names"]["en"])
                    })

            alternatives.append({
                "documents": alt_docs,
                "explanation": alt["explanation"].get(language, alt["explanation"]["en"])
            })

        return {
            "document_id": document_id,
            "original_document": self.documents_db[document_id]["names"].get(language, self.documents_db[document_id]["names"]["en"]),
            "language": language,
            "alternatives": alternatives
        }

    async def get_scheme_documents_with_alternatives(
        self,
        scheme_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get complete document requirements with alternatives for a scheme
        Validates: Requirements 5.1, 5.2
        """
        scheme_docs = await self.get_scheme_documents(scheme_id, language)
        
        if "error" in scheme_docs:
            return scheme_docs

        # Add alternatives for each document
        for doc in scheme_docs["documents"]:
            alternatives_info = await self.get_document_alternatives(doc["document_id"], language)
            doc["alternatives"] = alternatives_info.get("alternatives", [])

        return scheme_docs

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        # Get languages from first document
        first_doc = next(iter(self.documents_db.values()))
        return list(first_doc["names"].keys())

    def get_all_documents(self, language: str = "en") -> List[Dict[str, Any]]:
        """Get all documents in the database"""
        documents = []
        for doc_id, doc in self.documents_db.items():
            documents.append({
                "document_id": doc_id,
                "name": doc["names"].get(language, doc["names"]["en"]),
                "description": doc["descriptions"].get(language, doc["descriptions"]["en"]),
                "category": doc["category"]
            })
        return documents

    async def get_document_acquisition_guidance(
        self,
        document_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get step-by-step guidance for obtaining a specific document
        Validates: Requirements 5.3, 5.5
        """
        if document_id not in self.acquisition_guidance:
            return {
                "document_id": document_id,
                "error": "Acquisition guidance not available for this document"
            }

        guidance = self.acquisition_guidance[document_id]
        doc_info = self.documents_db.get(document_id, {})

        # Get authority information
        authority_id = guidance.get("authority")
        authority_info = None
        if authority_id and authority_id in self.authority_contacts:
            authority = self.authority_contacts[authority_id]
            authority_info = {
                "name": authority["names"].get(language, authority["names"]["en"]),
                "contact": authority["contact_info"].get(language, authority["contact_info"]["en"])
            }

        return {
            "document_id": document_id,
            "document_name": doc_info.get("names", {}).get(language, doc_info.get("names", {}).get("en", document_id)),
            "language": language,
            "steps": guidance["steps"].get(language, guidance["steps"]["en"]),
            "authority": authority_info,
            "processing_time": guidance["processing_time"].get(language, guidance["processing_time"]["en"]),
            "fees": guidance["fees"].get(language, guidance["fees"]["en"])
        }

    async def get_authority_contact_info(
        self,
        authority_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get contact information for a specific authority
        Validates: Requirement 5.3
        """
        if authority_id not in self.authority_contacts:
            return {
                "authority_id": authority_id,
                "error": "Authority information not available"
            }

        authority = self.authority_contacts[authority_id]

        return {
            "authority_id": authority_id,
            "name": authority["names"].get(language, authority["names"]["en"]),
            "language": language,
            "contact_info": authority["contact_info"].get(language, authority["contact_info"]["en"])
        }

    async def get_document_template(
        self,
        document_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get template and example information for a specific document
        Validates: Requirement 5.4
        """
        if document_id not in self.document_templates:
            return {
                "document_id": document_id,
                "message": "Template not available for this document"
            }

        template = self.document_templates[document_id]
        doc_info = self.documents_db.get(document_id, {})

        return {
            "document_id": document_id,
            "document_name": doc_info.get("names", {}).get(language, doc_info.get("names", {}).get("en", document_id)),
            "language": language,
            "template_info": template["template_info"].get(language, template["template_info"]["en"])
        }

    async def get_complete_document_guidance(
        self,
        document_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get complete guidance including acquisition steps, authority contacts, and templates
        Validates: Requirements 5.3, 5.4, 5.5
        """
        doc_info = self.documents_db.get(document_id)
        if not doc_info:
            return {
                "document_id": document_id,
                "error": "Document not found"
            }

        result = {
            "document_id": document_id,
            "document_name": doc_info["names"].get(language, doc_info["names"]["en"]),
            "description": doc_info["descriptions"].get(language, doc_info["descriptions"]["en"]),
            "category": doc_info["category"],
            "language": language
        }

        # Add acquisition guidance if available
        if document_id in self.acquisition_guidance:
            guidance_info = await self.get_document_acquisition_guidance(document_id, language)
            result["acquisition_guidance"] = {
                "steps": guidance_info.get("steps", []),
                "authority": guidance_info.get("authority"),
                "processing_time": guidance_info.get("processing_time"),
                "fees": guidance_info.get("fees")
            }

        # Add template information if available
        if document_id in self.document_templates:
            template_info = await self.get_document_template(document_id, language)
            result["template"] = template_info.get("template_info")

        # Add alternatives if available
        if document_id in self.document_alternatives:
            alternatives_info = await self.get_document_alternatives(document_id, language)
            result["alternatives"] = alternatives_info.get("alternatives", [])

        return result

    def get_all_authorities(self, language: str = "en") -> List[Dict[str, Any]]:
        """Get list of all authorities with contact information"""
        authorities = []
        for authority_id, authority in self.authority_contacts.items():
            authorities.append({
                "authority_id": authority_id,
                "name": authority["names"].get(language, authority["names"]["en"]),
                "contact_info": authority["contact_info"].get(language, authority["contact_info"]["en"])
            })
        return authorities
