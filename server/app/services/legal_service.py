# ===========================================
# Legal Service - Privacy Policy & Terms Management
# ===========================================

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db import models as m


class LegalService:
    """Service for managing legal documents (privacy policy, terms of service, etc.)"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Document Management ====================

    def create_document(
        self,
        doc_type: str,
        title: str,
        content: str,
        created_by_user_id: int,
        content_html: Optional[str] = None,
        requires_acceptance: bool = True,
        display_order: int = 0,
    ) -> m.LegalDocument:
        """Create a new legal document (creates new version)"""
        # Get next version number
        last_version = (
            self.db.query(m.LegalDocument)
            .filter(m.LegalDocument.doc_type == doc_type)
            .order_by(m.LegalDocument.version.desc())
            .first()
        )
        next_version = (last_version.version + 1) if last_version else 1

        # Deactivate old version
        if last_version:
            last_version.is_active = False
            self.db.commit()

        # Create new document
        doc = m.LegalDocument(
            doc_type=doc_type,
            version=next_version,
            title=title,
            content=content,
            content_html=content_html,
            is_active=True,
            requires_acceptance=requires_acceptance,
            display_order=display_order,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_active_document(self, doc_type: str) -> Optional[m.LegalDocument]:
        """Get the current active version of a document"""
        return (
            self.db.query(m.LegalDocument)
            .filter(
                m.LegalDocument.doc_type == doc_type,
                m.LegalDocument.is_active == True,
            )
            .first()
        )

    def get_document_by_version(
        self, doc_type: str, version: int
    ) -> Optional[m.LegalDocument]:
        """Get a specific version of a document"""
        return (
            self.db.query(m.LegalDocument)
            .filter(
                m.LegalDocument.doc_type == doc_type,
                m.LegalDocument.version == version,
            )
            .first()
        )

    def get_document_versions(self, doc_type: str) -> List[m.LegalDocument]:
        """Get all versions of a document"""
        return (
            self.db.query(m.LegalDocument)
            .filter(m.LegalDocument.doc_type == doc_type)
            .order_by(m.LegalDocument.version.desc())
            .all()
        )

    def get_all_active_documents(self) -> List[m.LegalDocument]:
        """Get all active legal documents"""
        return (
            self.db.query(m.LegalDocument)
            .filter(m.LegalDocument.is_active == True)
            .order_by(m.LegalDocument.display_order)
            .all()
        )

    def update_document(
        self,
        doc_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        content_html: Optional[str] = None,
        display_order: Optional[int] = None,
    ) -> Optional[m.LegalDocument]:
        """Update an active document (or create new version if needed)"""
        doc = (
            self.db.query(m.LegalDocument).filter(m.LegalDocument.id == doc_id).first()
        )
        if not doc:
            return None

        if title is not None:
            doc.title = title
        if content is not None:
            doc.content = content
        if content_html is not None:
            doc.content_html = content_html
        if display_order is not None:
            doc.display_order = display_order

        doc.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(doc)
        return doc

    # ==================== Acceptance Tracking ====================

    def record_acceptance(
        self,
        legal_document_id: int,
        user_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> m.LegalDocumentAcceptance:
        """Record acceptance of a legal document"""
        if not user_id and not customer_id:
            raise ValueError("Either user_id or customer_id must be provided")

        acceptance = m.LegalDocumentAcceptance(
            legal_document_id=legal_document_id,
            user_id=user_id,
            customer_id=customer_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(acceptance)
        self.db.commit()
        self.db.refresh(acceptance)
        return acceptance

    def has_accepted(
        self,
        legal_document_id: int,
        user_id: Optional[int] = None,
        customer_id: Optional[int] = None,
    ) -> bool:
        """Check if a user/customer has accepted a document"""
        query = self.db.query(m.LegalDocumentAcceptance).filter(
            m.LegalDocumentAcceptance.legal_document_id == legal_document_id
        )

        if user_id:
            query = query.filter(m.LegalDocumentAcceptance.user_id == user_id)
        elif customer_id:
            query = query.filter(m.LegalDocumentAcceptance.customer_id == customer_id)
        else:
            return False

        return query.first() is not None

    def get_user_acceptances(self, user_id: int) -> List[m.LegalDocumentAcceptance]:
        """Get all document acceptances by a user"""
        return (
            self.db.query(m.LegalDocumentAcceptance)
            .filter(m.LegalDocumentAcceptance.user_id == user_id)
            .order_by(m.LegalDocumentAcceptance.accepted_at.desc())
            .all()
        )

    def get_customer_acceptances(
        self, customer_id: int
    ) -> List[m.LegalDocumentAcceptance]:
        """Get all document acceptances by a customer"""
        return (
            self.db.query(m.LegalDocumentAcceptance)
            .filter(m.LegalDocumentAcceptance.customer_id == customer_id)
            .order_by(m.LegalDocumentAcceptance.accepted_at.desc())
            .all()
        )

    def get_acceptance_report(
        self, doc_type: str, start_date: Optional[datetime] = None
    ) -> dict:
        """Get acceptance statistics for a document"""
        query = (
            self.db.query(m.LegalDocumentAcceptance)
            .join(
                m.LegalDocument,
                m.LegalDocumentAcceptance.legal_document_id == m.LegalDocument.id,
            )
            .filter(m.LegalDocument.doc_type == doc_type)
        )

        if start_date:
            query = query.filter(m.LegalDocumentAcceptance.accepted_at >= start_date)

        acceptances = query.all()

        user_count = len(set(a.user_id for a in acceptances if a.user_id))
        customer_count = len(set(a.customer_id for a in acceptances if a.customer_id))
        total_acceptances = len(acceptances)

        return {
            "doc_type": doc_type,
            "total_acceptances": total_acceptances,
            "by_users": user_count,
            "by_customers": customer_count,
            "first_acceptance": acceptances[-1].accepted_at if acceptances else None,
            "last_acceptance": acceptances[0].accepted_at if acceptances else None,
        }

    # ==================== Consent Workflows ====================

    def get_required_consents(self) -> List[m.LegalDocument]:
        """Get all documents that require user acceptance"""
        return (
            self.db.query(m.LegalDocument)
            .filter(
                m.LegalDocument.is_active == True,
                m.LegalDocument.requires_acceptance == True,
            )
            .order_by(m.LegalDocument.display_order)
            .all()
        )

    def get_pending_consents(
        self, user_id: Optional[int] = None, customer_id: Optional[int] = None
    ) -> List[m.LegalDocument]:
        """Get documents that require acceptance but haven't been accepted yet"""
        required = self.get_required_consents()
        pending = []

        for doc in required:
            if not self.has_accepted(doc.id, user_id=user_id, customer_id=customer_id):
                pending.append(doc)

        return pending

    def accept_all_required(
        self,
        user_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> List[m.LegalDocumentAcceptance]:
        """Record acceptance of all required documents"""
        required = self.get_required_consents()
        acceptances = []

        for doc in required:
            if not self.has_accepted(doc.id, user_id=user_id, customer_id=customer_id):
                acceptance = self.record_acceptance(
                    legal_document_id=doc.id,
                    user_id=user_id,
                    customer_id=customer_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                acceptances.append(acceptance)

        return acceptances


# ==================== Default Legal Documents ====================


def setup_default_documents(db: Session, admin_user_id: int):
    """Initialize default legal documents"""
    defaults = [
        {
            "doc_type": "privacy_policy",
            "title": "Privacy Policy",
            "display_order": 1,
            "content": """# Privacy Policy

## Introduction
Vendly POS respects your privacy and is committed to protecting your personal data.

## Data Collection
We collect data necessary to provide our Point of Sale services, including:
- Customer information for transactions
- Employee information for system access
- Transaction history for reporting

## Data Usage
Your data is used for:
- Processing transactions
- Maintaining transaction history
- Generating reports and analytics
- Complying with tax and legal requirements

## Data Protection
We implement industry-standard security measures to protect your data against unauthorized access and misuse.

## Data Retention
Transaction data is retained in accordance with local tax and legal requirements.

## Your Rights
You have the right to access, correct, or delete your personal data. Contact our support team for requests.

## Contact Us
For privacy concerns, contact: privacy@vendly.com
""",
        },
        {
            "doc_type": "terms_of_service",
            "title": "Terms of Service",
            "display_order": 2,
            "content": """# Terms of Service

## Acceptance of Terms
By using Vendly POS, you agree to these Terms of Service.

## License Grant
Vendly POS grants you a limited, non-exclusive license to use this software for your business.

## User Responsibilities
- You are responsible for maintaining the confidentiality of your login credentials
- You agree to use the system in compliance with all applicable laws
- You will not attempt to gain unauthorized access to the system

## Limitation of Liability
Vendly POS is provided "as is" without warranties. We are not liable for any indirect, incidental, or consequential damages.

## Data Accuracy
You are responsible for ensuring that all data entered into the system is accurate and complies with applicable laws.

## Termination
We reserve the right to terminate access to the system for violations of these terms.

## Changes to Terms
We may update these terms at any time. Continued use constitutes acceptance of changes.

## Governing Law
These terms are governed by the laws of the jurisdiction in which Vendly POS operates.
""",
        },
        {
            "doc_type": "return_policy",
            "title": "Return Policy",
            "display_order": 3,
            "content": """# Return Policy

## Return Window
Customers may return or exchange items within [X] days of purchase.

## Conditions for Returns
- Items must be in original condition
- Original receipt or proof of purchase must be provided
- Items must not have been used or damaged

## Return Process
1. Bring item and receipt to store
2. Manager will inspect item
3. Refund will be processed to original payment method
4. Return will be recorded in system

## Non-Returnable Items
- Clearance items
- Final sale items
- Items purchased without receipt (store credit only)

## Return Exceptions
Exceptions require manager approval. Document reason in system.
""",
        },
    ]

    for default in defaults:
        existing = (
            db.query(m.LegalDocument)
            .filter(
                m.LegalDocument.doc_type == default["doc_type"],
                m.LegalDocument.is_active == True,
            )
            .first()
        )
        if not existing:
            doc = m.LegalDocument(
                doc_type=default["doc_type"],
                version=1,
                title=default["title"],
                content=default["content"],
                is_active=True,
                requires_acceptance=True,
                display_order=default["display_order"],
                created_by_user_id=admin_user_id,
            )
            db.add(doc)

    db.commit()
