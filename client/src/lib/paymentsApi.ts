// Stripe Payment Types
export interface StripePaymentIntentRequest {
  amount: number;
  currency?: string;
  sale_id?: number;
}

export interface StripePaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string;
}

export async function createStripePaymentIntent(req: StripePaymentIntentRequest): Promise<StripePaymentIntentResponse> {
  const res = await fetch("/api/v1/payments/stripe-intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("Failed to create payment intent");
  return res.json();
}
