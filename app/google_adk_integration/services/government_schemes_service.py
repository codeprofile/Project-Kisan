from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)



# Initialize Gemini client
try:
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Google GenerativeAI client initialized for Government Schemes")
    else:
        model = None
        logger.warning("❌ GOOGLE_AI_API_KEY not found for schemes service")

except ImportError:
    model = None
    logger.error("❌ google-generativeai not installed")

except Exception as e:
    model = None
    logger.error(f"❌ Failed to initialize AI client for schemes: {e}")


class GovernmentSchemesService:
    """AI-powered service for government schemes navigation and assistance"""

    def __init__(self):
        self.model = model

    async def search_schemes(
            self,
            query: str,
            state: Optional[str] = None,
            scheme_type: str = "all",
            farmer_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for relevant government schemes using AI"""
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "AI सेवा उपलब्ध नहीं है। कृपया GOOGLE_AI_API_KEY सेट करें।"
                }

            # Create comprehensive search prompt
            search_prompt = f"""
            आप एक सरकारी योजना विशेषज्ञ हैं। भारतीय किसान की निम्नलिखित आवश्यकता के लिए उपयुक्त सरकारी योजनाएं खोजें:

            किसान की आवश्यकता: {query}
            राज्य: {state or 'कोई विशिष्ट राज्य नहीं'}
            योजना प्रकार: {scheme_type}
            किसान श्रेणी: {farmer_category or 'सामान्य'}

            कृपया निम्नलिखित जानकारी प्रदान करें:

            1. **मुख्य योजनाएं** (केंद्र सरकार):
               - योजना का नाम
               - मुख्य लाभ
               - सब्सिडी राशि/प्रतिशत
               - बुनियादी पात्रता

            2. **राज्य सरकार की योजनाएं** (यदि state दी गई है):
               - राज्य-विशिष्ट योजनाएं
               - स्थानीय लाभ

            3. **अतिरिक्त विकल्प**:
               - बैंक लोन schemes
               - Private company schemes
               - NGO programs

            4. **व्यावहारिक सुझाव**:
               - कौन सी योजना सबसे बेहतर है
               - आवेदन की प्राथमिकता
               - सामान्य tips

            जानकारी सरल हिंदी में दें और वर्तमान (2024-25) योजनाओं पर फोकस करें।
            """

            # Call AI for scheme search
            response = self.model.generate_content(search_prompt)
            search_text = response.text

            return {
                "status": "success",
                "query": query,
                "state": state,
                "ai_response": search_text
            }

        except Exception as e:
            logger.error(f"Scheme search error: {e}")
            return {
                "status": "error",
                "message": f"योजना खोजने में त्रुटि: {str(e)}"
            }

    async def get_scheme_details(
            self,
            scheme_name: str,
            state: Optional[str] = None,
            include_application_info: bool = True
    ) -> Dict[str, Any]:
        """Get detailed information about a specific scheme"""
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "AI सेवा उपलब्ध नहीं है।"
                }

            # Create detailed information prompt
            details_prompt = f"""
            कृपया '{scheme_name}' योजना के बारे में विस्तृत जानकारी प्रदान करें:

            राज्य: {state or 'पूरे भारत के लिए'}
            आवेदन जानकारी शामिल करें: {'हां' if include_application_info else 'नहीं'}

            निम्नलिखित विवरण चाहिए:

            1. **योजना का पूरा नाम और उद्देश्य**

            2. **मुख्य लाभ और सुविधाएं**:
               - वित्तीय सहायता की राशि
               - सब्सिडी का प्रतिशत
               - अन्य लाभ

            3. **पात्रता मानदंड**:
               - आय सीमा
               - भूमि की आवश्यकता
               - आयु सीमा
               - श्रेणी आवश्यकताएं

            4. **आवश्यक दस्तावेज़**

            5. **योजना की अवधि और deadline**

            {'6. **आवेदन प्रक्रिया**: - ऑनलाइन/ऑफलाइन प्रक्रिया - आवेदन के चरण - महत्वपूर्ण लिंक' if include_application_info else ''}

            7. **संपर्क जानकारी**:
               - हेल्पलाइन नंबर
               - ऑफिशियल वेबसाइट
               - स्थानीय कार्यालय

            8. **महत्वपूर्ण बातें और सुझाव**

            सभी जानकारी सटीक, current और व्यावहारिक होनी चाहिए।
            """

            # Call AI for scheme details
            response = self.model.generate_content(details_prompt)
            details_text = response.text

            return {
                "status": "success",
                "scheme_name": scheme_name,
                "state": state,
                "ai_response": details_text
            }

        except Exception as e:
            logger.error(f"Scheme details error: {e}")
            return {
                "status": "error",
                "message": f"योजना विवरण प्राप्त करने में त्रुटि: {str(e)}"
            }

    async def check_eligibility(
            self,
            scheme_name: str,
            farmer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check farmer's eligibility for a scheme using AI analysis"""
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "AI सेवा उपलब्ध नहीं है।"
                }

            # Create eligibility check prompt
            eligibility_prompt = f"""
            कृपया '{scheme_name}' योजना के लिए निम्नलिखित किसान की पात्रता की जांच करें:

            किसान का विवरण:
            - भूमि का आकार: {farmer_profile.get('land_size', 'अज्ञात')} एकड़
            - वार्षिक आय: ₹{farmer_profile.get('annual_income', 'अज्ञात')}
            - श्रेणी: {farmer_profile.get('category', 'सामान्य')}
            - आयु: {farmer_profile.get('age', 'अज्ञात')} वर्ष
            - राज्य: {farmer_profile.get('state', 'अज्ञात')}
            - महिला किसान: {'हां' if farmer_profile.get('is_female') else 'नहीं'}
            - मौजूदा योजनाएं: {farmer_profile.get('existing_schemes', [])}

            कृपया निम्नलिखित विश्लेषण करें:

            1. **पात्रता स्थिति**: ✅ पात्र / ❌ अपात्र / 🔄 आंशिक पात्र

            2. **विस्तृत विश्लेषण**:
               - कौन सी शर्तें पूरी हो रही हैं
               - कौन सी शर्तें नहीं मिल रहीं
               - क्या सुधार की जा सकती है

            3. **सुझाव**:
               - पात्रता बढ़ाने के तरीके
               - वैकल्पिक योजनाएं
               - आवश्यक कार्रवाई

            4. **अगले कदम**:
               - तुरंत क्या करना चाहिए
               - दस्तावेज़ तैयार करना
               - आवेदन की timing

            स्पष्ट और actionable सलाह दें।
            """

            # Call AI for eligibility check
            response = self.model.generate_content(eligibility_prompt)
            eligibility_text = response.text

            return {
                "status": "success",
                "scheme_name": scheme_name,
                "farmer_profile": farmer_profile,
                "ai_response": eligibility_text
            }

        except Exception as e:
            logger.error(f"Eligibility check error: {e}")
            return {
                "status": "error",
                "message": f"पात्रता जांच में त्रुटि: {str(e)}"
            }

    async def get_application_process(
            self,
            scheme_name: str,
            state: Optional[str] = None,
            application_type: str = "online"
    ) -> Dict[str, Any]:
        """Get step-by-step application process"""
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "AI सेवा उपलब्ध नहीं है।"
                }

            # Create application process prompt
            process_prompt = f"""
            कृपया '{scheme_name}' योजना के लिए {application_type} आवेदन प्रक्रिया बताएं:

            राज्य: {state or 'सामान्य प्रक्रिया'}

            निम्नलिखित जानकारी चाहिए:

            1. **आवेदन से पहले की तैयारी**:
               - आवश्यक दस्तावेज़ की पूरी सूची
               - दस्तावेज़ कैसे तैयार करें
               - फोटो/scan की आवश्यकताएं

            2. **चरणबद्ध आवेदन प्रक्रिया**:
               {'- ऑनलाइन portal की जानकारी - Registration process - Form भरने की विधि - Document upload करना' if application_type == 'online' else ''}
               {'- कौन से कार्यालय में जाना है - किससे मिलना है - क्या documents ले जाना है' if application_type == 'offline' else ''}

            3. **महत्वपूर्ण लिंक और संपर्क**:
               - Official website
               - Direct application links
               - Helpline numbers
               - Office addresses

            4. **Application के बाद**:
               - कितने दिन में response मिलेगा
               - Status कैसे check करें
               - Problem होने पर क्या करें

            5. **Common Mistakes और Tips**:
               - गलतियों से कैसे बचें
               - Success rate बढ़ाने के तरीके

            व्यावहारिक और step-by-step guidance दें।
            """

            # Call AI for application process
            response = self.model.generate_content(process_prompt)
            process_text = response.text

            return {
                "status": "success",
                "scheme_name": scheme_name,
                "application_type": application_type,
                "ai_response": process_text
            }

        except Exception as e:
            logger.error(f"Application process error: {e}")
            return {
                "status": "error",
                "message": f"आवेदन प्रक्रिया प्राप्त करने में त्रुटि: {str(e)}"
            }

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service_available": self.model is not None,
            "ai_model": "gemini-2.0-flash-exp" if self.model else None,
            "api_configured": os.getenv("GOOGLE_AI_API_KEY") is not None,
            "approach": "Pure AI-driven government schemes assistance",
            "capabilities": [
                "Real-time scheme search using AI knowledge",
                "Dynamic eligibility assessment",
                "Current application process guidance",
                "AI-powered office location assistance",
                "Latest updates from AI knowledge base"
            ] if self.model else [],
            "data_source": "AI knowledge base - no hardcoded data"
        }

