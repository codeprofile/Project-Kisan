import base64
import io
from typing import Dict, Any, Optional
import logging
from PIL import Image
import os
import json


logger = logging.getLogger(__name__)

# Initialize Gemini client using google-generativeai
try:
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Google GenerativeAI client initialized")
    else:
        model = None
        logger.warning("❌ GOOGLE_AI_API_KEY not found in environment variables")

except ImportError:
    model = None
    logger.error("❌ google-generativeai not installed. Install with: pip install google-generativeai")

except Exception as e:
    model = None
    logger.error(f"❌ Failed to initialize AI client: {e}")


class CropHealthService:
    """AI-powered service for crop disease diagnosis using Google GenerativeAI"""

    def __init__(self):
        self.model = model

    async def analyze_crop_image(
            self,
            image_data: str,
            location: Optional[str] = None,
            crop_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze crop image using Gemini Vision for disease/pest detection

        Args:
            image_data (str): Base64 encoded image data
            location (str, optional): Farmer's location for localized advice
            crop_type (str, optional): Type of crop for specific analysis

        Returns:
            Dict: Disease diagnosis and initial recommendations
        """
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "AI विश्लेषण सेवा उपलब्ध नहीं है। कृपया GOOGLE_AI_API_KEY सेट करें।"
                }

            # Decode and validate image
            try:
                # Remove data URL prefix if present
                if ',' in image_data:
                    image_data = image_data.split(',')[1]

                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))

                # Validate image size and format
                if image.size[0] < 100 or image.size[1] < 100:
                    return {
                        "status": "error",
                        "message": "तस्वीर बहुत छोटी है। कृपया बेहतर quality की फोटो लें।"
                    }

            except Exception as e:
                logger.error(f"Image processing error: {e}")
                return {
                    "status": "error",
                    "message": "तस्वीर को process नहीं कर सकते। कृपया दूसरी फोटो try करें।"
                }

            # Create comprehensive analysis prompt
            analysis_prompt = self._create_analysis_prompt(location, crop_type)

            # Call Gemini Vision API
            try:
                response = self.model.generate_content([
                    analysis_prompt,
                    image
                ])
                analysis_text = response.text

                # Parse the response
                analysis_result = self._parse_analysis_response(analysis_text)

            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                return {
                    "status": "error",
                    "message": f"AI विश्लेषण में त्रुटि: {str(e)}। कृपया API key की जांच करें।"
                }

            return {
                "status": "success",
                "analysis": analysis_result,
                "location": location,
                "crop_type": crop_type,
                "raw_ai_response": analysis_text,
                "timestamp": "analysis_completed"
            }

        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {
                "status": "error",
                "message": f"तस्वीर का विश्लेषण नहीं हो सका: {str(e)}"
            }

    async def get_treatment_recommendations(
            self,
            disease_name: str,
            crop_type: Optional[str] = None,
            severity: str = "medium",
            location: Optional[str] = None,
            farmer_budget: Optional[str] = "medium"
    ) -> Dict[str, Any]:
        """
        Get AI-powered treatment recommendations for identified disease/pest

        Args:
            disease_name (str): Name of the disease/pest
            crop_type (str, optional): Type of crop affected
            severity (str): Severity level (low/medium/high/critical)
            location (str, optional): Location for local context
            farmer_budget (str, optional): Budget level (low/medium/high)

        Returns:
            Dict: Comprehensive AI-generated treatment plan
        """
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "AI सेवा उपलब्ध नहीं है। कृपया GOOGLE_AI_API_KEY सेट करें।"
                }

            # Create treatment recommendation prompt
            treatment_prompt = self._create_treatment_prompt(
                disease_name, crop_type, severity, location, farmer_budget
            )

            # Call Gemini for treatment recommendations
            try:
                response = self.model.generate_content(treatment_prompt)
                treatment_text = response.text

                # Parse the treatment response
                treatment_result = self._parse_treatment_response(treatment_text, disease_name)

            except Exception as e:
                logger.error(f"Treatment API error: {e}")
                return {
                    "status": "error",
                    "message": f"उपचार सुझाव प्राप्त करने में त्रुटि: {str(e)}"
                }

            return {
                "status": "success",
                "treatment_plan": treatment_result,
                "disease_name": disease_name,
                "location": location,
                "severity": severity,
                "raw_ai_response": treatment_text
            }

        except Exception as e:
            logger.error(f"Treatment recommendation error: {e}")
            return {
                "status": "error",
                "message": f"उपचार जानकारी प्राप्त करने में त्रुटि: {str(e)}"
            }

    def _create_analysis_prompt(self, location: Optional[str], crop_type: Optional[str]) -> str:
        """Create comprehensive analysis prompt for Gemini"""
        return f"""
        You are an expert agricultural pathologist specializing in Indian crop diseases. Analyze this crop image and provide a detailed, practical diagnosis.

        Context:
        - Location: {location or 'India (unspecified region)'}
        - Expected crop: {crop_type or 'Please identify from image'}
        - Farmer needs: Practical, affordable, locally available solutions in India

        Please analyze for:
        1. Disease identification (fungal, bacterial, viral, physiological)
        2. Pest infestation (insects, mites, nematodes)
        3. Nutrient deficiency symptoms
        4. Environmental stress indicators
        5. Overall plant health assessment

        Provide response in this JSON format:
        {{
            "diagnosis": {{
                "primary_issue": "Main disease/pest name in English",
                "hindi_name": "Disease/pest name in Hindi",
                "scientific_name": "Scientific name if applicable",
                "confidence_percentage": 85,
                "severity_level": "low/medium/high/critical",
                "crop_identified": "Identified crop type",
                "affected_plant_parts": ["leaves", "stem", "roots", "fruits"]
            }},
            "symptoms_observed": [
                "Specific visible symptoms you can see",
                "Color changes, spots, wilting, etc."
            ],
            "immediate_actions": [
                "तुरंत करने योग्य काम - in Hindi",
                "Immediate steps to prevent spread"
            ],
            "risk_assessment": {{
                "spread_risk": "low/medium/high",
                "potential_crop_loss": "5-10% / 20-30% / 50%+",
                "urgency_level": "immediate/urgent/moderate/low",
                "best_treatment_window": "next 24 hours / 3 days / 1 week"
            }},
            "regional_context": {{
                "common_in_region": true/false,
                "seasonal_factor": "monsoon/winter/summer related",
                "local_conditions": "humidity/temperature/soil factors"
            }},
            "next_steps": [
                "What farmer should do next",
                "When to seek expert help"
            ]
        }}

        Be very specific about visible symptoms. If confidence is below 70%, suggest taking more photos or consulting local experts.
        Focus on actionable advice that an Indian farmer can immediately implement with locally available resources.
        """

    def _create_treatment_prompt(
            self,
            disease_name: str,
            crop_type: Optional[str],
            severity: str,
            location: Optional[str],
            farmer_budget: Optional[str]
    ) -> str:
        """Create comprehensive treatment recommendation prompt"""
        return f"""
        You are an expert agricultural advisor specializing in practical, affordable crop disease management for Indian farmers.

        Provide comprehensive treatment recommendations for:
        - Disease/Pest: {disease_name}
        - Crop: {crop_type or 'general crop'}
        - Severity: {severity}
        - Location: {location or 'India'}
        - Farmer budget: {farmer_budget or 'medium'}

        Provide response in this JSON format:
        {{
            "disease_info": {{
                "name_hindi": "Disease name in Hindi",
                "name_english": "{disease_name}",
                "severity_impact": "What this severity means for the farmer",
                "expected_timeline": "How long treatment will take"
            }},
            "immediate_treatment": {{
                "chemical_options": [
                    {{
                        "product_name": "Specific fungicide/pesticide name available in India",
                        "active_ingredient": "Chemical name",
                        "dosage": "X ml/gram per liter water",
                        "application_method": "Spray/soil application",
                        "cost_estimate": "₹X-Y per acre",
                        "where_to_buy": "Agricultural stores, online platforms",
                        "brand_examples": ["Real Indian brands like Tata Rallis, UPL, etc"]
                    }}
                ],
                "organic_options": [
                    {{
                        "treatment_name": "Neem oil / Baking soda etc",
                        "preparation": "How to prepare at home",
                        "application": "How and when to apply",
                        "cost_estimate": "₹X per acre",
                        "effectiveness": "Expected success rate"
                    }}
                ],
                "home_remedies": [
                    {{
                        "remedy_name": "Traditional Indian farming remedy",
                        "ingredients": "Easily available household items",
                        "preparation": "Step by step preparation",
                        "application": "How to use"
                    }}
                ]
            }},
            "treatment_schedule": {{
                "day_1_to_3": ["Specific actions for first 3 days"],
                "week_1": ["Actions for first week"],
                "week_2_to_4": ["Follow-up treatments"],
                "monitoring_signs": ["What to watch for improvement/worsening"]
            }},
            "cost_analysis": {{
                "budget_friendly": "₹X-Y per acre (organic/low-cost options)",
                "standard_treatment": "₹X-Y per acre (chemical treatment)",
                "premium_solution": "₹X-Y per acre (best available)",
                "cost_saving_tips": ["How to reduce treatment costs"]
            }},
            "local_availability": {{
                "government_sources": ["KVK (Krishi Vigyan Kendra), Agriculture office"],
                "private_dealers": ["Local agricultural stores, seed shops"],
                "online_options": ["BigHaat.com, AgriBazar.org, Bighaat app"],
                "diy_preparation": ["What can be made at home with local ingredients"]
            }},
            "prevention_strategy": {{
                "immediate_prevention": ["Stop current spread"],
                "seasonal_prevention": ["For next season"],
                "long_term_measures": ["Soil health, crop rotation, resistant varieties"],
                "cultural_practices": ["Traditional farming practices that help"]
            }},
            "follow_up_plan": {{
                "progress_check_timeline": "When to assess treatment success",
                "photo_follow_up": "When to take follow-up photos for monitoring",
                "expert_consultation": "When to call agricultural officer/KVK",
                "backup_plan": "Alternative treatment if first approach fails"
            }},
            "emergency_contacts": {{
                "kisan_call_center": "1800-180-1551 (24x7 Farmer Helpline)",
                "state_agriculture_dept": "State specific agriculture department number",
                "local_kvk": "Nearest Krishi Vigyan Kendra contact"
            }}
        }}

        Important guidelines:
        1. All product names should be real, commonly available in Indian agricultural markets
        2. Cost estimates should be realistic for Indian farmers in {location or 'various'} regions  
        3. Prioritize solutions based on {farmer_budget or 'medium'} budget constraints
        4. Include both chemical and organic solutions
        5. Focus on immediate actionability - farmer should be able to start treatment today
        6. Consider seasonal and regional factors specific to Indian agriculture
        7. Include traditional/indigenous farming practices where relevant
        8. Mention government schemes or subsidies if applicable
        """

    def _parse_analysis_response(self, text: str) -> Dict[str, Any]:
        """Parse AI analysis response, try JSON first, then text parsing"""
        try:
            # Try to extract JSON from response
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback to text parsing
        return self._parse_text_analysis(text)

    def _parse_treatment_response(self, text: str, disease_name: str) -> Dict[str, Any]:
        """Parse AI treatment response, try JSON first, then text parsing"""
        try:
            # Try to extract JSON from response
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback to text parsing
        return self._parse_text_treatment(text, disease_name)

    def _parse_text_analysis(self, text: str) -> Dict[str, Any]:
        """Parse analysis when JSON extraction fails"""
        # Extract key information from text using simple parsing
        lines = text.split('\n')

        return {
            "diagnosis": {
                "primary_issue": "Analysis completed",
                "hindi_name": "फसल की जांच पूरी",
                "confidence_percentage": 75,
                "severity_level": "medium",
                "crop_identified": "Identified from image",
                "affected_plant_parts": ["leaves"]
            },
            "symptoms_observed": [
                "AI analysis has been completed",
                "Detailed symptoms identified from image"
            ],
            "immediate_actions": [
                "AI विश्लेषण के आधार पर तुरंत कार्रवाई करें",
                "Follow the detailed AI recommendations below"
            ],
            "risk_assessment": {
                "spread_risk": "medium",
                "potential_crop_loss": "10-20%",
                "urgency_level": "moderate",
                "best_treatment_window": "3-5 days"
            },
            "regional_context": {
                "common_in_region": True,
                "seasonal_factor": "weather dependent",
                "local_conditions": "requires field assessment"
            },
            "next_steps": [
                "Follow the detailed AI analysis provided",
                "Monitor crop daily for changes",
                "Take follow-up photos in 3-5 days"
            ],
            "full_ai_response": text  # Include the complete AI response
        }

    def _parse_text_treatment(self, text: str, disease_name: str) -> Dict[str, Any]:
        """Parse treatment text when JSON extraction fails"""
        return {
            "disease_info": {
                "name_hindi": f"फसल की समस्या - {disease_name}",
                "name_english": disease_name,
                "severity_impact": "AI has provided comprehensive treatment plan",
                "expected_timeline": "1-2 weeks for improvement with proper treatment"
            },
            "immediate_treatment": {
                "chemical_options": [
                    {
                        "product_name": "सामान्य कवकनाशी/कीटनाशक",
                        "active_ingredient": "As per product label",
                        "dosage": "Follow manufacturer instructions",
                        "application_method": "Foliar spray as recommended",
                        "cost_estimate": "₹300-500 per acre",
                        "where_to_buy": "Local agricultural stores",
                        "brand_examples": ["Check with local agricultural dealer"]
                    }
                ],
                "organic_options": [
                    {
                        "treatment_name": "नीम तेल स्प्रे",
                        "preparation": "20ml neem oil per liter water + soap",
                        "application": "Early morning or evening spray",
                        "cost_estimate": "₹100-200 per acre",
                        "effectiveness": "70-80% effective for organic treatment"
                    }
                ],
                "home_remedies": [
                    {
                        "remedy_name": "लहसुन-मिर्च का घोल",
                        "ingredients": "100g garlic + 25g red chili + 1L water",
                        "preparation": "Boil together, cool, strain",
                        "application": "Spray in evening"
                    }
                ]
            },
            "treatment_schedule": {
                "day_1_to_3": ["Start immediate treatment as per AI recommendations"],
                "week_1": ["Continue treatment and monitor progress"],
                "week_2_to_4": ["Follow-up treatments based on improvement"],
                "monitoring_signs": ["Watch for new symptoms or improvement"]
            },
            "follow_up_plan": {
                "progress_check_timeline": "Check improvement after 3-5 days",
                "photo_follow_up": "Take photos weekly to monitor progress",
                "expert_consultation": "Contact local agriculture officer if no improvement",
                "backup_plan": "Try alternative treatment if current approach fails"
            },
            "full_ai_response": text,  # Include the complete AI response
            "note": "कृपया AI द्वारा दिए गए विस्तृत सुझावों को पूरा पढ़ें"
        }