import React, { forwardRef } from "react";

interface ReceiptProps {
  saleId: number;
  items: { name: string; price: number; quantity: number }[];
  total: number;
  date: string;
  cashier?: string;
}

const Receipt = forwardRef<HTMLDivElement, ReceiptProps>(
  ({ saleId, items, total, date, cashier }, ref) => (
    <div ref={ref} className="p-4 w-80 bg-white text-black font-mono border border-gray-300 rounded">
      <h2 className="text-center text-lg font-bold mb-2">Vendly POS Receipt</h2>
      <div className="text-xs mb-2">Sale ID: {saleId}</div>
      <div className="text-xs mb-2">Date: {date}</div>
      {cashier && <div className="text-xs mb-2">Cashier: {cashier}</div>}
      <hr className="my-2" />
      <table className="w-full text-xs mb-2">
        <thead>
          <tr>
            <th className="text-left">Item</th>
            <th className="text-right">Qty</th>
            <th className="text-right">Price</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => (
            <tr key={i}>
              <td>{item.name}</td>
              <td className="text-right">{item.quantity}</td>
              <td className="text-right">${(item.price / 100).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <hr className="my-2" />
      <div className="flex justify-between font-bold">
        <span>Total</span>
        <span>${(total / 100).toFixed(2)}</span>
      </div>
      <div className="text-center text-xs mt-4">Thank you for your purchase!</div>
    </div>
  )
);

export default Receipt;
