"""
Restaurant Owner Management Service

This service handles:
- Owner registration and authentication
- Restaurant claiming workflow
- Special scheduling and management
- Owner dashboard functionality
- Approval workflow for owner-submitted content
"""

import logging
from datetime import datetime, timezone, time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
import hashlib
import jwt
from fastapi import HTTPException
from enum import Enum

logger = logging.getLogger(__name__)

class OwnerStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    REJECTED = "rejected"

class RestaurantClaimStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

class SpecialApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"

# =================== PYDANTIC MODELS ===================

class RestaurantOwnerCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=10, max_length=20)
    business_name: Optional[str] = Field(None, max_length=100)
    business_type: str = Field(default="restaurant")  # restaurant, bar, cafe, food_truck, etc.

class RestaurantOwner(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    business_name: Optional[str] = None
    business_type: str
    status: OwnerStatus
    restaurant_ids: List[str] = Field(default_factory=list)
    verification_documents: List[str] = Field(default_factory=list)
    is_verified: bool = False
    created_at: str
    updated_at: str

class RestaurantClaimRequest(BaseModel):
    id: Optional[str] = None
    restaurant_id: str
    owner_id: str
    business_license: Optional[str] = None
    proof_of_ownership: Optional[str] = None
    additional_documents: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    status: RestaurantClaimStatus = RestaurantClaimStatus.PENDING
    submitted_at: str
    reviewed_at: Optional[str] = None
    reviewer_notes: Optional[str] = None

class OwnerSpecialCreate(BaseModel):
    restaurant_id: str
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    special_type: str  # happy_hour, daily_special, discount, bogo, etc.
    price: Optional[float] = Field(None, ge=0)
    original_price: Optional[float] = Field(None, ge=0)
    discount_percentage: Optional[int] = Field(None, ge=0, le=100)
    days_available: List[str] = Field(..., min_items=1)  # ['monday', 'tuesday', etc.]
    time_start: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM format
    time_end: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")    # HH:MM format
    valid_from: str  # ISO date string
    valid_until: str  # ISO date string
    max_redemptions: Optional[int] = Field(None, ge=1)
    terms_conditions: Optional[str] = Field(None, max_length=1000)
    image: Optional[str] = Field(None, description="Base64 encoded image data")

class OwnerSpecial(BaseModel):
    id: str
    restaurant_id: str
    owner_id: str
    title: str
    description: str
    special_type: str
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[int] = None
    days_available: List[str]
    time_start: str
    time_end: str
    valid_from: str
    valid_until: str
    max_redemptions: Optional[int] = None
    current_redemptions: int = 0
    terms_conditions: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded image
    approval_status: SpecialApprovalStatus = SpecialApprovalStatus.PENDING
    is_active: bool = False
    admin_notes: Optional[str] = None
    created_at: str
    updated_at: str

class OwnerLoginRequest(BaseModel):
    email: EmailStr
    password: str

class OwnerDashboardStats(BaseModel):
    total_restaurants: int
    pending_claims: int
    active_specials: int
    pending_specials: int
    total_views: int
    total_favorites: int

# =================== OWNER SERVICE CLASS ===================

class RestaurantOwnerService:
    """Service for managing restaurant owners and their operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.owners_collection = db.restaurant_owners
        self.claims_collection = db.restaurant_claims
        self.specials_collection = db.owner_specials
        self.restaurants_collection = db.restaurants
        
    async def create_owner(self, owner_data: RestaurantOwnerCreate) -> RestaurantOwner:
        """Create a new restaurant owner account"""
        
        # Check if email already exists
        existing_owner = await self.owners_collection.find_one({"email": owner_data.email})
        if existing_owner:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = hashlib.sha256(owner_data.password.encode()).hexdigest()
        
        # Create owner document
        owner_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        owner_doc = {
            "id": owner_id,
            "first_name": owner_data.first_name,
            "last_name": owner_data.last_name,
            "email": owner_data.email,
            "password_hash": password_hash,
            "phone": owner_data.phone,
            "business_name": owner_data.business_name,
            "business_type": owner_data.business_type,
            "status": OwnerStatus.PENDING.value,
            "restaurant_ids": [],
            "verification_documents": [],
            "is_verified": False,
            "created_at": now,
            "updated_at": now
        }
        
        await self.owners_collection.insert_one(owner_doc)
        
        # Remove password_hash from response
        del owner_doc["password_hash"]
        
        logger.info(f"Created new restaurant owner: {owner_data.email}")
        return RestaurantOwner(**owner_doc)
    
    async def authenticate_owner(self, login_data: OwnerLoginRequest) -> Dict[str, Any]:
        """Authenticate restaurant owner and return token"""
        
        # Find owner by email
        owner_doc = await self.owners_collection.find_one({"email": login_data.email})
        if not owner_doc:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
        if owner_doc["password_hash"] != password_hash:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if account is suspended
        if owner_doc["status"] == OwnerStatus.SUSPENDED.value:
            raise HTTPException(status_code=403, detail="Account suspended")
        
        # Generate JWT token
        payload = {
            "user_id": owner_doc["id"],
            "email": owner_doc["email"],
            "user_type": "owner",
            "exp": datetime.now(timezone.utc).timestamp() + 86400  # 24 hours
        }
        
        # Use the same JWT secret as the main server
        import os
        JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        # Remove password_hash from response
        del owner_doc["password_hash"]
        
        logger.info(f"Owner authenticated: {login_data.email}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "owner",
            "owner": RestaurantOwner(**owner_doc)
        }
    
    async def claim_restaurant(self, claim_data: RestaurantClaimRequest) -> RestaurantClaimRequest:
        """Submit a restaurant claim request"""
        
        # Verify restaurant exists
        restaurant = await self.restaurants_collection.find_one({"id": claim_data.restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Check if restaurant is already claimed
        existing_claim = await self.claims_collection.find_one({
            "restaurant_id": claim_data.restaurant_id,
            "status": {"$in": [RestaurantClaimStatus.APPROVED.value, RestaurantClaimStatus.PENDING.value]}
        })
        if existing_claim:
            raise HTTPException(status_code=400, detail="Restaurant already claimed or claim pending")
        
        # Create claim document
        claim_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        claim_doc = {
            "id": claim_id,
            "restaurant_id": claim_data.restaurant_id,
            "owner_id": claim_data.owner_id,
            "business_license": claim_data.business_license,
            "proof_of_ownership": claim_data.proof_of_ownership,
            "additional_documents": claim_data.additional_documents,
            "notes": claim_data.notes,
            "status": RestaurantClaimStatus.PENDING.value,
            "submitted_at": now,
            "reviewed_at": None,
            "reviewer_notes": None
        }
        
        await self.claims_collection.insert_one(claim_doc)
        
        logger.info(f"Restaurant claim submitted: {claim_data.restaurant_id} by owner {claim_data.owner_id}")
        return RestaurantClaimRequest(**claim_doc)
    
    async def create_special(self, special_data: OwnerSpecialCreate, owner_id: str) -> OwnerSpecial:
        """Create a new special (pending approval)"""
        
        # Verify owner has access to restaurant
        owner = await self.owners_collection.find_one({"id": owner_id})
        if not owner or special_data.restaurant_id not in owner.get("restaurant_ids", []):
            raise HTTPException(status_code=403, detail="No access to this restaurant")
        
        # Create special document
        special_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        special_doc = {
            "id": special_id,
            "restaurant_id": special_data.restaurant_id,
            "owner_id": owner_id,
            "title": special_data.title,
            "description": special_data.description,
            "special_type": special_data.special_type,
            "price": special_data.price,
            "original_price": special_data.original_price,
            "discount_percentage": special_data.discount_percentage,
            "days_available": special_data.days_available,
            "time_start": special_data.time_start,
            "time_end": special_data.time_end,
            "valid_from": special_data.valid_from,
            "valid_until": special_data.valid_until,
            "max_redemptions": special_data.max_redemptions,
            "current_redemptions": 0,
            "terms_conditions": special_data.terms_conditions,
            "approval_status": SpecialApprovalStatus.APPROVED.value,  # Auto-approve
            "is_active": True,  # Auto-activate
            "admin_notes": None,
            "created_at": now,
            "updated_at": now
        }
        
        await self.specials_collection.insert_one(special_doc)
        
        logger.info(f"Special created by owner {owner_id} for restaurant {special_data.restaurant_id}")
        return OwnerSpecial(**special_doc)
    
    async def get_owner_dashboard(self, owner_id: str) -> OwnerDashboardStats:
        """Get dashboard statistics for owner"""
        
        owner = await self.owners_collection.find_one({"id": owner_id})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        restaurant_ids = owner.get("restaurant_ids", [])
        
        # Count pending claims
        pending_claims = await self.claims_collection.count_documents({
            "owner_id": owner_id,
            "status": RestaurantClaimStatus.PENDING.value
        })
        
        # Count active specials
        active_specials = await self.specials_collection.count_documents({
            "owner_id": owner_id,
            "approval_status": SpecialApprovalStatus.APPROVED.value,
            "is_active": True
        })
        
        # Count pending specials
        pending_specials = await self.specials_collection.count_documents({
            "owner_id": owner_id,
            "approval_status": SpecialApprovalStatus.PENDING.value
        })
        
        # TODO: Add view and favorite counts from analytics
        
        return OwnerDashboardStats(
            total_restaurants=len(restaurant_ids),
            pending_claims=pending_claims,
            active_specials=active_specials,
            pending_specials=pending_specials,
            total_views=0,  # TODO: Implement analytics
            total_favorites=0  # TODO: Implement analytics
        )
    
    async def get_owner_specials(self, owner_id: str, restaurant_id: Optional[str] = None) -> List[OwnerSpecial]:
        """Get all specials for an owner"""
        
        query = {"owner_id": owner_id}
        if restaurant_id:
            query["restaurant_id"] = restaurant_id
        
        specials_cursor = self.specials_collection.find(query).sort("created_at", -1)
        specials = await specials_cursor.to_list(length=None)
        
        return [OwnerSpecial(**special) for special in specials]
    
    async def update_special(self, special_id: str, owner_id: str, special_data: dict) -> OwnerSpecial:
        """Update an existing special"""
        
        # Verify the special exists and belongs to this owner
        existing_special = await self.specials_collection.find_one({
            "id": special_id,
            "owner_id": owner_id
        })
        
        if not existing_special:
            raise HTTPException(status_code=404, detail="Special not found or you don't have permission to edit it")
        
        # Update the special
        update_data = {
            "title": special_data.get("title", existing_special.get("title")),
            "description": special_data.get("description", existing_special.get("description")),
            "special_type": special_data.get("special_type", existing_special.get("special_type")),
            "price": special_data.get("price"),
            "original_price": special_data.get("original_price"),
            "discount_percentage": special_data.get("discount_percentage"),
            "days_available": special_data.get("days_available", existing_special.get("days_available")),
            "time_start": special_data.get("time_start", existing_special.get("time_start")),
            "time_end": special_data.get("time_end", existing_special.get("time_end")),
            "valid_from": special_data.get("valid_from", existing_special.get("valid_from")),
            "valid_until": special_data.get("valid_until", existing_special.get("valid_until")),
            "max_redemptions": special_data.get("max_redemptions"),
            "terms_conditions": special_data.get("terms_conditions"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            # Auto-approve edits (no manual approval needed)
            "approval_status": SpecialApprovalStatus.APPROVED.value,
            "is_active": True
        }
        
        await self.specials_collection.update_one(
            {"id": special_id},
            {"$set": update_data}
        )
        
        # Get and return the updated special
        updated_special = await self.specials_collection.find_one({"id": special_id})
        logger.info(f"Special updated: {special_id} by owner: {owner_id}")
        
        return OwnerSpecial(**updated_special)
    
    async def delete_special(self, special_id: str, owner_id: str) -> bool:
        """Delete a special"""
        
        # Verify the special exists and belongs to this owner
        existing_special = await self.specials_collection.find_one({
            "id": special_id,
            "owner_id": owner_id
        })
        
        if not existing_special:
            raise HTTPException(status_code=404, detail="Special not found or you don't have permission to delete it")
        
        # Delete the special
        result = await self.specials_collection.delete_one({"id": special_id})
        
        if result.deleted_count > 0:
            logger.info(f"Special deleted: {special_id} by owner: {owner_id}")
            return True
        
        return False
    
    async def get_owner_restaurants(self, owner_id: str) -> List[Dict]:
        """Get all restaurants owned by this owner"""
        
        owner = await self.owners_collection.find_one({"id": owner_id})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        owner_email = owner.get("email")
        restaurant_ids = owner.get("restaurant_ids", [])
        
        # Build query to find restaurants by ID or by owner_email
        query_conditions = []
        if restaurant_ids:
            query_conditions.append({"id": {"$in": restaurant_ids}})
        if owner_email:
            query_conditions.append({"owner_email": owner_email})
        
        if not query_conditions:
            return []
        
        restaurants_cursor = self.restaurants_collection.find(
            {"$or": query_conditions} if len(query_conditions) > 1 else query_conditions[0],
            {"_id": 0}  # Exclude MongoDB ObjectId
        )
        restaurants = await restaurants_cursor.to_list(length=None)
        
        return restaurants

    async def link_restaurant_to_owner(self, owner_id: str, restaurant_id: str) -> bool:
        """Link a restaurant to an owner by adding to their restaurant_ids"""
        
        # Update owner's restaurant_ids
        result = await self.owners_collection.update_one(
            {"id": owner_id},
            {"$addToSet": {"restaurant_ids": restaurant_id}}
        )
        
        # Also set owner_email on the restaurant
        owner = await self.owners_collection.find_one({"id": owner_id}, {"_id": 0, "email": 1})
        if owner:
            await self.restaurants_collection.update_one(
                {"id": restaurant_id},
                {"$set": {"owner_email": owner.get("email"), "owner_id": owner_id}}
            )
        
        return result.modified_count > 0 or result.matched_count > 0

# =================== ADMIN FUNCTIONS ===================

class OwnerAdminService:
    """Admin functions for managing owner operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.owners_collection = db.restaurant_owners
        self.claims_collection = db.restaurant_claims
        self.specials_collection = db.owner_specials
        self.restaurants_collection = db.restaurants
    
    async def approve_claim(self, claim_id: str, admin_notes: Optional[str] = None) -> bool:
        """Approve a restaurant claim"""
        
        claim = await self.claims_collection.find_one({"id": claim_id})
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Update claim status
        await self.claims_collection.update_one(
            {"id": claim_id},
            {
                "$set": {
                    "status": RestaurantClaimStatus.APPROVED.value,
                    "reviewed_at": datetime.now(timezone.utc).isoformat(),
                    "reviewer_notes": admin_notes
                }
            }
        )
        
        # Add restaurant to owner's restaurant list
        await self.owners_collection.update_one(
            {"id": claim["owner_id"]},
            {"$addToSet": {"restaurant_ids": claim["restaurant_id"]}}
        )
        
        # Update restaurant to mark as claimed
        await self.restaurants_collection.update_one(
            {"id": claim["restaurant_id"]},
            {
                "$set": {
                    "is_claimed": True,
                    "owner_id": claim["owner_id"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"Claim approved: {claim_id}")
        return True
    
    async def approve_special(self, special_id: str, admin_notes: Optional[str] = None) -> bool:
        """Approve a special"""
        
        await self.specials_collection.update_one(
            {"id": special_id},
            {
                "$set": {
                    "approval_status": SpecialApprovalStatus.APPROVED.value,
                    "is_active": True,
                    "admin_notes": admin_notes,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"Special approved: {special_id}")
        return True
    
    async def get_pending_claims(self) -> List[RestaurantClaimRequest]:
        """Get all pending restaurant claims"""
        
        claims_cursor = self.claims_collection.find(
            {"status": RestaurantClaimStatus.PENDING.value}
        ).sort("submitted_at", 1)
        
        claims = await claims_cursor.to_list(length=None)
        
        # Clean MongoDB data for Pydantic models
        cleaned_claims = []
        for claim in claims:
            # Remove MongoDB _id and prepare data
            if '_id' in claim:
                del claim['_id']
            
            # Handle different field names that might exist in database
            # Ensure required fields exist with default values if missing
            if 'restaurant_id' not in claim:
                claim['restaurant_id'] = claim.get('google_place_id', 'unknown')
            if 'submitted_at' not in claim:
                claim['submitted_at'] = claim.get('created_at', datetime.now(timezone.utc).isoformat())
            if 'owner_id' not in claim:
                claim['owner_id'] = claim.get('user_id', 'unknown')
            
            try:
                cleaned_claims.append(RestaurantClaimRequest(**claim))
            except Exception as e:
                # Skip invalid claims and log the error
                logger.warning(f"Skipping invalid claim: {e}")
                continue
        
        return cleaned_claims
    
    async def get_pending_specials(self) -> List[OwnerSpecial]:
        """Get all pending specials"""
        
        specials_cursor = self.specials_collection.find(
            {"approval_status": SpecialApprovalStatus.PENDING.value}
        ).sort("created_at", 1)
        
        specials = await specials_cursor.to_list(length=None)
        
        # Clean MongoDB data for Pydantic models
        cleaned_specials = []
        for special in specials:
            # Remove MongoDB _id and prepare data
            if '_id' in special:
                del special['_id']
            cleaned_specials.append(OwnerSpecial(**special))
        
        return cleaned_specials

# Global service instances
_owner_service: Optional[RestaurantOwnerService] = None
_owner_admin_service: Optional[OwnerAdminService] = None

def get_owner_service(db: AsyncIOMotorDatabase) -> RestaurantOwnerService:
    """Get or create owner service instance"""
    global _owner_service
    if _owner_service is None:
        _owner_service = RestaurantOwnerService(db)
    return _owner_service

def get_owner_admin_service(db: AsyncIOMotorDatabase) -> OwnerAdminService:
    """Get or create owner admin service instance"""  
    global _owner_admin_service
    if _owner_admin_service is None:
        _owner_admin_service = OwnerAdminService(db)
    return _owner_admin_service