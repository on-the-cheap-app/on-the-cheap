# On-the-Cheap Subscription System Implementation Plan

## ✅ Approved Pricing Structure

### Starter Tier - FREE
- 1 restaurant location
- 5 specials per month
- Basic listing features
- Customer reviews & ratings
- Mobile app presence

### Pro Tier - $99/month
- **Monthly**: $99/month
- **Annual**: $948/year ($79/month - save 20%)
- **14-day free trial**
- Unlimited restaurant locations (up to 3)
- Unlimited specials & promotions
- Basic analytics dashboard
- Priority listing
- Digital coupon creation

### Enterprise Tier - $299/month
- **Monthly**: $299/month
- **Annual**: $2,988/year ($249/month - save 20%)
- **14-day free trial**
- Everything in Pro, plus:
- Unlimited locations
- AI-driven upselling
- Dynamic pricing optimization
- POS integration
- Advanced analytics
- Dedicated account manager
- API access

---

## 📋 Implementation Phases

### Phase 1: Payment Processor Setup (YOU DO THIS)

**Step 1: Create Stripe Account**
1. Go to https://stripe.com/
2. Click "Start now" or "Sign up"
3. Enter email and create password
4. Choose account type: "Individual" or "Business"
5. Complete business information:
   - Business name: "On-the-Cheap" or your company name
   - Business address
   - Phone number
   - Tax ID (optional for now)
6. Verify email address
7. **Get API Keys:**
   - Go to https://dashboard.stripe.com/test/apikeys
   - Copy "Publishable key" (starts with pk_test_)
   - Copy "Secret key" (starts with sk_test_)
   - Save these securely

**Step 2: Create Stripe Products & Pricing**
1. In Stripe Dashboard, go to "Products"
2. Click "+ Add product"

**Pro Tier Product:**
- Name: "On-the-Cheap Pro"
- Description: "Professional tier for high-volume restaurants"
- Pricing:
  - Monthly: $99/month, recurring
  - Annual: $948/year, recurring annually
- Add 14-day free trial to both
- Save Price IDs (will look like: price_xxxxx)

**Enterprise Tier Product:**
- Name: "On-the-Cheap Enterprise"
- Description: "Enterprise tier with AI and POS integration"
- Pricing:
  - Monthly: $299/month, recurring
  - Annual: $2,988/year, recurring annually
- Add 14-day free trial to both
- Save Price IDs

**Step 3: Create PayPal Business Account**
1. Go to https://www.paypal.com/
2. Click "Sign Up" → "Business Account"
3. Enter business email
4. Complete business information
5. Verify email and phone
6. **Get API Credentials:**
   - Go to https://developer.paypal.com/
   - Log in with PayPal account
   - Click "Apps & Credentials"
   - Switch to "Live" mode (later, start with Sandbox)
   - Create app: "On-the-Cheap Subscriptions"
   - Copy Client ID and Secret

**Step 4: Create PayPal Subscription Plans**
1. In PayPal Developer Dashboard
2. Go to "Subscriptions" → "Plans"
3. Create plans matching Stripe:
   - Pro Monthly: $99/month with 14-day trial
   - Pro Annual: $948/year with 14-day trial
   - Enterprise Monthly: $299/month with 14-day trial
   - Enterprise Annual: $2,988/year with 14-day trial
4. Save Plan IDs

---

### Phase 2: Database Schema (I IMPLEMENT THIS)

**New MongoDB Collections:**

