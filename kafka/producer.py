# ===========================================
# Vendly POS - Kafka Producer
# Async producer for sending events to Kafka
# ===========================================

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from .config import kafka_config, KafkaTopics


@dataclass
class BaseEvent:
    """Base class for all Kafka events"""
    event_id: str
    event_type: str
    timestamp: str
    source: str = "vendly-pos"
    version: str = "1.0"
    
    @classmethod
    def create(cls, event_type: str, **kwargs):
        """Factory method to create an event"""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class SaleCreatedEvent(BaseEvent):
    """Event emitted when a sale is created"""
    sale_id: str = ""
    store_id: str = ""
    user_id: str = ""
    total_amount: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    items: list = None
    payment_method: str = ""
    customer_id: Optional[str] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []


@dataclass
class InventoryUpdatedEvent(BaseEvent):
    """Event emitted when inventory is updated"""
    product_id: str = ""
    variant_id: str = ""
    previous_quantity: int = 0
    new_quantity: int = 0
    change_reason: str = ""
    location_id: Optional[str] = None


@dataclass
class PaymentProcessedEvent(BaseEvent):
    """Event emitted when a payment is processed"""
    payment_id: str = ""
    sale_id: str = ""
    amount: float = 0.0
    payment_method: str = ""
    status: str = ""  # success, failed, pending, refunded
    transaction_reference: Optional[str] = None
    error_message: Optional[str] = None


class KafkaProducer:
    """Async Kafka producer for Vendly events"""
    
    def __init__(self, config=None):
        self.config = config or kafka_config
        self._producer = None
    
    async def start(self):
        """Initialize the Kafka producer"""
        try:
            from aiokafka import AIOKafkaProducer
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            await self._producer.start()
        except ImportError:
            # Fallback for when aiokafka is not installed
            print("Warning: aiokafka not installed. Kafka producer disabled.")
            self._producer = None
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self._producer:
            await self._producer.stop()
    
    async def send_event(
        self,
        topic: KafkaTopics,
        event: BaseEvent,
        key: Optional[str] = None
    ) -> bool:
        """Send an event to Kafka"""
        if not self._producer:
            # Log the event instead if Kafka is not available
            print(f"[KAFKA-DISABLED] Topic: {topic.value}, Event: {event.to_json()}")
            return False
        
        try:
            await self._producer.send_and_wait(
                topic=topic.value,
                value=event.to_dict(),
                key=key or event.event_id
            )
            return True
        except Exception as e:
            print(f"Error sending event to Kafka: {e}")
            return False
    
    async def send_sale_event(self, sale_data: Dict[str, Any]) -> bool:
        """Send a sale created event"""
        event = SaleCreatedEvent.create(
            event_type="sale_created",
            sale_id=sale_data.get("sale_id", ""),
            store_id=sale_data.get("store_id", ""),
            user_id=sale_data.get("user_id", ""),
            total_amount=sale_data.get("total_amount", 0.0),
            tax_amount=sale_data.get("tax_amount", 0.0),
            discount_amount=sale_data.get("discount_amount", 0.0),
            items=sale_data.get("items", []),
            payment_method=sale_data.get("payment_method", ""),
            customer_id=sale_data.get("customer_id"),
        )
        return await self.send_event(KafkaTopics.SALES_EVENTS, event, key=event.sale_id)
    
    async def send_inventory_event(
        self,
        product_id: str,
        variant_id: str,
        previous_qty: int,
        new_qty: int,
        reason: str
    ) -> bool:
        """Send an inventory updated event"""
        event = InventoryUpdatedEvent.create(
            event_type="inventory_updated",
            product_id=product_id,
            variant_id=variant_id,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            change_reason=reason,
        )
        return await self.send_event(
            KafkaTopics.INVENTORY_EVENTS, 
            event, 
            key=f"{product_id}:{variant_id}"
        )
    
    async def send_payment_event(self, payment_data: Dict[str, Any]) -> bool:
        """Send a payment processed event"""
        event = PaymentProcessedEvent.create(
            event_type="payment_processed",
            payment_id=payment_data.get("payment_id", ""),
            sale_id=payment_data.get("sale_id", ""),
            amount=payment_data.get("amount", 0.0),
            payment_method=payment_data.get("payment_method", ""),
            status=payment_data.get("status", ""),
            transaction_reference=payment_data.get("transaction_reference"),
            error_message=payment_data.get("error_message"),
        )
        return await self.send_event(
            KafkaTopics.PAYMENT_EVENTS, 
            event, 
            key=event.payment_id
        )


# Singleton producer instance
producer = KafkaProducer()
