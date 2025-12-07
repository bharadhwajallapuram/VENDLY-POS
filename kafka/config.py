# ===========================================
# Vendly POS - Kafka Configuration
# Event streaming configuration for real-time POS events
# ===========================================

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class KafkaTopics(str, Enum):
    """Kafka topics for Vendly POS events"""
    SALES_EVENTS = "vendly.sales.events"
    INVENTORY_EVENTS = "vendly.inventory.events"
    USER_EVENTS = "vendly.user.events"
    PAYMENT_EVENTS = "vendly.payment.events"
    NOTIFICATION_EVENTS = "vendly.notification.events"
    ANALYTICS_EVENTS = "vendly.analytics.events"
    AUDIT_LOGS = "vendly.audit.logs"


@dataclass
class KafkaConfig:
    """Kafka configuration settings"""
    
    # Connection settings
    bootstrap_servers: str = field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    )
    
    # Security settings
    security_protocol: str = field(
        default_factory=lambda: os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    )
    sasl_mechanism: Optional[str] = field(
        default_factory=lambda: os.getenv("KAFKA_SASL_MECHANISM")
    )
    sasl_username: Optional[str] = field(
        default_factory=lambda: os.getenv("KAFKA_SASL_USERNAME")
    )
    sasl_password: Optional[str] = field(
        default_factory=lambda: os.getenv("KAFKA_SASL_PASSWORD")
    )
    
    # Consumer settings
    consumer_group_id: str = field(
        default_factory=lambda: os.getenv("KAFKA_CONSUMER_GROUP", "vendly-pos-group")
    )
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    
    # Producer settings
    acks: str = "all"  # Ensure message durability
    retries: int = 3
    batch_size: int = 16384
    linger_ms: int = 10
    compression_type: str = "gzip"
    
    # Topic configuration
    default_partitions: int = 3
    default_replication_factor: int = 1
    
    def get_producer_config(self) -> Dict:
        """Get producer configuration dictionary"""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "acks": self.acks,
            "retries": self.retries,
            "batch.size": self.batch_size,
            "linger.ms": self.linger_ms,
            "compression.type": self.compression_type,
        }
        
        if self.security_protocol != "PLAINTEXT":
            config["security.protocol"] = self.security_protocol
            if self.sasl_mechanism:
                config["sasl.mechanism"] = self.sasl_mechanism
                config["sasl.username"] = self.sasl_username
                config["sasl.password"] = self.sasl_password
        
        return config
    
    def get_consumer_config(self) -> Dict:
        """Get consumer configuration dictionary"""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.consumer_group_id,
            "auto.offset.reset": self.auto_offset_reset,
            "enable.auto.commit": self.enable_auto_commit,
        }
        
        if self.security_protocol != "PLAINTEXT":
            config["security.protocol"] = self.security_protocol
            if self.sasl_mechanism:
                config["sasl.mechanism"] = self.sasl_mechanism
                config["sasl.username"] = self.sasl_username
                config["sasl.password"] = self.sasl_password
        
        return config


@dataclass
class TopicConfig:
    """Configuration for individual Kafka topics"""
    name: str
    partitions: int = 3
    replication_factor: int = 1
    retention_ms: int = 604800000  # 7 days
    cleanup_policy: str = "delete"
    
    def to_dict(self) -> Dict:
        return {
            "num_partitions": self.partitions,
            "replication_factor": self.replication_factor,
            "config": {
                "retention.ms": str(self.retention_ms),
                "cleanup.policy": self.cleanup_policy,
            }
        }


# Topic configurations
TOPIC_CONFIGS: List[TopicConfig] = [
    TopicConfig(
        name=KafkaTopics.SALES_EVENTS.value,
        partitions=6,  # Higher partitions for sales (high throughput)
        retention_ms=2592000000,  # 30 days for sales data
    ),
    TopicConfig(
        name=KafkaTopics.INVENTORY_EVENTS.value,
        partitions=3,
        retention_ms=604800000,  # 7 days
    ),
    TopicConfig(
        name=KafkaTopics.PAYMENT_EVENTS.value,
        partitions=3,
        retention_ms=7776000000,  # 90 days for payment audit
    ),
    TopicConfig(
        name=KafkaTopics.USER_EVENTS.value,
        partitions=2,
        retention_ms=604800000,
    ),
    TopicConfig(
        name=KafkaTopics.NOTIFICATION_EVENTS.value,
        partitions=2,
        retention_ms=86400000,  # 1 day
    ),
    TopicConfig(
        name=KafkaTopics.ANALYTICS_EVENTS.value,
        partitions=4,
        retention_ms=2592000000,  # 30 days
    ),
    TopicConfig(
        name=KafkaTopics.AUDIT_LOGS.value,
        partitions=2,
        retention_ms=31536000000,  # 1 year for audit logs
        cleanup_policy="compact",  # Keep latest state
    ),
]


# Event schemas for different event types
EVENT_SCHEMAS = {
    "sale_created": {
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "event_type": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "sale_id": {"type": "string"},
            "store_id": {"type": "string"},
            "user_id": {"type": "string"},
            "total_amount": {"type": "number"},
            "items": {"type": "array"},
            "payment_method": {"type": "string"},
        },
        "required": ["event_id", "event_type", "timestamp", "sale_id", "total_amount"]
    },
    "inventory_updated": {
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "event_type": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "product_id": {"type": "string"},
            "variant_id": {"type": "string"},
            "previous_quantity": {"type": "integer"},
            "new_quantity": {"type": "integer"},
            "change_reason": {"type": "string"},
        },
        "required": ["event_id", "event_type", "timestamp", "product_id", "new_quantity"]
    },
    "payment_processed": {
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "event_type": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "payment_id": {"type": "string"},
            "sale_id": {"type": "string"},
            "amount": {"type": "number"},
            "payment_method": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["event_id", "event_type", "timestamp", "payment_id", "amount", "status"]
    },
}


# Default configuration instance
kafka_config = KafkaConfig()
