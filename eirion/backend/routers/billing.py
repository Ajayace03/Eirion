"""
Sprint 8: Stripe Subscription Billing
POST /billing/create-checkout-session  → returns Stripe Checkout URL
POST /billing/webhook                  → marks User.is_pro on payment success

Requires env: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID
"""
import os
import json
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

router = APIRouter()

PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_placeholder")
SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:5173/dashboard?upgraded=true")
CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "http://localhost:5173/dashboard")


@router.post("/create-checkout-session")
async def create_checkout_session():
    """
    Creates a Stripe Checkout Session for the Eirion Pro subscription ($20/mo).
    Returns the session URL for the frontend to redirect to.
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        # Local dev stub — return a fake URL so frontend can be tested without Stripe
        return JSONResponse({"url": f"{SUCCESS_URL}&stub=1"})

    try:
        import stripe
        stripe.api_key = stripe_key

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": PRICE_ID, "quantity": 1}],
            mode="subscription",
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
        )
        return JSONResponse({"url": session.url})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
):
    """
    Handles Stripe webhook events. On 'checkout.session.completed',
    marks the associated user as is_pro=True in the database (Phase 1+).
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    payload = await request.body()

    if not webhook_secret:
        # Local dev: just acknowledge without verifying
        return JSONResponse({"received": True})

    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        event = stripe.Webhook.construct_event(payload, stripe_signature, webhook_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email")
        print(f"[Stripe] New Pro subscriber: {customer_email}")
        # TODO Phase 1: look up user by email in DB and set is_pro=True

    return JSONResponse({"received": True})