```javascript
// subscriptions collection
{
  "_id": ObjectId,
  "subscription_id": "sub_xxx", // Stripe/PayPal subscription ID
  "owner_id": "owner_uuid",
  "tier": "free" | "pro" | "enterprise",
  "billing_period": "monthly" | "annual",
  "status": "active" | "trialing" | "past_due" | "canceled" | "incomplete",
  "payment_processor": "stripe" | "paypal",
  "current_period_start": ISODate,
  "current_period_end": ISODate,
  "trial_end": ISODate,
  "cancel_at_period_end": false,
  "canceled_at": null,
  "created_at": ISODate,
  "updated_at": ISODate
}

// payment_transactions collection
{
  "_id": ObjectId,
  "transaction_id": "pi_xxx" | "paypal_txn_xxx",
  "owner_id": "owner_uuid",
  "subscription_id": "sub_xxx",
  "amount": 99.00,
  "currency": "usd",
  "status": "pending" | "succeeded" | "failed",
  "payment_processor": "stripe" | "paypal",
  "metadata": {},
  "created_at": ISODate,
  "updated_at": ISODate
}

// Update restaurant_owners collection
{
  // ... existing fields
  "subscription_tier": "free" | "pro" | "enterprise",
  "subscription_id": "sub_xxx",
  "subscription_status": "active" | "trialing" | "past_due" | "canceled",
  "trial_ends_at": ISODate,
  "billing_period": "monthly" | "annual",
  "features_limit": {
    "max_locations": 1,  // 1 for free, 3 for pro, unlimited for enterprise
    "max_specials_per_month": 5,  // 5 for free, unlimited for pro/enterprise
    "analytics": false,  // false for free, true for pro/enterprise
    "ai_features": false  // false for free/pro, true for enterprise
  }
}
```

---

### Phase 3: Backend Implementation (I IMPLEMENT THIS)

**New Endpoints:**

```python
# Subscription Management
POST   /api/owners/subscriptions/create       # Start new subscription
POST   /api/owners/subscriptions/upgrade      # Upgrade tier
POST   /api/owners/subscriptions/downgrade    # Downgrade tier
POST   /api/owners/subscriptions/cancel       # Cancel subscription
GET    /api/owners/subscriptions/status       # Get current subscription
GET    /api/owners/subscriptions/history      # Payment history

# Stripe Integration
POST   /api/stripe/checkout                   # Create Stripe checkout session
GET    /api/stripe/session/:id/status         # Check session status
POST   /api/webhook/stripe                    # Stripe webhooks

# PayPal Integration
POST   /api/paypal/subscription/create        # Create PayPal subscription
POST   /api/paypal/subscription/:id/cancel    # Cancel PayPal subscription
POST   /api/webhook/paypal                    # PayPal webhooks

# Feature Gating
GET    /api/owners/features/check             # Check feature availability
POST   /api/owners/specials/create            # Check limits before creating
```

---

### Phase 4: Frontend Implementation (I IMPLEMENT THIS)

**New Components:**

1. **SubscriptionPricingCard** - Display pricing tiers
2. **SubscriptionCheckout** - Payment flow (Stripe/PayPal choice)
3. **SubscriptionManagement** - Manage active subscription
4. **BillingHistory** - View past payments
5. **UpgradePrompt** - Show when hitting limits
6. **TrialBanner** - Display trial days remaining

**New Pages:**

1. `/owner/pricing` - View and select plans
2. `/owner/checkout` - Complete subscription payment
3. `/owner/billing` - Manage subscription and view history
4. `/owner/upgrade` - Upgrade flow with feature comparison

---

### Phase 5: Feature Gating Logic (I IMPLEMENT THIS)

**Middleware/Decorators:**

```python
@require_subscription_tier("pro")
async def create_unlimited_special():
    # Only pro/enterprise can access
    pass

@check_feature_limit("specials_count", 5)
async def create_special_with_limit():
    # Check if free tier has reached 5 specials
    pass

def can_access_analytics(owner_id):
    # Check if pro or enterprise
    pass

def can_use_ai_features(owner_id):
    # Check if enterprise
    pass
```

---

### Phase 6: Trial Period Handling (I IMPLEMENT THIS)

**Logic:**

- New paid subscriptions start with 14-day trial
- Trial tracked in database
- Daily cron job checks trial expirations
- Email notifications:
  - Trial started
  - Trial ending in 3 days
  - Trial ended
- Auto-downgrade to free if payment fails after trial

---

### Phase 7: Upgrade/Downgrade Logic (I IMPLEMENT THIS)

**Rules:**

