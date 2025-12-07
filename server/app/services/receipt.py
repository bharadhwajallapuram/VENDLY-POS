"""
Vendly POS - Receipt Generator
Generates printable receipts for sales
"""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from app.core.config_loader import (
    get_store_info,
    get_receipt_settings,
    get_tax_settings,
)


@dataclass
class ReceiptItem:
    name: str
    quantity: int
    unit_price: float
    total: float


@dataclass
class Receipt:
    receipt_number: str
    date: datetime
    items: List[ReceiptItem]
    subtotal: float
    tax_amount: float
    tax_rate: float
    total: float
    payment_method: str
    amount_paid: float
    change: float
    cashier_name: str
    customer_name: Optional[str] = None


def generate_receipt_text(receipt: Receipt, width: int = 40) -> str:
    """
    Generate a text-based receipt for thermal printers (58mm = 32 chars, 80mm = 40-48 chars)
    """
    store = get_store_info()
    settings = get_receipt_settings()
    tax = get_tax_settings()

    lines = []

    def center(text: str) -> str:
        return text.center(width)

    def line(char: str = "-") -> str:
        return char * width

    def item_line(left: str, right: str) -> str:
        space = width - len(left) - len(right)
        return left + " " * max(1, space) + right

    # Header
    lines.append(center(store.get("name", "VENDLY POS")))
    if store.get("address"):
        lines.append(center(store.get("address", "")))
    if store.get("city"):
        city_line = (
            f"{store.get('city', '')}, {store.get('state', '')} {store.get('zip', '')}"
        )
        lines.append(center(city_line))
    if store.get("phone"):
        lines.append(center(f"Tel: {store.get('phone', '')}"))

    lines.append(line("="))

    # Receipt info
    lines.append(f"Receipt #: {receipt.receipt_number}")
    lines.append(f"Date: {receipt.date.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Cashier: {receipt.cashier_name}")
    if receipt.customer_name:
        lines.append(f"Customer: {receipt.customer_name}")

    lines.append(line("-"))

    # Items
    for item in receipt.items:
        # Item name
        lines.append(item.name[:width])
        # Quantity x Price = Total
        qty_price = f"  {item.quantity} x ${item.unit_price:.2f}"
        total = f"${item.total:.2f}"
        lines.append(item_line(qty_price, total))

    lines.append(line("-"))

    # Totals
    lines.append(item_line("Subtotal:", f"${receipt.subtotal:.2f}"))

    if receipt.tax_amount > 0:
        tax_label = f"{tax.get('tax_name', 'Tax')} ({receipt.tax_rate}%):"
        lines.append(item_line(tax_label, f"${receipt.tax_amount:.2f}"))

    lines.append(line("="))
    lines.append(item_line("TOTAL:", f"${receipt.total:.2f}"))
    lines.append(line("="))

    # Payment
    lines.append("")
    lines.append(
        item_line(f"Paid ({receipt.payment_method}):", f"${receipt.amount_paid:.2f}")
    )
    if receipt.change > 0:
        lines.append(item_line("Change:", f"${receipt.change:.2f}"))

    lines.append("")
    lines.append(line("-"))

    # Footer
    lines.append(center(settings.get("header", "Thank you for shopping!")))
    lines.append(center(settings.get("footer", "Please come again!")))

    # Tax number if configured
    if tax.get("tax_number"):
        lines.append("")
        lines.append(center(f"Tax ID: {tax.get('tax_number')}"))

    lines.append("")
    lines.append(center(receipt.date.strftime("%Y-%m-%d %H:%M:%S")))

    return "\n".join(lines)


def generate_receipt_html(receipt: Receipt) -> str:
    """
    Generate an HTML receipt for browser printing or email
    """
    store = get_store_info()
    settings = get_receipt_settings()
    tax = get_tax_settings()
    currency = store.get("currency", "USD")

    items_html = ""
    for item in receipt.items:
        items_html += f"""
        <tr>
            <td>{item.name}</td>
            <td class="center">{item.quantity}</td>
            <td class="right">${item.unit_price:.2f}</td>
            <td class="right">${item.total:.2f}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Receipt #{receipt.receipt_number}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            width: 80mm;
            padding: 10px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 10px;
        }}
        .store-name {{
            font-size: 18px;
            font-weight: bold;
        }}
        .divider {{
            border-top: 1px dashed #000;
            margin: 8px 0;
        }}
        .divider-double {{
            border-top: 2px solid #000;
            margin: 8px 0;
        }}
        .info {{
            margin-bottom: 10px;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 4px 2px;
            text-align: left;
        }}
        .center {{
            text-align: center;
        }}
        .right {{
            text-align: right;
        }}
        .total-row {{
            font-weight: bold;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            margin-top: 15px;
        }}
        @media print {{
            body {{
                width: 80mm;
            }}
            .no-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="store-name">{store.get("name", "VENDLY POS")}</div>
        <div>{store.get("address", "")}</div>
        <div>{store.get("city", "")}, {store.get("state", "")} {store.get("zip", "")}</div>
        <div>Tel: {store.get("phone", "")}</div>
    </div>
    
    <div class="divider-double"></div>
    
    <div class="info">
        <div class="info-row">
            <span>Receipt #:</span>
            <span>{receipt.receipt_number}</span>
        </div>
        <div class="info-row">
            <span>Date:</span>
            <span>{receipt.date.strftime("%Y-%m-%d %H:%M")}</span>
        </div>
        <div class="info-row">
            <span>Cashier:</span>
            <span>{receipt.cashier_name}</span>
        </div>
        {"<div class='info-row'><span>Customer:</span><span>" + receipt.customer_name + "</span></div>" if receipt.customer_name else ""}
    </div>
    
    <div class="divider"></div>
    
    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th class="center">Qty</th>
                <th class="right">Price</th>
                <th class="right">Total</th>
            </tr>
        </thead>
        <tbody>
            {items_html}
        </tbody>
    </table>
    
    <div class="divider"></div>
    
    <div class="info">
        <div class="info-row">
            <span>Subtotal:</span>
            <span>${receipt.subtotal:.2f}</span>
        </div>
        {"<div class='info-row'><span>" + tax.get('tax_name', 'Tax') + " (" + str(receipt.tax_rate) + "%):</span><span>$" + f'{receipt.tax_amount:.2f}' + "</span></div>" if receipt.tax_amount > 0 else ""}
    </div>
    
    <div class="divider-double"></div>
    
    <div class="info total-row">
        <div class="info-row">
            <span>TOTAL:</span>
            <span>${receipt.total:.2f}</span>
        </div>
    </div>
    
    <div class="divider-double"></div>
    
    <div class="info">
        <div class="info-row">
            <span>Paid ({receipt.payment_method}):</span>
            <span>${receipt.amount_paid:.2f}</span>
        </div>
        {"<div class='info-row'><span>Change:</span><span>$" + f'{receipt.change:.2f}' + "</span></div>" if receipt.change > 0 else ""}
    </div>
    
    <div class="footer">
        <div class="divider"></div>
        <p>{settings.get("header", "Thank you for shopping!")}</p>
        <p>{settings.get("footer", "Please come again!")}</p>
        {"<p style='margin-top:10px'>Tax ID: " + tax.get('tax_number') + "</p>" if tax.get('tax_number') else ""}
        <p style="margin-top: 10px; font-size: 10px;">{receipt.date.strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="no-print" style="margin-top: 20px; text-align: center;">
        <button onclick="window.print()" style="padding: 10px 20px; font-size: 14px; cursor: pointer;">
            🖨️ Print Receipt
        </button>
    </div>
</body>
</html>
    """

    return html
