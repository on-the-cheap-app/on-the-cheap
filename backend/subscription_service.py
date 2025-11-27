"""
Subscription Service for On-the-Cheap
Handles subscription management, feature gating, and Stripe integration
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorCollection
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutStatusResponse
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier:
    """Subscription tier definitions"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus:
    """Subscription status types"""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class FeatureLimits:
    """Feature limits by subscription tier"""
    
    TIERS = {
        SubscriptionTier.FREE: {
            "max_locations": 1,
            "max_specials_per_month": 5,
            "analytics_enabled": False,
            "ai_features_enabled": False,
            "priority_listing": False,
            "digital_coupons": False,
            "api_access": False,
            "dedicated_support": False
        },
        SubscriptionTier.PRO: {
            "max_locations": 3,
            "max_specials_per_month": -1,  # Unlimited
            "analytics_enabled": True,
            "ai_features_enabled": False,
            "priority_listing": True,
            "digital_coupons": True,
            "api_access": False,
            "dedicated_support": False
        },
        SubscriptionTier.ENTERPRISE: {
            "max_locations": -1,  # Unlimited
            "max_specials_per_month": -1,  # Unlimited
            "analytics_enabled": True,
            "ai_features_enabled": True,
            "priority_listing": True,
            "digital_coupons": True,
            "api_access": True,
            "dedicated_support": True
        }
    }
    
    @classmethod
    def get_limits(cls, tier: str) -> Dict:
        """Get feature limits for a subscription tier"""
        return cls.TIERS.get(tier, cls.TIERS[SubscriptionTier.FREE])


