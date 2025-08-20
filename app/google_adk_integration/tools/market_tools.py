from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import logging
from google.adk.tools.tool_context import ToolContext

from ..mandi_db.database import get_db_session
from ..mandi_db.models import MarketPrice, MarketAnalytics

logger = logging.getLogger(__name__)


async def get_market_prices(
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        days: int = 7,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get current market prices for a specific commodity from database

    Args:
        commodity (str): Name of the commodity (e.g., "Onion", "Tomato")
        state (str, optional): State filter
        district (str, optional): District filter
        days (int): Number of days to fetch data for (default: 7)
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Current prices, trends, and market information
    """
    try:
        with get_db_session() as db:
            # Build query with filters
            query = db.query(MarketPrice).filter(
                and_(
                    MarketPrice.commodity.ilike(f"%{commodity}%"),
                    MarketPrice.arrival_date >= datetime.now() - timedelta(days=days),
                    MarketPrice.is_active == True
                )
            )

            if state:
                query = query.filter(MarketPrice.state.ilike(f"%{state}%"))
            if district:
                query = query.filter(MarketPrice.district.ilike(f"%{district}%"))

            # Get results ordered by latest date and best price
            prices = query.order_by(
                desc(MarketPrice.arrival_date),
                desc(MarketPrice.modal_price)
            ).limit(20).all()

            if not prices:
                result = {
                    "status": "no_data",
                    "message": f"{commodity} के लिए हाल की कीमत डेटा उपलब्ध नहीं है",
                    "commodity": commodity,
                    "suggestions": [
                        "कमोडिटी का नाम सही से लिखें (जैसे: प्याज, टमाटर, आलू)",
                        "अधिक दिनों के लिए खोजें",
                        "राज्य या जिला फिल्टर हटाएं"
                    ]
                }

                # Store in session context
                if tool_context:
                    tool_context.state["last_commodity_search"] = commodity
                    tool_context.state["last_search_result"] = "no_data"

                return result

            # Process and organize results
            market_data = []
            total_price = 0
            min_price = float('inf')
            max_price = 0

            for price in prices:
                market_info = {
                    "market": price.market,
                    "district": price.district,
                    "state": price.state,
                    "modal_price": price.modal_price,
                    "min_price": price.min_price,
                    "max_price": price.max_price,
                    "arrival_date": price.arrival_date.strftime("%d-%m-%Y"),
                    "trend": price.trend,
                    "price_change": price.price_change,
                    "percentage_change": round(price.percentage_change, 2),
                    "variety": price.variety or "सामान्य",
                    "grade": price.grade or "मध्यम"
                }
                market_data.append(market_info)

                # Calculate summary stats
                total_price += price.modal_price
                min_price = min(min_price, price.modal_price)
                max_price = max(max_price, price.modal_price)

            # Summary statistics
            avg_price = round(total_price / len(prices), 2)
            price_range = max_price - min_price

            # Trend analysis
            up_trends = sum(1 for p in prices if p.trend == 'up')
            down_trends = sum(1 for p in prices if p.trend == 'down')

            overall_trend = "stable"
            if up_trends > down_trends and up_trends > len(prices) * 0.4:
                overall_trend = "up"
            elif down_trends > up_trends and down_trends > len(prices) * 0.4:
                overall_trend = "down"

            # Generate recommendations
            recommendations = []
            if overall_trend == "up":
                recommendations.extend([
                    f"{commodity} की कीमतें बढ़ रही हैं - बेचने का अच्छा समय है",
                    "गुणवत्ता बनाए रखें और बेहतर दाम की प्रतीक्षा करें"
                ])
            elif overall_trend == "down":
                recommendations.extend([
                    f"{commodity} की कीमतें गिर रही हैं - जल्दी बेचने पर विचार करें",
                    "नुकसान से बचने के लिए तुरंत मार्केट में जाएं"
                ])
            else:
                recommendations.extend([
                    f"{commodity} की कीमतें स्थिर हैं - नियमित बिक्री करें",
                    "बाजार रिसर्च करके बेहतर मंडी चुनें"
                ])

            # Add price-based recommendations
            if price_range > avg_price * 0.3:
                recommendations.append(f"मंडियों में ₹{price_range:.0f} तक का अंतर है - बेहतर मंडी चुनें")

            result = {
                "status": "success",
                "commodity": commodity,
                "data_date": datetime.now().strftime("%d-%m-%Y %H:%M"),

                "price_summary": {
                    "average_price": avg_price,
                    "highest_price": max_price,
                    "lowest_price": min_price,
                    "price_range": round(price_range, 2),
                    "total_markets": len(set(f"{p.market}-{p.district}" for p in prices))
                },

                "overall_trend": overall_trend,
                "trend_stats": {
                    "up_trend_markets": up_trends,
                    "down_trend_markets": down_trends,
                    "stable_markets": len(prices) - up_trends - down_trends
                },

                "best_markets": market_data[:5],  # Top 5 markets
                "all_markets": market_data,
                "recommendations": recommendations
            }

            # Store in session context
            if tool_context:
                tool_context.state["last_commodity_search"] = commodity
                tool_context.state["last_search_result"] = "success"
                tool_context.state["last_price_data"] = result

            return result

    except Exception as e:
        logger.error(f"Error fetching market prices: {e}")
        error_result = {
            "status": "error",
            "message": f"मार्केट डेटा लाने में त्रुटि: {str(e)}",
            "commodity": commodity
        }

        # Store error in session context
        if tool_context:
            tool_context.state["last_commodity_search"] = commodity
            tool_context.state["last_search_result"] = "error"

        return error_result


async def get_price_analysis(
        commodity: str,
        analysis_days: int = 30,
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get detailed price analysis and trends for a commodity

    Args:
        commodity (str): Name of the commodity
        analysis_days (int): Number of days for analysis (default: 30)
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Comprehensive price analysis with trends and patterns
    """
    try:
        with get_db_session() as db:
            # First check if we have recent analytics
            analytics = db.query(MarketAnalytics).filter(
                and_(
                    MarketAnalytics.commodity.ilike(f"%{commodity}%"),
                    MarketAnalytics.analysis_date >= datetime.now() - timedelta(days=3)
                )
            ).order_by(desc(MarketAnalytics.analysis_date)).first()

            if analytics:
                # Use existing analytics
                price_history = json.loads(analytics.price_history) if analytics.price_history else []
                recommendations = json.loads(analytics.recommendations) if analytics.recommendations else []

                result = {
                    "status": "success",
                    "commodity": commodity,
                    "analysis_date": analytics.analysis_date.strftime("%d-%m-%Y"),
                    "data_source": "analytics",

                    "price_statistics": {
                        "average_price": analytics.avg_price,
                        "highest_price": analytics.highest_price,
                        "lowest_price": analytics.lowest_price,
                        "price_volatility": round(analytics.price_volatility, 2),
                        "total_markets": analytics.total_markets
                    },

                    "trend_analysis": {
                        "weekly_trend": analytics.weekly_trend,
                        "monthly_trend": analytics.monthly_trend,
                        "trend_confidence": "high"
                    },

                    "predictions": {
                        "7_day_price": analytics.predicted_price_7d,
                        "14_day_price": analytics.predicted_price_14d,
                        "confidence": round(analytics.prediction_confidence, 1)
                    },

                    "top_market": {
                        "name": analytics.top_market,
                        "price": analytics.top_market_price
                    },

                    "price_history": price_history[-14:],  # Last 14 days
                    "recommendations": recommendations
                }
            else:
                # Generate analysis from raw data
                result = await generate_live_analysis(db, commodity, analysis_days)

            # Store in session context
            if tool_context:
                tool_context.state["last_analysis_commodity"] = commodity
                tool_context.state["last_analysis_result"] = result

            return result

    except Exception as e:
        logger.error(f"Error in price analysis: {e}")
        error_result = {
            "status": "error",
            "message": f"कीमत विश्लेषण में त्रुटि: {str(e)}",
            "commodity": commodity
        }

        # Store error in session context
        if tool_context:
            tool_context.state["last_analysis_commodity"] = commodity
            tool_context.state["last_analysis_result"] = "error"

        return error_result


async def get_selling_advice(
        commodity: str,
        quantity: Optional[float] = None,
        quality_grade: str = "medium",
        urgency: str = "normal",
        tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get selling advice for a commodity

    Args:
        commodity (str): Name of the commodity
        quantity (float, optional): Quantity to sell in quintals
        quality_grade (str): Quality grade - "high", "medium", "low"
        urgency (str): Selling urgency - "urgent", "normal", "flexible"
        tool_context (ToolContext): Optional session context

    Returns:
        Dict: Selling strategy and recommendations
    """
    try:
        with get_db_session() as db:
            # Get recent market data
            recent_prices = db.query(MarketPrice).filter(
                and_(
                    MarketPrice.commodity.ilike(f"%{commodity}%"),
                    MarketPrice.arrival_date >= datetime.now() - timedelta(days=5),
                    MarketPrice.is_active == True
                )
            ).order_by(desc(MarketPrice.modal_price)).limit(10).all()

            if not recent_prices:
                result = {
                    "status": "no_data",
                    "message": f"{commodity} के लिए हाल की मार्केट जानकारी उपलब्ध नहीं है"
                }

                # Store in session context
                if tool_context:
                    tool_context.state["last_advice_commodity"] = commodity
                    tool_context.state["last_advice_result"] = "no_data"

                return result

            # Quality price adjustment
            quality_multiplier = {"high": 1.15, "medium": 1.0, "low": 0.85}[quality_grade]

            # Calculate best options
            best_markets = []
            for price in recent_prices:
                adjusted_price = price.modal_price * quality_multiplier
                best_markets.append({
                    "market": price.market,
                    "district": price.district,
                    "state": price.state,
                    "adjusted_price": round(adjusted_price, 2),
                    "original_price": price.modal_price,
                    "trend": price.trend,
                    "date": price.arrival_date.strftime("%d-%m-%Y"),
                    "potential_revenue": round(adjusted_price * quantity, 2) if quantity else None
                })

            # Generate timing advice
            up_trends = sum(1 for p in recent_prices if p.trend == 'up')
            down_trends = sum(1 for p in recent_prices if p.trend == 'down')

            timing_advice = generate_timing_advice(up_trends, down_trends, len(recent_prices), urgency)

            # Financial projections
            avg_price = sum(m["adjusted_price"] for m in best_markets) / len(best_markets)
            best_price = max(m["adjusted_price"] for m in best_markets)

            financial_summary = {
                "average_expected_price": round(avg_price, 2),
                "best_possible_price": round(best_price, 2),
                "quality_adjustment": f"{((quality_multiplier - 1) * 100):+.0f}%"
            }

            if quantity:
                financial_summary.update({
                    "quantity_quintals": quantity,
                    "estimated_revenue": round(avg_price * quantity, 2),
                    "best_case_revenue": round(best_price * quantity, 2),
                    "revenue_difference": round((best_price - avg_price) * quantity, 2)
                })

            # Strategy recommendations
            strategy = generate_selling_strategy(timing_advice, quality_grade, best_markets, urgency)

            result = {
                "status": "success",
                "commodity": commodity,
                "quality_grade": quality_grade,
                "urgency_level": urgency,
                "analysis_date": datetime.now().strftime("%d-%m-%Y %H:%M"),

                "timing_advice": timing_advice,
                "financial_summary": financial_summary,
                "best_markets": best_markets[:5],
                "strategy_recommendations": strategy,

                "summary": {
                    "action": timing_advice["action"],
                    "reason": timing_advice["reason"],
                    "best_market": f"{best_markets[0]['market']}, {best_markets[0]['district']}",
                    "expected_price": financial_summary["average_expected_price"]
                }
            }

            # Store in session context
            if tool_context:
                tool_context.state["last_advice_commodity"] = commodity
                tool_context.state["last_advice_result"] = result
                tool_context.state["last_advice_params"] = {
                    "quantity": quantity,
                    "quality_grade": quality_grade,
                    "urgency": urgency
                }

            return result

    except Exception as e:
        logger.error(f"Error generating selling advice: {e}")
        error_result = {
            "status": "error",
            "message": f"सेलिंग सलाह तैयार करने में त्रुटि: {str(e)}",
            "commodity": commodity
        }

        # Store error in session context
        if tool_context:
            tool_context.state["last_advice_commodity"] = commodity
            tool_context.state["last_advice_result"] = "error"

        return error_result


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_live_analysis(db, commodity: str, days: int) -> Dict[str, Any]:
    """Generate analysis from raw market data when analytics not available"""

    # Get historical data
    historical_prices = db.query(MarketPrice).filter(
        and_(
            MarketPrice.commodity.ilike(f"%{commodity}%"),
            MarketPrice.arrival_date >= datetime.now() - timedelta(days=days),
            MarketPrice.is_active == True
        )
    ).order_by(MarketPrice.arrival_date).all()

    if len(historical_prices) < 5:
        return {
            "status": "insufficient_data",
            "message": f"{commodity} के लिए विश्लेषण हेतु पर्याप्त डेटा नहीं है ({len(historical_prices)} records)",
            "suggestion": "कम दिनों के लिए खोजें या कमोडिटी का नाम बदलें"
        }

    # Calculate statistics
    prices = [p.modal_price for p in historical_prices]
    avg_price = sum(prices) / len(prices)
    max_price = max(prices)
    min_price = min(prices)

    # Calculate volatility (standard deviation)
    variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
    volatility = variance ** 0.5

    # Trend analysis
    recent_prices = prices[-7:] if len(prices) >= 7 else prices
    older_prices = prices[:-7] if len(prices) >= 14 else prices[:len(prices) // 2]

    recent_avg = sum(recent_prices) / len(recent_prices)
    older_avg = sum(older_prices) / len(older_prices) if older_prices else recent_avg

    trend = "stable"
    if recent_avg > older_avg * 1.05:
        trend = "up"
    elif recent_avg < older_avg * 0.95:
        trend = "down"

    # Generate price history for chart
    price_history = []
    for i, price_record in enumerate(historical_prices[-14:]):  # Last 14 days
        price_history.append({
            "date": price_record.arrival_date.strftime("%d-%m-%Y"),
            "price": price_record.modal_price,
            "market": price_record.market
        })

    # Simple predictions
    trend_factor = 1.0
    if trend == "up":
        trend_factor = 1.02
    elif trend == "down":
        trend_factor = 0.98

    predicted_7d = avg_price * trend_factor
    predicted_14d = avg_price * (trend_factor ** 2)

    # Recommendations
    recommendations = [
        f"औसत कीमत पिछले {days} दिनों में ₹{avg_price:.0f} प्रति क्विंटल रही है",
        f"कीमत में अधिकतम ₹{max_price:.0f} और न्यूनतम ₹{min_price:.0f} का अंतर देखा गया",
        f"बाजार की स्थिति: {trend}",
    ]

    if volatility > avg_price * 0.1:
        recommendations.append("कीमतों में अधिक उतार-चढ़ाव है - सही समय का इंतजार करें")

    if trend == "up":
        recommendations.append("कीमतें बढ़ने की प्रवृत्ति दिखा रही हैं")
    elif trend == "down":
        recommendations.append("कीमतों में गिरावट का रुझान है - जल्दी बेचने पर विचार करें")

    return {
        "status": "success",
        "commodity": commodity,
        "analysis_date": datetime.now().strftime("%d-%m-%Y"),
        "data_source": "live_calculation",
        "analysis_period": f"{days} दिन",
        "data_points": len(historical_prices),

        "price_statistics": {
            "average_price": round(avg_price, 2),
            "highest_price": max_price,
            "lowest_price": min_price,
            "price_volatility": round(volatility, 2),
            "total_markets": len(set(f"{p.market}-{p.district}" for p in historical_prices))
        },

        "trend_analysis": {
            "overall_trend": trend,
            "recent_avg": round(recent_avg, 2),
            "historical_avg": round(older_avg, 2),
            "trend_confidence": "medium"
        },

        "predictions": {
            "7_day_price": round(predicted_7d, 2),
            "14_day_price": round(predicted_14d, 2),
            "confidence": 65.0,
            "note": "सरल गणना पर आधारित"
        },

        "price_history": price_history,
        "recommendations": recommendations
    }


def generate_timing_advice(up_trends: int, down_trends: int, total_markets: int, urgency: str) -> Dict[str, Any]:
    """Generate timing advice based on market trends and urgency"""

    if urgency == "urgent":
        return {
            "action": "sell_immediately",
            "reason": "तत्काल बिक्री की आवश्यकता के कारण",
            "timeline": "आज ही",
            "confidence": "high"
        }

    # Calculate trend strength
    up_percentage = (up_trends / total_markets) * 100
    down_percentage = (down_trends / total_markets) * 100

    if up_percentage > 60:
        action = "wait_few_days" if urgency == "flexible" else "sell_soon"
        reason = "अधिकतर मंडियों में कीमतें बढ़ रही हैं"
        timeline = "2-4 दिन" if urgency == "flexible" else "1-2 दिन"
    elif down_percentage > 60:
        action = "sell_immediately"
        reason = "अधिकतर मंडियों में कीमतें गिर रही हैं"
        timeline = "आज या कल"
    else:
        action = "flexible_timing"
        reason = "कीमतें मिश्रित रुझान दिखा रही हैं"
        timeline = "अगले 3-5 दिन में"

    return {
        "action": action,
        "reason": reason,
        "timeline": timeline,
        "confidence": "medium",
        "market_trend_summary": f"{up_percentage:.0f}% मंडियों में वृद्धि, {down_percentage:.0f}% में गिरावट"
    }


def generate_selling_strategy(timing_advice: Dict, quality_grade: str, markets: List, urgency: str) -> List[str]:
    """Generate comprehensive selling strategy"""

    strategies = []

    # Timing strategy
    if timing_advice["action"] == "wait_few_days":
        strategies.append("कुछ दिन प्रतीक्षा करें - कीमत बढ़ने की संभावना है")
    elif timing_advice["action"] == "sell_immediately":
        strategies.append("तुरंत बेच दें - देरी से कम दाम मिल सकते हैं")
    else:
        strategies.append("अपनी सुविधा के अनुसार बेच सकते हैं")

    # Quality strategy
    if quality_grade == "high":
        strategies.append("उच्च गुणवत्ता के कारण 10-15% अधिक दाम की मांग करें")
    elif quality_grade == "low":
        strategies.append("गुणवत्ता के कारण जल्दी बेचें - देरी से और कम दाम मिलेंगे")

    # Market selection strategy
    if len(markets) > 1:
        price_diff = markets[0]["adjusted_price"] - markets[-1]["adjusted_price"]
        if price_diff > 20:
            strategies.append(f"सबसे अच्छी मंडी में ₹{price_diff:.0f} प्रति क्विंटल अधिक मिल सकता है")

    # Add general advice
    strategies.extend([
        "मंडी पहुंचने से पहले फोन करके कीमत कन्फर्म करें",
        "सुबह 6-10 बजे का समय सबसे अच्छा है",
        "ट्रांसपोर्ट कॉस्ट को ध्यान में रखकर मंडी चुनें"
    ])

    return strategies