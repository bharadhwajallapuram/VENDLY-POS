# ===========================================
# Legal Documents API - Privacy Policy & Terms
# ===========================================

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db import models as m
from app.services.legal_service import LegalService

router = APIRouter(prefix="/legal", tags=["legal"])


# ==================== Schemas ====================


class LegalDocumentCreate(BaseModel):
    doc_type: str
    title: str
    content: str
    content_html: Optional[str] = None
    requires_acceptance: bool = True
    display_order: int = 0


class LegalDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    display_order: Optional[int] = None


class LegalDocumentOut(BaseModel):
    id: int
    doc_type: str
    version: int
    title: str
    content: str
    content_html: Optional[str]
    is_active: bool
    requires_acceptance: bool
    display_order: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AcceptanceRecordOut(BaseModel):
    id: int
    legal_document_id: int
    user_id: Optional[int]
    customer_id: Optional[int]
    ip_address: Optional[str]
    accepted_at: datetime

    class Config:
        from_attributes = True


class ConsentOut(BaseModel):
    """Document requiring user consent"""

    id: int
    doc_type: str
    title: str
    content: str
    content_html: Optional[str]
    version: int
    requires_acceptance: bool
    has_accepted: bool


class AcceptanceReportOut(BaseModel):
    doc_type: str
    total_acceptances: int
    by_users: int
    by_customers: int
    first_acceptance: Optional[datetime]
    last_acceptance: Optional[datetime]


# ==================== Document Management ====================


@router.post("/documents", response_model=LegalDocumentOut, status_code=201)
def create_document(
    payload: LegalDocumentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new legal document (creates new version)"""
    if user.role != "admin":
        raise HTTPException(403, detail="Only admins can create legal documents")

    service = LegalService(db)
    doc = service.create_document(
        doc_type=payload.doc_type,
        title=payload.title,
        content=payload.content,
        created_by_user_id=user.id,
        content_html=payload.content_html,
        requires_acceptance=payload.requires_acceptance,
        display_order=payload.display_order,
    )
    return doc


@router.get("/documents", response_model=List[LegalDocumentOut])
def list_active_documents(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get all active legal documents"""
    service = LegalService(db)
    docs = service.get_all_active_documents()
    return docs


@router.get("/documents/type/{doc_type}", response_model=LegalDocumentOut)
def get_active_document(
    doc_type: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get current active version of a document"""
    service = LegalService(db)
    doc = service.get_active_document(doc_type)
    if not doc:
        raise HTTPException(404, detail="Document not found")
    return doc


@router.get(
    "/documents/type/{doc_type}/versions", response_model=List[LegalDocumentOut]
)
def get_document_versions(
    doc_type: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get all versions of a document"""
    if user.role != "admin":
        raise HTTPException(403, detail="Only admins can view document history")

    service = LegalService(db)
    docs = service.get_document_versions(doc_type)
    if not docs:
        raise HTTPException(404, detail="Document not found")
    return docs


@router.get("/documents/{doc_id}", response_model=LegalDocumentOut)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a specific document by ID"""
    doc = db.query(m.LegalDocument).filter(m.LegalDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, detail="Document not found")
    return doc


@router.put("/documents/{doc_id}", response_model=LegalDocumentOut)
def update_document(
    doc_id: int,
    payload: LegalDocumentUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update a legal document"""
    if user.role != "admin":
        raise HTTPException(403, detail="Only admins can update documents")

    service = LegalService(db)
    doc = service.update_document(
        doc_id=doc_id,
        title=payload.title,
        content=payload.content,
        content_html=payload.content_html,
        display_order=payload.display_order,
    )
    if not doc:
        raise HTTPException(404, detail="Document not found")
    return doc


# ==================== Consent & Acceptance ====================


@router.get("/consent", response_model=List[ConsentOut])
def get_required_consents(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[m.User] = Depends(get_current_user),
):
    """Get all documents requiring user acceptance"""
    service = LegalService(db)
    docs = service.get_required_consents()

    result = []
    user_id = user.id if user else None

    for doc in docs:
        has_accepted = service.has_accepted(doc.id, user_id=user_id)
        result.append(
            ConsentOut(
                id=doc.id,
                doc_type=doc.doc_type,
                title=doc.title,
                content=doc.content,
                content_html=doc.content_html,
                version=doc.version,
                requires_acceptance=doc.requires_acceptance,
                has_accepted=has_accepted,
            )
        )

    return result


@router.get("/pending-consents", response_model=List[ConsentOut])
def get_pending_consents(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get documents that haven't been accepted yet"""
    service = LegalService(db)
    docs = service.get_pending_consents(user_id=user.id)

    result = []
    for doc in docs:
        result.append(
            ConsentOut(
                id=doc.id,
                doc_type=doc.doc_type,
                title=doc.title,
                content=doc.content,
                content_html=doc.content_html,
                version=doc.version,
                requires_acceptance=doc.requires_acceptance,
                has_accepted=False,
            )
        )

    return result


@router.post("/accept/{doc_id}", response_model=AcceptanceRecordOut, status_code=201)
def accept_document(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Record acceptance of a legal document"""
    doc = db.query(m.LegalDocument).filter(m.LegalDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, detail="Document not found")

    service = LegalService(db)
    acceptance = service.record_acceptance(
        legal_document_id=doc_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return acceptance


@router.post("/accept-all", response_model=List[AcceptanceRecordOut], status_code=201)
def accept_all_required(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Record acceptance of all required documents"""
    service = LegalService(db)
    acceptances = service.accept_all_required(
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return acceptances


@router.get("/user-acceptances", response_model=List[AcceptanceRecordOut])
def get_user_acceptances(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get all documents accepted by current user"""
    service = LegalService(db)
    acceptances = service.get_user_acceptances(user.id)
    return acceptances


# ==================== Reporting ====================


@router.get("/report/acceptance/{doc_type}", response_model=AcceptanceReportOut)
def get_acceptance_report(
    doc_type: str,
    start_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get acceptance statistics for a document"""
    if user.role not in ["admin", "manager"]:
        raise HTTPException(403, detail="Only admins/managers can view reports")

    try:
        start = datetime.fromisoformat(start_date) if start_date else None
    except ValueError:
        raise HTTPException(400, detail="Invalid date format")

    service = LegalService(db)
    report = service.get_acceptance_report(doc_type, start_date=start)
    return report
