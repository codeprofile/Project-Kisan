import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import json
import asyncio
import os
from ..mandi_db.database import get_db_session
from ..mandi_db.models import MarketPrice, MarketAnalytics, DataSyncLog



logger = logging.getLogger(__name__)


class CoreMarketDataSyncService:
    """Simplified but complete data synchronization service"""

    def __init__(self):
        self.api_key = os.environ.get("MANDI_API_KEY")
        self.resource_id = '9ef84268-d588-465a-a308-a864a43d0070'
        self.base_url = f'https://api.data.gov.in/resource/{self.resource_id}'
        self.max_retries = 3
        self.retry_delay = 2

    async def sync_market_data(self, days_back: int = 7, force_full_sync: bool = False) -> Dict[str, Any]:
        """Main sync function - gets data and processes it"""
        start_time = time.time()

        try:
            with get_db_session() as db:
                # Determine sync type
                last_sync = db.query(DataSyncLog).filter(
                    DataSyncLog.status == 'success'
                ).order_by(desc(DataSyncLog.sync_date)).first()

                sync_type = 'full' if not last_sync or force_full_sync else 'incremental'

                logger.info(f"Starting {sync_type} sync for {days_back} days")

                # Step 1: Fetch data from API
                all_records = await self._fetch_market_data(days_back)

                if not all_records:
                    raise Exception("No data received from API")

                # Step 2: Process and store data
                process_stats = await self._process_and_store_data(db, all_records)

                # Step 3: Calculate trends
                trend_stats = await self._calculate_price_trends(db)

                # Step 4: Generate analytics
                analytics_stats = await self._generate_market_analytics(db)

                duration = time.time() - start_time

                # Log successful sync
                sync_log = DataSyncLog(
                    sync_date=datetime.now(),
                    sync_type=sync_type,
                    status='success',
                    records_processed=len(all_records),
                    records_inserted=process_stats['inserted'],
                    records_updated=process_stats['updated'],
                    duration_seconds=duration
                )
                db.add(sync_log)

                logger.info(f"Sync completed successfully in {duration:.2f} seconds")

                return {
                    'status': 'success',
                    'sync_type': sync_type,
                    'duration': duration,
                    'records_fetched': len(all_records),
                    'records_inserted': process_stats['inserted'],
                    'records_updated': process_stats['updated'],
                    'trends_calculated': trend_stats['processed'],
                    'analytics_generated': analytics_stats['commodities']
                }

        except Exception as e:
            # Log failed sync
            with get_db_session() as db:
                sync_log = DataSyncLog(
                    sync_date=datetime.now(),
                    sync_type=sync_type if 'sync_type' in locals() else 'unknown',
                    status='failed',
                    error_message=str(e),
                    duration_seconds=time.time() - start_time
                )
                db.add(sync_log)

            logger.error(f"Sync failed: {e}")
            raise

    async def _fetch_market_data(self, days_back: int) -> List[Dict]:
        """Fetch data from Government API for specified days"""
        all_records = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%d-%m-%Y")

            try:
                daily_records = await self._fetch_api_data_for_date(date_str)
                all_records.extend(daily_records)
                logger.info(f"Fetched {len(daily_records)} records for {date_str}")

                # Rate limiting - be nice to the government API
                await asyncio.sleep(1)

            except Exception as e:
                logger.warning(f"Failed to fetch data for {date_str}: {e}")
                # Continue with other dates even if one fails

            current_date += timedelta(days=1)

        logger.info(f"Total records fetched: {len(all_records)}")
        return all_records

    async def _fetch_api_data_for_date(self, date_str: str) -> List[Dict]:
        """Fetch data from API for a specific date"""
        records = []
        offset = 0
        limit = 1000

        while True:
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'limit': limit,
                'offset': offset,
                'filters[arrival_date]': date_str
            }

            for attempt in range(self.max_retries):
                try:
                    response = requests.get(self.base_url, params=params, timeout=30)
                    response.raise_for_status()

                    data = response.json()
                    batch_records = data.get('records', [])

                    if not batch_records:
                        return records  # No more data for this date

                    records.extend(batch_records)
                    offset += limit

                    # If we got less than limit, we've reached the end
                    if len(batch_records) < limit:
                        return records

                    break  # Success, exit retry loop

                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.error(f"API request failed after {self.max_retries} attempts: {e}")
                        return records

                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        return records

    async def _process_and_store_data(self, db: Session, records: List[Dict]) -> Dict[str, int]:
        """Process and store records in database"""
        stats = {'inserted': 0, 'updated': 0, 'skipped': 0}

        for record in records:
            try:
                # Clean and validate the record
                cleaned = self._clean_record(record)
                if not cleaned:
                    stats['skipped'] += 1
                    continue

                # Check if record already exists
                existing = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.state == cleaned['state'],
                        MarketPrice.district == cleaned['district'],
                        MarketPrice.market == cleaned['market'],
                        MarketPrice.commodity == cleaned['commodity'],
                        MarketPrice.arrival_date == cleaned['arrival_date']
                    )
                ).first()

                if existing:
                    # Update existing record
                    for key, value in cleaned.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                    stats['updated'] += 1
                else:
                    # Insert new record
                    new_price = MarketPrice(**cleaned)
                    db.add(new_price)
                    stats['inserted'] += 1

                # Commit in batches for performance
                if (stats['inserted'] + stats['updated']) % 50 == 0:
                    db.commit()

            except Exception as e:
                logger.warning(f"Failed to process record: {e}")
                stats['skipped'] += 1
                continue

        # Final commit
        db.commit()

        logger.info(f"Data processing completed: {stats}")
        return stats

    def _clean_record(self, record: Dict) -> Dict[str, Any]:
        """Clean and validate a single record"""
        try:
            # Parse arrival date - handle multiple formats
            arrival_date_str = record.get('arrival_date', '')
            arrival_date = None

            # Try different date formats that the API might return
            date_formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%y', '%d/%m/%y']

            for fmt in date_formats:
                try:
                    arrival_date = datetime.strptime(arrival_date_str, fmt)
                    break
                except ValueError:
                    continue

            if not arrival_date:
                logger.warning(f"Could not parse date: {arrival_date_str}")
                return None

            # Convert prices to float, handle None/empty values
            min_price = self._safe_float(record.get('min_price', 0))
            max_price = self._safe_float(record.get('max_price', 0))
            modal_price = self._safe_float(record.get('modal_price', 0))

            # Validate essential fields
            required_fields = ['state', 'district', 'market', 'commodity']
            for field in required_fields:
                if not record.get(field) or not record[field].strip():
                    return None

            # Modal price must be positive
            if modal_price <= 0:
                return None

            # Ensure min/max are logical
            if min_price > modal_price:
                min_price = modal_price
            if max_price < modal_price:
                max_price = modal_price

            return {
                'state': record['state'].strip(),
                'district': record['district'].strip(),
                'market': record['market'].strip(),
                'commodity': record['commodity'].strip(),
                'variety': record.get('variety', '').strip() or None,
                'grade': record.get('grade', '').strip() or None,
                'arrival_date': arrival_date,
                'min_price': min_price,
                'max_price': max_price,
                'modal_price': modal_price,
                'is_active': True
            }

        except Exception as e:
            logger.warning(f"Record cleaning failed: {e}")
            return None

    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    async def _calculate_price_trends(self, db: Session) -> Dict[str, int]:
        """Calculate price trends for recent data"""
        processed = 0

        # Get unique commodities from recent data
        recent_commodities = db.query(MarketPrice.commodity).filter(
            MarketPrice.arrival_date >= datetime.now() - timedelta(days=7)
        ).distinct().all()

        for (commodity,) in recent_commodities:
            try:
                # Get last 14 days of data for this commodity
                commodity_prices = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity == commodity,
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=14)
                    )
                ).order_by(MarketPrice.arrival_date.desc()).all()

                if len(commodity_prices) < 2:
                    continue

                # Calculate trends for each record
                for i, record in enumerate(commodity_prices):
                    if i < len(commodity_prices) - 1:
                        # Compare with previous day
                        previous_record = commodity_prices[i + 1]
                        current_price = record.modal_price
                        previous_price = previous_record.modal_price

                        if previous_price > 0:
                            price_change = current_price - previous_price
                            percentage_change = (price_change / previous_price) * 100

                            # Determine trend
                            if percentage_change > 2:
                                trend = 'up'
                            elif percentage_change < -2:
                                trend = 'down'
                            else:
                                trend = 'stable'

                            # Update record
                            record.price_change = round(price_change, 2)
                            record.percentage_change = round(percentage_change, 2)
                            record.trend = trend

                            processed += 1

            except Exception as e:
                logger.warning(f"Trend calculation failed for {commodity}: {e}")

        db.commit()
        logger.info(f"Trends calculated for {processed} records")
        return {'processed': processed}

    async def _generate_market_analytics(self, db: Session) -> Dict[str, int]:
        """Generate market analytics for commodities"""
        commodities_processed = 0
        analysis_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get unique commodities with recent data
        recent_commodities = db.query(MarketPrice.commodity).filter(
            MarketPrice.arrival_date >= datetime.now() - timedelta(days=30)
        ).distinct().all()

        for (commodity,) in recent_commodities:
            try:
                # Get recent data for this commodity
                commodity_data = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity == commodity,
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=30)
                    )
                ).all()

                if len(commodity_data) < 5:
                    continue

                # Calculate analytics
                prices = [r.modal_price for r in commodity_data]
                avg_price = sum(prices) / len(prices)
                highest_price = max(prices)
                lowest_price = min(prices)

                # Calculate volatility (standard deviation)
                variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
                volatility = variance ** 0.5

                # Find top market
                top_market_record = max(commodity_data, key=lambda x: x.modal_price)

                # Calculate trends
                weekly_data = [r for r in commodity_data if r.arrival_date >= datetime.now() - timedelta(days=7)]
                weekly_trend = self._calculate_trend_direction(weekly_data)
                monthly_trend = self._calculate_trend_direction(commodity_data)

                # Simple predictions
                predicted_7d, predicted_14d, confidence = self._predict_prices(commodity_data)

                # Generate price history
                price_history = self._generate_price_history(commodity_data)

                # Generate recommendations
                recommendations = self._generate_recommendations(weekly_trend, avg_price, volatility)

                # Check if analytics already exist for today
                existing = db.query(MarketAnalytics).filter(
                    and_(
                        MarketAnalytics.commodity == commodity,
                        MarketAnalytics.analysis_date == analysis_date
                    )
                ).first()

                analytics_data = {
                    'commodity': commodity,
                    'analysis_date': analysis_date,
                    'avg_price': round(avg_price, 2),
                    'highest_price': highest_price,
                    'lowest_price': lowest_price,
                    'price_volatility': round(volatility, 2),
                    'total_markets': len(set(f"{r.market}-{r.district}" for r in commodity_data)),
                    'top_market': f"{top_market_record.market}, {top_market_record.district}",
                    'top_market_price': top_market_record.modal_price,
                    'weekly_trend': weekly_trend,
                    'monthly_trend': monthly_trend,
                    'predicted_price_7d': predicted_7d,
                    'predicted_price_14d': predicted_14d,
                    'prediction_confidence': confidence,
                    'price_history': json.dumps(price_history),
                    'recommendations': json.dumps(recommendations)
                }

                if existing:
                    # Update existing analytics
                    for key, value in analytics_data.items():
                        setattr(existing, key, value)
                else:
                    # Create new analytics
                    analytics = MarketAnalytics(**analytics_data)
                    db.add(analytics)

                commodities_processed += 1

            except Exception as e:
                logger.warning(f"Analytics generation failed for {commodity}: {e}")

        db.commit()
        logger.info(f"Analytics generated for {commodities_processed} commodities")
        return {'commodities': commodities_processed}

    def _calculate_trend_direction(self, data: List[MarketPrice]) -> str:
        """Calculate overall trend direction from price data"""
        if len(data) < 2:
            return 'stable'

        # Sort by date
        sorted_data = sorted(data, key=lambda x: x.arrival_date)

        # Compare first half with second half
        mid_point = len(sorted_data) // 2
        first_half_avg = sum(r.modal_price for r in sorted_data[:mid_point]) / mid_point
        second_half_avg = sum(r.modal_price for r in sorted_data[mid_point:]) / (len(sorted_data) - mid_point)

        change_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100

        if change_percentage > 5:
            return 'up'
        elif change_percentage < -5:
            return 'down'
        else:
            return 'stable'

    def _predict_prices(self, data: List[MarketPrice]) -> tuple:
        """Simple price prediction using recent trends"""
        if len(data) < 3:
            avg_price = sum(r.modal_price for r in data) / len(data)
            return avg_price, avg_price, 50.0

        # Sort by date
        sorted_data = sorted(data, key=lambda x: x.arrival_date)

        # Get recent trend
        recent_data = sorted_data[-7:] if len(sorted_data) >= 7 else sorted_data
        prices = [r.modal_price for r in recent_data]

        # Simple linear trend
        if len(prices) >= 3:
            # Calculate average change per day
            daily_changes = []
            for i in range(1, len(prices)):
                daily_changes.append(prices[i] - prices[i - 1])

            avg_daily_change = sum(daily_changes) / len(daily_changes)
            current_price = prices[-1]

            predicted_7d = current_price + (avg_daily_change * 7)
            predicted_14d = current_price + (avg_daily_change * 14)

            # Calculate confidence based on trend consistency
            price_variance = sum((p - sum(prices) / len(prices)) ** 2 for p in prices) / len(prices)
            volatility = (price_variance ** 0.5) / (sum(prices) / len(prices))
            confidence = max(40, min(85, 80 - (volatility * 100)))

        else:
            avg_price = sum(prices) / len(prices)
            predicted_7d = avg_price
            predicted_14d = avg_price
            confidence = 50.0

        return round(predicted_7d, 2), round(predicted_14d, 2), round(confidence, 1)

    def _generate_price_history(self, data: List[MarketPrice]) -> List[Dict]:
        """Generate price history for the last 14 days"""
        # Group by date
        date_prices = {}
        for record in data:
            date_key = record.arrival_date.strftime('%Y-%m-%d')
            if date_key not in date_prices:
                date_prices[date_key] = []
            date_prices[date_key].append(record.modal_price)

        # Calculate average price per date
        history = []
        for date_key in sorted(date_prices.keys())[-14:]:  # Last 14 days
            prices = date_prices[date_key]
            avg_price = sum(prices) / len(prices)
            history.append({
                'date': date_key,
                'price': round(avg_price, 2),
                'records': len(prices)
            })

        return history

    def _generate_recommendations(self, trend: str, avg_price: float, volatility: float) -> List[str]:
        """Generate market recommendations"""
        recommendations = []

        if trend == 'up':
            recommendations.extend([
                "कीमतें बढ़ रही हैं - बेचने का अच्छा समय है",
                "मांग अच्छी है - गुणवत्ता पर ध्यान दें",
                "थोड़ा इंतज़ार करने से बेहतर दाम मिल सकते हैं"
            ])
        elif trend == 'down':
            recommendations.extend([
                "कीमतें गिर रही हैं - जल्दी बेचने पर विचार करें",
                "बाजार में अधिक सप्लाई है - तुरंत बेचें",
                "भंडारण लागत बचाने के लिए तत्काल बिक्री करें"
            ])
        else:
            recommendations.extend([
                "कीमतें स्थिर हैं - नियमित बिक्री करें",
                "मार्केट रिसर्च करके बेहतर मंडी चुनें",
                "गुणवत्ता पर फोकस करके बेहतर दाम लें"
            ])

        # Add volatility-based recommendations
        if volatility > avg_price * 0.15:
            recommendations.append("कीमतों में अधिक उतार-चढ़ाव है - सही समय का इंतज़ार करें")

        return recommendations

    # Public methods for manual operations
    async def sync_today_data(self) -> Dict[str, Any]:
        """Sync only today's data - for quick updates"""
        return await self.sync_market_data(days_back=1)

    async def sync_week_data(self) -> Dict[str, Any]:
        """Sync last week's data"""
        return await self.sync_market_data(days_back=7)

    async def force_full_sync(self, days_back: int = 30) -> Dict[str, Any]:
        """Force a complete resync"""
        return await self.sync_market_data(days_back=days_back, force_full_sync=True)