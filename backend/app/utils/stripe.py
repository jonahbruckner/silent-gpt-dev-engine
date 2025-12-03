import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Preise pro Pack aus ENV oder Default (899 = 8,99 €)
PACK_PRICE_EUR_CENTS = int(os.getenv("PACK_PRICE_EUR_CENTS", "899"))

def create_checkout_session(pack_slug: str):
    """
    Erzeugt eine Stripe Checkout Session für ein Pack.
    Der Preis ist üblicherweise fest (1 Preis pro Pack).
    """
    base_url = os.getenv("PUBLIC_SITE_URL", "").rstrip("/")
    success_url = f"{base_url}/thank-you?pack={pack_slug}"
    cancel_url = f"{base_url}/products/{pack_slug}"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"SilentGPT Pack: {pack_slug}",
                    },
                    "unit_amount": PACK_PRICE_EUR_CENTS,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return session
