// This is a mock API handler for payment methods. Replace with your real backend endpoint.
import type { NextApiRequest, NextApiResponse } from 'next';

const paymentMethods = [
  { code: 'cash', label: 'Cash', enabled: true },
  { code: 'card', label: 'Card', enabled: true },
  { code: 'upi', label: 'UPI', enabled: true },
  { code: 'wallet', label: 'Wallet', enabled: true },
];

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json(paymentMethods);
}