class SubscriptionService:
    """Service for managing subscriptions"""
    
    def __init__(
        self,
        db_client,
        stripe_api_key: str,
        webhook_url: str
    ):
        self.db = db_client
        self.subscriptions: AsyncIOMotorCollection = db_client.subscriptions
        self.transactions: AsyncIOMotorCollection = db_client.payment_transactions
        self.owners: AsyncIOMotorCollection = db_client.restaurant_owners
        
        # Initialize Stripe
        self.stripe_checkout = StripeCheckout(
            api_key=stripe_api_key,
            webhook_url=webhook_url
        )
    
    async def get_owner_subscription(self, owner_id: str) -> Optional[Dict]:
        """Get owner's current subscription"""
        subscription = await self.subscriptions.find_one({"owner_id": owner_id})
        return subscription
    
    async def get_owner_tier(self, owner_id: str) -> str:
        """Get owner's subscription tier"""
        owner = await self.owners.find_one({"id": owner_id})
        if not owner:
            return SubscriptionTier.FREE
        
        return owner.get("subscription_tier", SubscriptionTier.FREE)
    
    async def check_feature_access(self, owner_id: str, feature: str) -> bool:
        """Check if owner has access to a feature"""
        tier = await self.get_owner_tier(owner_id)
        limits = FeatureLimits.get_limits(tier)
        
        feature_key = f"{feature}_enabled"
        return limits.get(feature_key, False)
    
    async def check_usage_limit(
        self,
        owner_id: str,
        limit_type: str,
        current_count: int
    ) -> Dict[str, any]:
        """
        Check if owner has reached a usage limit
        
        Args:
            owner_id: Owner's ID
            limit_type: Type of limit (e.g., 'max_specials_per_month', 'max_locations')
            current_count: Current usage count
            
        Returns:
            Dict with 'allowed' (bool) and 'limit' (int) and 'upgrade_required' (bool)
        """
        tier = await self.get_owner_tier(owner_id)
        limits = FeatureLimits.get_limits(tier)
        
        limit_value = limits.get(limit_type, 0)
        
        # -1 means unlimited
        if limit_value == -1:
            return {
                "allowed": True,
                "limit": -1,
                "current": current_count,
                "upgrade_required": False
            }
        
        allowed = current_count < limit_value
        
        return {
            "allowed": allowed,
            "limit": limit_value,
            "current": current_count,
            "upgrade_required": not allowed,
            "recommended_tier": SubscriptionTier.PRO if tier == SubscriptionTier.FREE else SubscriptionTier.ENTERPRISE
        }
    
    async def create_subscription_checkout(
        self,
        owner_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Stripe checkout session for subscription
        
        Args:
            owner_id: Owner's ID
            price_id: Stripe price ID for the subscription
            success_url: URL to redirect after success
            cancel_url: URL to redirect on cancel
            metadata: Additional metadata
            
        Returns:
            Dict with checkout URL and session ID
        """
        if metadata is None:
            metadata = {}
        
        metadata["owner_id"] = owner_id
        metadata["type"] = "subscription"
        
        # Create checkout session (Stripe handles trial automatically based on price configuration)
        from emergentintegrations.payments.stripe.checkout import CheckoutSessionRequest
        
        checkout_request = CheckoutSessionRequest(
            stripe_price_id=price_id,
            quantity=1,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            payment_methods=["card"]
        )
        
        session = await self.stripe_checkout.create_checkout_session(checkout_request)
        
        # Create pending transaction record
        await self.transactions.insert_one({
            "transaction_id": session.session_id,
            "owner_id": owner_id,
            "subscription_id": None,  # Will be updated after webhook
            "amount": 0.0,  # Will be updated from webhook
            "currency": "usd",
            "status": "pending",
            "payment_processor": "stripe",
            "stripe_price_id": price_id,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Created subscription checkout for owner {owner_id}, session {session.session_id}")
        
        return {
            "url": session.url,
            "session_id": session.session_id
        }
    
    async def check_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
        """Check the status of a checkout session"""
        return await self.stripe_checkout.get_checkout_status(session_id)
    
    async def handle_successful_subscription(
        self,
        session_id: str,
        stripe_subscription_id: str,
        tier: str,
        billing_period: str,
        trial_end: Optional[datetime] = None
    ):
        """
        Handle successful subscription creation/update
        
        Args:
            session_id: Stripe checkout session ID
            stripe_subscription_id: Stripe subscription ID
            tier: Subscription tier (pro/enterprise)
            billing_period: monthly or annual
            trial_end: Trial end date if applicable
        """
        # Get transaction
        transaction = await self.transactions.find_one({"transaction_id": session_id})
        if not transaction:
            logger.error(f"Transaction not found for session {session_id}")
            return
        
        owner_id = transaction["owner_id"]
        
        # Update transaction
        await self.transactions.update_one(
            {"transaction_id": session_id},
            {
                "$set": {
                    "subscription_id": stripe_subscription_id,
                    "status": "succeeded",
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Create or update subscription record
        now = datetime.now(timezone.utc)
        subscription_data = {
            "subscription_id": stripe_subscription_id,
            "owner_id": owner_id,
            "tier": tier,
            "billing_period": billing_period,
            "status": SubscriptionStatus.TRIALING if trial_end else SubscriptionStatus.ACTIVE,
            "payment_processor": "stripe",
            "trial_end": trial_end,
            "current_period_start": now,
            "current_period_end": now + timedelta(days=30 if billing_period == "monthly" else 365),
            "cancel_at_period_end": False,
            "canceled_at": None,
            "updated_at": now
        }
        
        existing = await self.subscriptions.find_one({"owner_id": owner_id})
        if existing:
            await self.subscriptions.update_one(
                {"owner_id": owner_id},
                {"$set": subscription_data}
            )
        else:
            subscription_data["created_at"] = now
            await self.subscriptions.insert_one(subscription_data)
        
        # Update owner record
        await self.owners.update_one(
            {"id": owner_id},
            {
                "$set": {
                    "subscription_tier": tier,
                    "subscription_id": stripe_subscription_id,
                    "subscription_status": subscription_data["status"],
                    "trial_ends_at": trial_end,
                    "billing_period": billing_period,
                    "features_limit": FeatureLimits.get_limits(tier),
                    "updated_at": now
                }
            }
        )
        
        logger.info(f"Successfully activated {tier} subscription for owner {owner_id}")
    
    async def cancel_subscription(self, owner_id: str, immediate: bool = False) -> Dict:
        """
        Cancel owner's subscription
        
        Args:
            owner_id: Owner's ID
            immediate: If True, cancel immediately. If False, cancel at period end
            
        Returns:
            Status message
        """
        subscription = await self.subscriptions.find_one({"owner_id": owner_id})
        if not subscription:
            return {"error": "No active subscription found"}
        
        now = datetime.now(timezone.utc)
        
        if immediate:
            # Immediate cancellation - downgrade to free
            await self.subscriptions.update_one(
                {"owner_id": owner_id},
                {
                    "$set": {
                        "status": SubscriptionStatus.CANCELED,
                        "canceled_at": now,
                        "updated_at": now
                    }
                }
            )
            
            await self.owners.update_one(
                {"id": owner_id},
                {
                    "$set": {
                        "subscription_tier": SubscriptionTier.FREE,
                        "subscription_status": SubscriptionStatus.CANCELED,
                        "features_limit": FeatureLimits.get_limits(SubscriptionTier.FREE),
                        "updated_at": now
                    }
                }
            )
            
            return {"message": "Subscription canceled immediately. Downgraded to Free tier."}
        else:
            # Cancel at period end - keep access until then
            await self.subscriptions.update_one(
                {"owner_id": owner_id},
                {
                    "$set": {
                        "cancel_at_period_end": True,
                        "canceled_at": now,
                        "updated_at": now
                    }
                }
            )
            
            period_end = subscription.get("current_period_end")
            return {
                "message": f"Subscription will be canceled at period end ({period_end.strftime('%Y-%m-%d')}). You'll keep access until then."
            }
    
    async def get_subscription_analytics(self, owner_id: str) -> Dict:
        """Get subscription and usage analytics for owner"""
        tier = await self.get_owner_tier(owner_id)
        subscription = await self.get_owner_subscription(owner_id)
        limits = FeatureLimits.get_limits(tier)
        
        # Get current month's special count
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        owner = await self.owners.find_one({"id": owner_id})
        restaurant_ids = owner.get("restaurant_ids", [])
        
        # Count specials this month (you'll need to implement this based on your specials schema)
        # For now, returning 0 as placeholder
        specials_this_month = 0
        
        return {
            "tier": tier,
            "status": subscription.get("status") if subscription else "free",
            "billing_period": subscription.get("billing_period") if subscription else None,
            "trial_ends_at": subscription.get("trial_end") if subscription else None,
            "period_end": subscription.get("current_period_end") if subscription else None,
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False) if subscription else False,
            "limits": limits,
            "usage": {
                "locations": len(restaurant_ids),
                "specials_this_month": specials_this_month
            }
        }
