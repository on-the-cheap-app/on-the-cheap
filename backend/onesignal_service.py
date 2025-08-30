import os
import httpx
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class NotificationPayload(BaseModel):
    title: str
    message: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    segments: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    tags: Optional[Dict[str, str]] = None
    buttons: Optional[List[Dict[str, str]]] = None

class OneSignalService:
    def __init__(self):
        self.app_id = os.getenv("ONESIGNAL_APP_ID")
        self.api_key = os.getenv("ONESIGNAL_API_KEY")
        self.base_url = "https://onesignal.com/api/v1"
        
        if not self.app_id or not self.api_key:
            logger.warning("OneSignal credentials not found. Push notifications will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("OneSignal service initialized successfully")

    async def send_notification(self, payload: NotificationPayload) -> Optional[Dict]:
        """Send push notification to specified audience"""
        if not self.enabled:
            logger.warning("OneSignal not configured. Notification not sent.")
            return None

        notification_data = {
            "app_id": self.app_id,
            "headings": {"en": payload.title},
            "contents": {"en": payload.message}
        }

        # Add targeting
        if payload.segments:
            notification_data["included_segments"] = payload.segments
        elif payload.user_ids:
            notification_data["include_external_user_ids"] = payload.user_ids
        else:
            notification_data["included_segments"] = ["All"]

        # Add optional features
        if payload.url:
            notification_data["url"] = payload.url
        
        if payload.image_url:
            notification_data["chrome_web_image"] = payload.image_url
            notification_data["big_picture"] = payload.image_url

        # Add tag filters for targeted messaging
        if payload.tags:
            filters = []
            for key, value in payload.tags.items():
                filters.append({
                    "field": "tag",
                    "key": key,
                    "relation": "=",
                    "value": value
                })
            notification_data["filters"] = filters

        # Add action buttons
        if payload.buttons:
            notification_data["buttons"] = payload.buttons

        try:
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Basic {self.api_key}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/notifications",
                    headers=headers,
                    json=notification_data,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Notification sent successfully. ID: {result.get('id')}, Recipients: {result.get('recipients', 0)}")
                return result
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to send notification: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")
            return None

    async def get_notification_status(self, notification_id: str) -> Optional[Dict]:
        """Get notification delivery status and analytics"""
        if not self.enabled:
            return None

        try:
            headers = {
                "Authorization": f"Basic {self.api_key}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/notifications/{notification_id}",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to get notification status: {e}")
            return None

class RestaurantNotificationService:
    def __init__(self, onesignal_service: OneSignalService):
        self.onesignal = onesignal_service

    async def send_daily_special_notification(self, special_data: Dict, target_users: Optional[List[str]] = None) -> Optional[Dict]:
        """Send notification about new daily special"""
        payload = NotificationPayload(
            title="🍽️ New Daily Special Available!",
            message=f"Try {special_data['name']} - {special_data.get('description', 'Available today only')}",
            url=f"/specials/{special_data['id']}" if special_data.get('id') else None,
            image_url=special_data.get('image_url'),
            segments=["All"] if not target_users else None,
            user_ids=target_users,
            tags={"notify_new_specials": "true"} if not target_users else None,
            buttons=[
                {"id": "view_special", "text": "View Special"},
                {"id": "find_location", "text": "Find Location"}
            ]
        )
        
        return await self.onesignal.send_notification(payload)

    async def send_limited_time_offer(self, offer_data: Dict, target_users: Optional[List[str]] = None) -> Optional[Dict]:
        """Send urgent notification for limited-time offers"""
        payload = NotificationPayload(
            title="⏰ Limited Time Offer!",
            message=f"{offer_data.get('discount', '20')}% off {offer_data.get('item', 'selected items')} - Hurry!",
            url=f"/offers/{offer_data['id']}" if offer_data.get('id') else None,
            image_url=offer_data.get('image_url'),
            segments=["All"] if not target_users else None,
            user_ids=target_users,
            tags={"notify_new_specials": "true"} if not target_users else None
        )
        
        return await self.onesignal.send_notification(payload)

    async def send_favorite_restaurant_update(self, restaurant_data: Dict, user_ids: List[str]) -> Optional[Dict]:
        """Send notification about updates to favorited restaurants"""
        if not user_ids:
            return None
            
        payload = NotificationPayload(
            title="❤️ Your Favorite Restaurant Has News!",
            message=f"{restaurant_data['name']} has new specials available",
            url=f"/restaurants/{restaurant_data['id']}" if restaurant_data.get('id') else None,
            image_url=restaurant_data.get('image_url'),
            user_ids=user_ids,
            buttons=[
                {"id": "view_restaurant", "text": "View Restaurant"},
                {"id": "see_specials", "text": "See Specials"}
            ]
        )
        
        return await self.onesignal.send_notification(payload)

    async def send_daily_digest(self, digest_data: Dict, target_segment: str = "daily_digest") -> Optional[Dict]:
        """Send daily digest of specials"""
        payload = NotificationPayload(
            title="📱 Daily Specials Digest",
            message=f"Today we found {digest_data.get('special_count', 5)} new specials near you!",
            url="/daily-digest" if digest_data.get('has_link') else None,
            segments=[target_segment],
            tags={"notify_daily_digest": "true"}
        )
        
        return await self.onesignal.send_notification(payload)

    async def send_location_based_special(self, special_data: Dict, location: str) -> Optional[Dict]:
        """Send location-based special notification"""
        payload = NotificationPayload(
            title="📍 Special Near You!",
            message=f"New special at {special_data['restaurant_name']} - just {special_data.get('distance', '0.5')} miles away",
            url=f"/restaurants/{special_data['restaurant_id']}" if special_data.get('restaurant_id') else None,
            tags={
                "notify_new_specials": "true",
                "preferred_location": location
            }
        )
        
        return await self.onesignal.send_notification(payload)

# Global service instances
onesignal_service = OneSignalService()
restaurant_notification_service = RestaurantNotificationService(onesignal_service)

def get_onesignal_service() -> OneSignalService:
    return onesignal_service

def get_restaurant_notification_service() -> RestaurantNotificationService:
    return restaurant_notification_service