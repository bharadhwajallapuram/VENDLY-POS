"""
Vendly POS - Granular Permissions System
==========================================
Defines granular permissions for cashier, manager, and admin roles.
"""

from enum import Enum
from typing import Set


class Permission(str, Enum):
    """Granular permissions"""

    # Sales & POS
    PROCESS_SALES = "process_sales"  # Core POS functionality
    VOID_SALES = "void_sales"
    REFUND_SALES = "refund_sales"
    PROCESS_PAYMENTS = "process_payments"

    # Products
    VIEW_PRODUCTS = "view_products"
    CREATE_PRODUCTS = "create_products"
    UPDATE_PRODUCTS = "update_products"
    DELETE_PRODUCTS = "delete_products"
    MANAGE_INVENTORY = "manage_inventory"

    # Categories
    MANAGE_CATEGORIES = "manage_categories"

    # Discounts & Coupons
    VIEW_DISCOUNTS = "view_discounts"
    CREATE_DISCOUNTS = "create_discounts"
    UPDATE_DISCOUNTS = "update_discounts"
    DELETE_DISCOUNTS = "delete_discounts"
    APPLY_DISCOUNTS = "apply_discounts"

    # Customers
    VIEW_CUSTOMERS = "view_customers"
    CREATE_CUSTOMERS = "create_customers"
    UPDATE_CUSTOMERS = "update_customers"
    DELETE_CUSTOMERS = "delete_customers"
    MANAGE_LOYALTY = "manage_loyalty"

    # Users & Roles
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    MANAGE_ROLES = "manage_roles"

    # Reports & Analytics
    VIEW_REPORTS = "view_reports"
    VIEW_SALES_REPORTS = "view_sales_reports"
    VIEW_INVENTORY_REPORTS = "view_inventory_reports"
    VIEW_CUSTOMER_REPORTS = "view_customer_reports"
    EXPORT_REPORTS = "export_reports"

    # Settings
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_PAYMENT_METHODS = "manage_payment_methods"

    # Audit & Compliance
    VIEW_AUDIT_LOG = "view_audit_log"


class RolePermissions:
    """Define permissions for each role"""

    CASHIER_PERMISSIONS: Set[Permission] = {
        # Sales & POS
        Permission.PROCESS_SALES,
        Permission.PROCESS_PAYMENTS,
        Permission.REFUND_SALES,
        # Products
        Permission.VIEW_PRODUCTS,
        # Discounts
        Permission.APPLY_DISCOUNTS,
        # Customers
        Permission.VIEW_CUSTOMERS,
        Permission.CREATE_CUSTOMERS,
        Permission.UPDATE_CUSTOMERS,
        # Reports
        Permission.VIEW_SALES_REPORTS,
    }

    MANAGER_PERMISSIONS: Set[Permission] = {
        # All cashier permissions
        *CASHIER_PERMISSIONS,
        # Sales & POS (extended)
        Permission.VOID_SALES,
        # Products
        Permission.CREATE_PRODUCTS,
        Permission.UPDATE_PRODUCTS,
        Permission.MANAGE_INVENTORY,
        # Categories
        Permission.MANAGE_CATEGORIES,
        # Discounts & Coupons
        Permission.VIEW_DISCOUNTS,
        Permission.CREATE_DISCOUNTS,
        Permission.UPDATE_DISCOUNTS,
        # Customers
        Permission.DELETE_CUSTOMERS,
        Permission.MANAGE_LOYALTY,
        # Reports
        Permission.VIEW_INVENTORY_REPORTS,
        Permission.VIEW_CUSTOMER_REPORTS,
        Permission.EXPORT_REPORTS,
        # Settings
        Permission.MANAGE_PAYMENT_METHODS,
        # Audit
        Permission.VIEW_AUDIT_LOG,
    }

    ADMIN_PERMISSIONS: Set[Permission] = {
        # All manager permissions
        *MANAGER_PERMISSIONS,
        # Products (extended)
        Permission.DELETE_PRODUCTS,
        # Discounts & Coupons (extended)
        Permission.DELETE_DISCOUNTS,
        # Users & Roles
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_ROLES,
        # Settings
        Permission.MANAGE_SETTINGS,
        # Reports
        Permission.VIEW_REPORTS,
    }

    @classmethod
    def get_permissions(cls, role: str) -> Set[Permission]:
        """Get permissions for a specific role"""
        role_lower = role.lower()

        if role_lower == "admin":
            return cls.ADMIN_PERMISSIONS
        elif role_lower == "manager":
            return cls.MANAGER_PERMISSIONS
        elif role_lower in ("cashier", "clerk"):
            return cls.CASHIER_PERMISSIONS
        else:
            # Default to minimal permissions for unknown roles
            return set()

    @classmethod
    def has_permission(cls, role: str, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        permissions = cls.get_permissions(role)
        return permission in permissions


# Permission groups for convenience
class PermissionGroups:
    """Group related permissions for easier management"""

    POS_OPERATIONS = {
        Permission.PROCESS_SALES,
        Permission.VOID_SALES,
        Permission.REFUND_SALES,
        Permission.PROCESS_PAYMENTS,
    }

    PRODUCT_MANAGEMENT = {
        Permission.VIEW_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.UPDATE_PRODUCTS,
        Permission.DELETE_PRODUCTS,
        Permission.MANAGE_INVENTORY,
    }

    CUSTOMER_MANAGEMENT = {
        Permission.VIEW_CUSTOMERS,
        Permission.CREATE_CUSTOMERS,
        Permission.UPDATE_CUSTOMERS,
        Permission.DELETE_CUSTOMERS,
        Permission.MANAGE_LOYALTY,
    }

    REPORTING = {
        Permission.VIEW_REPORTS,
        Permission.VIEW_SALES_REPORTS,
        Permission.VIEW_INVENTORY_REPORTS,
        Permission.VIEW_CUSTOMER_REPORTS,
        Permission.EXPORT_REPORTS,
    }

    USER_MANAGEMENT = {
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_ROLES,
    }

    ADMIN_ONLY = {
        Permission.MANAGE_SETTINGS,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_ROLES,
    }
