from typing import Dict, Any, Optional
import logging
from google.adk.tools.tool_context import ToolContext
from ..services.crop_health_service import CropHealthService

logger = logging.getLogger(__name__)

# Initialize the service
crop_health_service = CropHealthService()


async def analyze_crop_image(
        image_data: str,
        location: Optional[str] = None,
        crop_type: Optional[str] = None,
        additional_info: Optional[str] = None,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Analyze crop image using AI for disease/pest detection

    Args:
        image_data (str): Base64 encoded image data
        location (str, optional): Farmer's location for localized advice
        crop_type (str, optional): Type of crop for specific analysis
        additional_info (str, optional): Additional context from farmer
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Disease diagnosis and initial recommendations
    """
    try:
        logger.info(f"Starting crop image analysis for location: {location}, crop: {crop_type}")

        # Call the AI service for image analysis
        result = await crop_health_service.analyze_crop_image(
            image_data=image_data,
            location=location,
            crop_type=crop_type
        )

        # Store analysis in session context for follow-up
        if tool_context and result.get("status") == "success":
            analysis_data = result.get("analysis", {})
            diagnosis = analysis_data.get("diagnosis", {})

            tool_context.state["last_image_analysis"] = analysis_data
            tool_context.state["last_analyzed_crop"] = diagnosis.get("crop_identified")
            tool_context.state["last_disease"] = diagnosis.get("primary_issue")
            tool_context.state["last_severity"] = diagnosis.get("severity_level")
            tool_context.state["farmer_location"] = location

            logger.info(
                f"Analysis completed: {diagnosis.get('primary_issue')} with {diagnosis.get('confidence_percentage')}% confidence")

        return result

    except Exception as e:
        logger.error(f"Error in crop image analysis: {e}")
        return {
            "status": "error",
            "message": f"तस्वीर का विश्लेषण नहीं हो सका: {str(e)}। कृपया दोबारा कोशिश करें।"
        }


async def get_disease_treatment_info(
        disease_name: str,
        crop_type: Optional[str] = None,
        severity: str = "medium",
        location: Optional[str] = None,
        farmer_budget: str = "medium",
        urgency: str = "normal",
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get comprehensive AI-powered treatment information for crop diseases/pests

    Args:
        disease_name (str): Name of the disease/pest
        crop_type (str, optional): Type of crop affected
        severity (str): Severity level (low/medium/high/critical)
        location (str, optional): Location for local context
        farmer_budget (str): Budget level (low/medium/high)
        urgency (str): Treatment urgency (immediate/urgent/normal)
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Comprehensive AI-generated treatment plan
    """
    try:
        logger.info(f"Getting treatment info for: {disease_name}, severity: {severity}")

        # Get treatment recommendations from AI service
        result = await crop_health_service.get_treatment_recommendations(
            disease_name=disease_name,
            crop_type=crop_type,
            severity=severity,
            location=location,
            farmer_budget=farmer_budget
        )

        # Store treatment info in session context
        if tool_context and result.get("status") == "success":
            tool_context.state["last_treatment_info"] = result.get("treatment_plan")
            tool_context.state["last_treatment_disease"] = disease_name
            tool_context.state["treatment_severity"] = severity
            tool_context.state["farmer_budget"] = farmer_budget

            logger.info(f"Treatment recommendations generated for {disease_name}")

        return result

    except Exception as e:
        logger.error(f"Error getting treatment info: {e}")
        return {
            "status": "error",
            "message": f"उपचार जानकारी प्राप्त करने में त्रुटि: {str(e)}। कृपया दोबारा कोशिश करें।"
        }


async def get_follow_up_advice(
        previous_treatment: str,
        current_status: str,
        days_since_treatment: int = 0,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get follow-up advice based on treatment progress

    Args:
        previous_treatment (str): Previous treatment given
        current_status (str): Current condition of the crop
        days_since_treatment (int): Days since treatment started
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Follow-up recommendations
    """
    try:
        # Get context from previous session if available
        last_disease = tool_context.state.get("last_disease") if tool_context else "unknown"
        last_severity = tool_context.state.get("last_severity") if tool_context else "medium"
        farmer_location = tool_context.state.get("farmer_location") if tool_context else None

        # Create follow-up prompt for AI
        follow_up_prompt = f"""
        Farmer has been treating {last_disease} for {days_since_treatment} days.
        Previous treatment: {previous_treatment}
        Current status: {current_status}
        Original severity: {last_severity}
        Location: {farmer_location}

        Please provide follow-up advice in Hindi and English:
        1. Is the treatment working?
        2. Should continue current treatment or change?
        3. Any additional measures needed?
        4. When to expect full recovery?
        5. Warning signs to watch for?

        Provide practical, actionable advice.
        """

        # For now, return structured advice
        # In production, this could also call the AI service
        return {
            "status": "success",
            "follow_up_advice": {
                "treatment_progress": f"{days_since_treatment} दिन का उपचार चल रहा है",
                "current_assessment": current_status,
                "next_steps": [
                    "वर्तमान उपचार जारी रखें" if "better" in current_status.lower() else "उपचार में बदलाव की आवश्यकता",
                    "रोजाना निगरानी करते रहें",
                    "3-5 दिन में फिर से फोटो लें"
                ],
                "warning_signs": [
                    "यदि समस्या बढ़ रही हो",
                    "नए लक्षण दिखाई दें",
                    "पूरा पौधा प्रभावित हो रहा हो"
                ],
                "expected_timeline": "7-14 दिन में पूर्ण सुधार की उम्मीद"
            }
        }

    except Exception as e:
        logger.error(f"Error in follow-up advice: {e}")
        return {
            "status": "error",
            "message": f"फॉलो-अप सलाह में त्रुटि: {str(e)}"
        }


async def get_preventive_measures(
        crop_type: str,
        location: Optional[str] = None,
        season: Optional[str] = None,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get AI-powered preventive measures for crop health

    Args:
        crop_type (str): Type of crop
        location (str, optional): Location for regional advice
        season (str, optional): Current season
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Preventive measures and best practices
    """
    try:
        logger.info(f"Getting preventive measures for {crop_type} in {location}")

        # This could call the AI service for comprehensive preventive advice
        # For now, providing structured response
        return {
            "status": "success",
            "preventive_measures": {
                "crop_type": crop_type,
                "location": location,
                "general_prevention": [
                    "स्वच्छ बीज का उपयोग करें",
                    "उचित फसल चक्र अपनाएं",
                    "संतुलित उर्वरक का प्रयोग",
                    "खेत में जल निकासी की व्यवस्था"
                ],
                "seasonal_care": [
                    "मौसम के अनुसार छिड़काव करें",
                    "उचित सिंचाई प्रबंधन",
                    "कीट-रोग की नियमित निगरानी"
                ],
                "organic_methods": [
                    "नीम आधारित उपचार",
                    "जैविक कीटनाशकों का प्रयोग",
                    "फायदेमंद कीड़ों को संरक्षित करें"
                ],
                "monitoring_schedule": {
                    "daily": "पत्तियों की रंगत देखें",
                    "weekly": "नए कीड़े या रोग के लिए जांच",
                    "monthly": "मिट्टी और पौधे की समग्र सेहत"
                }
            }
        }

    except Exception as e:
        logger.error(f"Error in preventive measures: {e}")
        return {
            "status": "error",
            "message": f"बचाव के उपाय प्राप्त करने में त्रुटि: {str(e)}"
        }