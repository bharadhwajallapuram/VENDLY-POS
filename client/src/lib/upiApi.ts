// UPI Payment Types
export interface UPIPaymentRequest {
  amount: number;
  upi_id: string;
  sale_id?: number;
}

export interface UPIPaymentResponse {
  transaction_id: string;
  status: string;
  upi_url?: string;
}

export async function createUPIPaymentRequest(req: UPIPaymentRequest): Promise<UPIPaymentResponse> {
  const res = await fetch("/api/v1/payments/upi-request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("Failed to create UPI payment request");
  return res.json();
}
