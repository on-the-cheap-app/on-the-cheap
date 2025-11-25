"""
Digital Coupon System for Restaurant Owners

This service provides:
- Coupon creation and management for restaurant owners
- QR code generation for redemption
- Analytics and performance tracking
- Customer coupon discovery and redemption
- Revenue tracking and ROI metrics
"""

import logging
import qrcode
import io
import base64
import uuid
import os
import random
import string
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CouponType(Enum):
    PERCENTAGE = "percentage"  # 20% off
    FIXED_AMOUNT = "fixed_amount"  # $5 off
    BOGO = "bogo"  # Buy one get one
    FREE_ITEM = "free_item"  # Free appetizer
    COMBO_DEAL = "combo_deal"  # Meal + drink for $15

class CouponStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    DRAFT = "draft"

class TargetAudience(Enum):
    ALL_CUSTOMERS = "all_customers"
    NEW_CUSTOMERS = "new_customers"
    RETURNING_CUSTOMERS = "returning_customers"
    LOYAL_CUSTOMERS = "loyal_customers"

# =================== PYDANTIC MODELS ===================

class CouponCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    coupon_type: CouponType
    
    # Discount values
    discount_percentage: Optional[int] = Field(None, ge=1, le=100)
    discount_amount: Optional[float] = Field(None, ge=0.01)
    free_item: Optional[str] = Field(None, max_length=200)
    combo_price: Optional[float] = Field(None, ge=0.01)
    
    # Validity and limits
    valid_from: str  # ISO date string
    valid_until: str  # ISO date string
    max_redemptions: Optional[int] = Field(None, ge=1)
    max_per_customer: int = Field(default=1, ge=1)
    minimum_purchase: Optional[float] = Field(None, ge=0)
    
    # Targeting
    target_audience: TargetAudience = TargetAudience.ALL_CUSTOMERS
    days_of_week: List[str] = Field(default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
    time_restrictions: Optional[Dict[str, str]] = None  # {"start": "17:00", "end": "19:00"}
    
    # Marketing
    terms_conditions: Optional[str] = Field(None, max_length=1000)
    promotional_message: Optional[str] = Field(None, max_length=200)
    
    @validator('coupon_type')
    def validate_coupon_fields(cls, v, values):
        # Ensure required fields are present based on coupon type
        if v == CouponType.PERCENTAGE and not values.get('discount_percentage'):
            raise ValueError('discount_percentage required for percentage coupons')
        elif v == CouponType.FIXED_AMOUNT and not values.get('discount_amount'):
            raise ValueError('discount_amount required for fixed amount coupons')
        elif v == CouponType.FREE_ITEM and not values.get('free_item'):
            raise ValueError('free_item required for free item coupons')
        elif v == CouponType.COMBO_DEAL and not values.get('combo_price'):
            raise ValueError('combo_price required for combo deal coupons')
        return v

class Coupon(BaseModel):
    id: str
    restaurant_id: str
    owner_id: str
    title: str
    description: str
    coupon_type: CouponType
    
    # Discount details
    discount_percentage: Optional[int] = None
    discount_amount: Optional[float] = None
    free_item: Optional[str] = None
    combo_price: Optional[float] = None
    
    # Validity and limits
    valid_from: str
    valid_until: str
    max_redemptions: Optional[int] = None
    max_per_customer: int = 1
    minimum_purchase: Optional[float] = None
    
    # Usage tracking
    total_redemptions: int = 0
    total_revenue_impact: float = 0.0
    unique_customers: int = 0
    
    # Targeting
    target_audience: TargetAudience
    days_of_week: List[str]
    time_restrictions: Optional[Dict[str, str]] = None
    
    # Marketing
    terms_conditions: Optional[str] = None
    promotional_message: Optional[str] = None
    
    # QR Code
    qr_code: Optional[str] = None  # Base64 encoded QR code image
    redemption_code: str  # Short code for manual entry
    
    # Metadata
    status: CouponStatus = CouponStatus.ACTIVE
    created_at: str
    updated_at: str
    
    # Analytics (calculated fields)
    views: int = 0
    saves: int = 0
    click_rate: float = 0.0
    conversion_rate: float = 0.0

class CouponRedemption(BaseModel):
    id: str
    coupon_id: str
    restaurant_id: str
    customer_id: Optional[str] = None  # Can be None for walk-in customers
    customer_email: Optional[str] = None
    redemption_method: str  # "qr_code", "manual_code", "staff_scan"
    order_total: Optional[float] = None
    discount_applied: float
    redeemed_at: str
    redeemed_by_staff: Optional[str] = None  # Staff member who processed redemption

class CouponAnalytics(BaseModel):
    coupon_id: str
    period_days: int
    
    # Performance metrics
    total_views: int
    total_saves: int
    total_redemptions: int
    unique_customers: int
    
    # Financial impact
    total_discount_given: float
    estimated_revenue_generated: float
    average_order_value: float
    roi_percentage: float
    
    # Engagement metrics
    view_to_save_rate: float
    save_to_redemption_rate: float
    repeat_customer_rate: float
    
    # Time analysis
    peak_redemption_hours: List[Dict[str, Any]]
    popular_days: List[str]

# =================== COUPON SERVICE CLASS ===================

class CouponService:
    """Service for managing digital coupons and redemptions"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.coupons_collection = db.coupons
        self.redemptions_collection = db.coupon_redemptions
        self.restaurants_collection = db.restaurants
        self.owners_collection = db.restaurant_owners
        
    async def create_coupon(self, coupon_data: CouponCreate, owner_id: str, restaurant_id: str) -> Coupon:
        """Create a new digital coupon"""
        
        # Verify owner has access to restaurant
        owner = await self.owners_collection.find_one({"id": owner_id})
        if not owner or restaurant_id not in owner.get("restaurant_ids", []):
            raise HTTPException(status_code=403, detail="No access to this restaurant")
        
        # Generate unique IDs and codes
        coupon_id = str(uuid.uuid4())
        redemption_code = self._generate_redemption_code()
        
        # Generate QR code
        qr_code_image = self._generate_qr_code(coupon_id, redemption_code)
        
        now = datetime.now(timezone.utc).isoformat()
        
        coupon_doc = {
            "id": coupon_id,
            "restaurant_id": restaurant_id,
            "owner_id": owner_id,
            "title": coupon_data.title,
            "description": coupon_data.description,
            "coupon_type": coupon_data.coupon_type.value,
            "discount_percentage": coupon_data.discount_percentage,
            "discount_amount": coupon_data.discount_amount,
            "free_item": coupon_data.free_item,
            "combo_price": coupon_data.combo_price,
            "valid_from": coupon_data.valid_from,
            "valid_until": coupon_data.valid_until,
            "max_redemptions": coupon_data.max_redemptions,
            "max_per_customer": coupon_data.max_per_customer,
            "minimum_purchase": coupon_data.minimum_purchase,
            "total_redemptions": 0,
            "total_revenue_impact": 0.0,
            "unique_customers": 0,
            "target_audience": coupon_data.target_audience.value,
            "days_of_week": coupon_data.days_of_week,
            "time_restrictions": coupon_data.time_restrictions,
            "terms_conditions": coupon_data.terms_conditions,
            "promotional_message": coupon_data.promotional_message,
            "qr_code": qr_code_image,
            "redemption_code": redemption_code,
            "status": CouponStatus.ACTIVE.value,
            "created_at": now,
            "updated_at": now,
            "views": 0,
            "saves": 0,
            "click_rate": 0.0,
            "conversion_rate": 0.0
        }
        
        await self.coupons_collection.insert_one(coupon_doc)
        
        logger.info(f"Created coupon {coupon_id} for restaurant {restaurant_id}")
        return Coupon(**coupon_doc)
    
    def _generate_redemption_code(self) -> str:
        """Generate a short, memorable redemption code"""
        import random
        import string
        
        # Generate a 6-character alphanumeric code
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def _generate_qr_code(self, coupon_id: str, redemption_code: str) -> str:
        """Generate QR code for coupon redemption"""
        
        # Get frontend URL from environment variable
        frontend_url = os.environ.get('FRONTEND_URL', 'https://cheapcoupons.preview.emergentagent.com')
        
        # QR code contains redemption URL and data
        qr_data = {
            "type": "coupon_redemption",
            "coupon_id": coupon_id,
            "code": redemption_code,
            "url": f"{frontend_url}/redeem/{coupon_id}"
        }
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        img_buffer = io.BytesIO()
        qr_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_base64}"
    
    async def get_owner_coupons(self, owner_id: str, restaurant_id: Optional[str] = None) -> List[Coupon]:
        """Get all coupons for an owner"""
        
        query = {"owner_id": owner_id}
        if restaurant_id:
            query["restaurant_id"] = restaurant_id
        
        coupons_cursor = self.coupons_collection.find(query).sort("created_at", -1)
        coupons = await coupons_cursor.to_list(length=None)
        
        return [Coupon(**coupon) for coupon in coupons]
    
    async def get_active_coupons_by_location(self, latitude: float, longitude: float, radius_miles: float = 10) -> List[Dict]:
        """Get active coupons near a location"""
        
        # First get restaurants in the area
        restaurants_in_area = await self.restaurants_collection.find({
            "location": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                    "$maxDistance": radius_miles * 1609.34  # Convert miles to meters
                }
            }
        }).to_list(length=100)
        
        restaurant_ids = [r["id"] for r in restaurants_in_area]
        
        # Get active coupons for these restaurants
        now = datetime.now(timezone.utc).isoformat()
        active_coupons = await self.coupons_collection.find({
            "restaurant_id": {"$in": restaurant_ids},
            "status": CouponStatus.ACTIVE.value,
            "valid_from": {"$lte": now},
            "valid_until": {"$gte": now}
        }).to_list(length=50)
        
        # Combine with restaurant data
        enriched_coupons = []
        restaurant_map = {r["id"]: r for r in restaurants_in_area}
        
        for coupon in active_coupons:
            restaurant = restaurant_map.get(coupon["restaurant_id"])
            if restaurant:
                coupon_with_restaurant = {
                    **coupon,
                    "restaurant": {
                        "name": restaurant["name"],
                        "address": restaurant["address"],
                        "cuisine_type": restaurant.get("cuisine_type", []),
                        "photos": restaurant.get("photos", [])
                    }
                }
                enriched_coupons.append(coupon_with_restaurant)
        
        return enriched_coupons
    
    async def redeem_coupon(self, coupon_id: str, customer_id: Optional[str] = None, 
                           order_total: Optional[float] = None, staff_id: Optional[str] = None) -> Dict[str, Any]:
        """Redeem a coupon and track analytics"""
        
        # Get coupon
        coupon = await self.coupons_collection.find_one({"id": coupon_id})
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        
        # Validate coupon is active and within date range
        now = datetime.now(timezone.utc)
        valid_from = datetime.fromisoformat(coupon["valid_from"].replace('Z', '+00:00'))
        valid_until = datetime.fromisoformat(coupon["valid_until"].replace('Z', '+00:00'))
        
        if coupon["status"] != CouponStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Coupon is not active")
        
        if now < valid_from or now > valid_until:
            raise HTTPException(status_code=400, detail="Coupon is expired or not yet valid")
        
        # Check redemption limits
        if coupon.get("max_redemptions") and coupon["total_redemptions"] >= coupon["max_redemptions"]:
            raise HTTPException(status_code=400, detail="Coupon redemption limit reached")
        
        # Check per-customer limit if customer is identified
        if customer_id and coupon["max_per_customer"] > 1:
            customer_redemptions = await self.redemptions_collection.count_documents({
                "coupon_id": coupon_id,
                "customer_id": customer_id
            })
            if customer_redemptions >= coupon["max_per_customer"]:
                raise HTTPException(status_code=400, detail="Customer redemption limit reached")
        
        # Check minimum purchase
        if coupon.get("minimum_purchase") and order_total and order_total < coupon["minimum_purchase"]:
            raise HTTPException(status_code=400, detail=f"Minimum purchase of ${coupon['minimum_purchase']} required")
        
        # Calculate discount
        discount_applied = self._calculate_discount(coupon, order_total or 0)
        
        # Create redemption record
        redemption_id = str(uuid.uuid4())
        redemption_doc = {
            "id": redemption_id,
            "coupon_id": coupon_id,
            "restaurant_id": coupon["restaurant_id"],
            "customer_id": customer_id,
            "redemption_method": "api",
            "order_total": order_total,
            "discount_applied": discount_applied,
            "redeemed_at": now.isoformat(),
            "redeemed_by_staff": staff_id
        }
        
        await self.redemptions_collection.insert_one(redemption_doc)
        
        # Update coupon analytics
        await self.coupons_collection.update_one(
            {"id": coupon_id},
            {
                "$inc": {
                    "total_redemptions": 1,
                    "total_revenue_impact": order_total or 0,
                    "unique_customers": 1 if customer_id else 0
                },
                "$set": {"updated_at": now.isoformat()}
            }
        )
        
        logger.info(f"Coupon {coupon_id} redeemed for ${discount_applied} discount")
        
        return {
            "redemption_id": redemption_id,
            "discount_applied": discount_applied,
            "coupon_title": coupon["title"],
            "success": True
        }
    
    def _calculate_discount(self, coupon: Dict, order_total: float) -> float:
        """Calculate discount amount based on coupon type"""
        
        coupon_type = coupon["coupon_type"]
        
        if coupon_type == CouponType.PERCENTAGE.value:
            return round(order_total * (coupon["discount_percentage"] / 100), 2)
        elif coupon_type == CouponType.FIXED_AMOUNT.value:
            return min(coupon["discount_amount"], order_total)
        elif coupon_type == CouponType.BOGO.value:
            # For BOGO, assume 50% discount (simplified)
            return round(order_total * 0.5, 2)
        elif coupon_type == CouponType.FREE_ITEM.value:
            # Return estimated value of free item (simplified)
            return 10.0  # Default free item value
        elif coupon_type == CouponType.COMBO_DEAL.value:
            # Discount is difference between normal price and combo price
            return max(0, order_total - coupon["combo_price"])
        
        return 0.0
    
    async def get_coupon_analytics(self, coupon_id: str, days: int = 30) -> CouponAnalytics:
        """Get detailed analytics for a coupon"""
        
        # Get coupon
        coupon = await self.coupons_collection.find_one({"id": coupon_id})
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        
        # Get redemptions in the specified period
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        redemptions = await self.redemptions_collection.find({
            "coupon_id": coupon_id,
            "redeemed_at": {"$gte": cutoff_date.isoformat()}
        }).to_list(length=None)
        
        # Calculate metrics
        total_redemptions = len(redemptions)
        unique_customers = len(set(r.get("customer_id") for r in redemptions if r.get("customer_id")))
        total_discount_given = sum(r.get("discount_applied", 0) for r in redemptions)
        total_revenue = sum(r.get("order_total", 0) for r in redemptions if r.get("order_total"))
        
        # Calculate rates
        views = coupon.get("views", 0)
        saves = coupon.get("saves", 0)
        
        view_to_save_rate = (saves / views * 100) if views > 0 else 0
        save_to_redemption_rate = (total_redemptions / saves * 100) if saves > 0 else 0
        average_order_value = (total_revenue / total_redemptions) if total_redemptions > 0 else 0
        
        # Estimate ROI (simplified)
        estimated_new_revenue = total_revenue * 0.7  # Assume 70% is incremental
        marketing_cost = 0  # No direct marketing cost for digital coupons
        roi_percentage = ((estimated_new_revenue - total_discount_given - marketing_cost) / max(total_discount_given, 1)) * 100
        
        return CouponAnalytics(
            coupon_id=coupon_id,
            period_days=days,
            total_views=views,
            total_saves=saves,
            total_redemptions=total_redemptions,
            unique_customers=unique_customers,
            total_discount_given=total_discount_given,
            estimated_revenue_generated=estimated_new_revenue,
            average_order_value=average_order_value,
            roi_percentage=roi_percentage,
            view_to_save_rate=view_to_save_rate,
            save_to_redemption_rate=save_to_redemption_rate,
            repeat_customer_rate=0.0,  # TODO: Calculate repeat rate
            peak_redemption_hours=[],  # TODO: Calculate peak hours
            popular_days=[]  # TODO: Calculate popular days
        )

# Global service instance
_coupon_service: Optional[CouponService] = None

def get_coupon_service(db: AsyncIOMotorDatabase) -> CouponService:
    """Get or create coupon service instance"""
    global _coupon_service
    if _coupon_service is None:
        _coupon_service = CouponService(db)
    return _coupon_service