**Immediate Upgrades:**
- Free → Pro: Immediate access, trial starts
- Free → Enterprise: Immediate access, trial starts
- Pro → Enterprise: Immediate access, prorated charge

**End-of-Period Downgrades:**
- Pro → Free: Effective at period end
- Enterprise → Pro: Effective at period end
- Enterprise → Free: Effective at period end

**Proration:**
- Stripe handles automatically
- PayPal may need manual calculation

---

## 🔧 Environment Variables Needed

```bash
# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_xxxx
STRIPE_SECRET_KEY=sk_test_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
STRIPE_PRO_MONTHLY_PRICE_ID=price_xxxx
STRIPE_PRO_ANNUAL_PRICE_ID=price_xxxx
STRIPE_ENTERPRISE_MONTHLY_PRICE_ID=price_xxxx
STRIPE_ENTERPRISE_ANNUAL_PRICE_ID=price_xxxx

# PayPal
PAYPAL_CLIENT_ID=xxxx
PAYPAL_SECRET=xxxx
PAYPAL_MODE=sandbox  # or 'live'
PAYPAL_PRO_MONTHLY_PLAN_ID=P-xxxx
PAYPAL_PRO_ANNUAL_PLAN_ID=P-xxxx
PAYPAL_ENTERPRISE_MONTHLY_PLAN_ID=P-xxxx
PAYPAL_ENTERPRISE_ANNUAL_PLAN_ID=P-xxxx
```

---

## 📊 Testing Strategy

### Test Cases:

1. **Free Tier Tests:**
   - Create restaurant (should work)
   - Create 6th special (should fail)
   - Try to access analytics (should fail)

2. **Trial Tests:**
   - Subscribe to Pro trial
   - Verify 14 days access
   - Test trial expiration handling

3. **Payment Tests:**
   - Successful payment
   - Failed payment
   - Payment method update

4. **Upgrade Tests:**
   - Free → Pro (with trial)
   - Pro → Enterprise (prorated)

5. **Downgrade Tests:**
   - Enterprise → Pro (end of period)
   - Pro → Free (end of period)

6. **Cancellation Tests:**
   - Cancel subscription
   - Verify access until period end

---

## 🚀 Deployment Checklist

- [ ] Stripe products created
- [ ] PayPal plans created
- [ ] Environment variables set
- [ ] Database indexes created
- [ ] Webhook URLs configured
- [ ] Email notifications set up
- [ ] Feature gating tested
- [ ] Payment flow tested
- [ ] Trial period tested
- [ ] Upgrade/downgrade tested
- [ ] Error handling verified

---

## 📈 Success Metrics

- Subscription conversion rate
- Trial-to-paid conversion rate
- Churn rate
- Average revenue per user (ARPU)
- Upgrade rate from free to paid
- Payment failure rate

---

## 🆘 Common Issues & Solutions

**Issue: Payment fails during trial**
- Solution: Send email, retry payment, extend trial 3 days

**Issue: User cancels during trial**
- Solution: Immediate downgrade to free, no charge

**Issue: Upgrade proration confusion**
- Solution: Show clear breakdown before confirming

**Issue: Feature limits not enforcing**
- Solution: Check middleware implementation, database updates

---

## ⏱️ Implementation Timeline

- **Week 1**: Payment processor setup + database schema
- **Week 2**: Backend subscription management + webhooks
- **Week 3**: Frontend checkout + subscription UI
- **Week 4**: Feature gating + testing
- **Week 5**: Trial handling + notifications
- **Week 6**: Final testing + deployment

**Total: 6 weeks to production**

---

## 💰 Revenue Projections

Assuming:
- 1000 restaurants on platform
- 10% convert to Pro ($99/month)
- 2% convert to Enterprise ($299/month)

**Monthly Revenue:**
- Pro: 100 × $99 = $9,900
- Enterprise: 20 × $299 = $5,980
- **Total: $15,880/month = $190,560/year**

With 20% annual discount uptake:
- 30% choose annual = ~$152,000/year upfront
