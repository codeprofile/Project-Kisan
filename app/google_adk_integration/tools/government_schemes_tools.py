from typing import Dict, Any, Optional
import logging
from google.adk.tools.tool_context import ToolContext
from ..services.government_schemes_service import GovernmentSchemesService

logger = logging.getLogger(__name__)

# Initialize the service
government_schemes_service = GovernmentSchemesService()


async def search_government_schemes(
        query: str,
        state: Optional[str] = None,
        scheme_type: str = "all",
        farmer_category: Optional[str] = None,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """Search for government schemes based on farmer's needs"""
    try:
        logger.info(f"Searching schemes for: {query}, state: {state}")

        # Search schemes using AI service
        result = await government_schemes_service.search_schemes(
            query=query,
            state=state,
            scheme_type=scheme_type,
            farmer_category=farmer_category
        )

        # Store search context for follow-up questions
        if tool_context and result.get("status") == "success":
            tool_context.state["last_scheme_search"] = query
            tool_context.state["last_search_query"] = query
            tool_context.state["user_state"] = state
            tool_context.state["farmer_category"] = farmer_category

            logger.info(f"AI scheme search completed for: {query}")

        return result

    except Exception as e:
        logger.error(f"Error searching schemes: {e}")
        return {
            "status": "error",
            "message": f"योजना खोजने में त्रुटि: {str(e)}। कृपया दोबारा कोशिश करें।"
        }


async def get_scheme_details(
        scheme_name: str,
        state: Optional[str] = None,
        include_application_info: bool = True,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """Get detailed information about a specific government scheme"""
    try:
        logger.info(f"Getting details for scheme: {scheme_name}")

        # Get detailed scheme information
        result = await government_schemes_service.get_scheme_details(
            scheme_name=scheme_name,
            state=state,
            include_application_info=include_application_info
        )

        # Store scheme context for related questions
        if tool_context and result.get("status") == "success":
            tool_context.state["current_scheme"] = scheme_name
            tool_context.state["last_scheme_query"] = scheme_name
            tool_context.state["last_viewed_scheme"] = scheme_name

            logger.info(f"Retrieved AI details for scheme: {scheme_name}")

        return result

    except Exception as e:
        logger.error(f"Error getting scheme details: {e}")
        return {
            "status": "error",
            "message": f"योजना विवरण प्राप्त करने में त्रुटि: {str(e)}"
        }


async def check_eligibility(
        scheme_name: str,
        farmer_profile: Dict[str, Any],
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """Check farmer's eligibility for a specific scheme"""
    try:
        logger.info(f"Checking eligibility for {scheme_name}")

        # Check eligibility using AI service
        result = await government_schemes_service.check_eligibility(
            scheme_name=scheme_name,
            farmer_profile=farmer_profile
        )

        # Store eligibility context
        if tool_context:
            tool_context.state["last_eligibility_check"] = {
                "scheme": scheme_name,
                "profile_provided": bool(farmer_profile),
                "check_completed": True
            }

            logger.info(f"AI eligibility check completed for {scheme_name}")

        return result

    except Exception as e:
        logger.error(f"Error checking eligibility: {e}")
        return {
            "status": "error",
            "message": f"पात्रता जांच में त्रुटि: {str(e)}"
        }


async def get_application_process(
        scheme_name: str,
        state: Optional[str] = None,
        application_type: str = "online",
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """Get step-by-step application process for a scheme"""
    try:
        logger.info(f"Getting application process for: {scheme_name}")

        # Get application process information
        result = await government_schemes_service.get_application_process(
            scheme_name=scheme_name,
            state=state,
            application_type=application_type
        )

        # Store application context
        if tool_context and result.get("status") == "success":
            tool_context.state["current_application"] = {
                "scheme": scheme_name,
                "state": state,
                "type": application_type,
                "guidance_provided": True
            }

            logger.info(f"AI application process provided for: {scheme_name}")

        return result

    except Exception as e:
        logger.error(f"Error getting application process: {e}")
        return {
            "status": "error",
            "message": f"आवेदन प्रक्रिया प्राप्त करने में त्रुटि: {str(e)}"
        }
