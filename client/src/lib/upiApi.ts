import { UPIPaymentRequest, UPIPaymentResponse } from "../../shared/types";

export async function createUPIPaymentRequest(req: UPIPaymentRequest): Promise<UPIPaymentResponse> {
  const res = await fetch("/api/v1/payments/upi-request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("Failed to create UPI payment request");
  return res.json();
}
