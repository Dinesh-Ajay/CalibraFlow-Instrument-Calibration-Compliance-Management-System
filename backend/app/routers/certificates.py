from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user, get_request_id, require_roles
from app.models.certificate import Certificate
from app.models.user import User
from app.schemas.certificate import CertificateCreate, CertificateOut, CertificateVerifyRequest
from app.services.certificate_service import create_or_upload_certificate, verify_certificate
from app.utils.file_storage import save_uploaded_file

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.post("/upload", response_model=CertificateOut, status_code=status.HTTP_201_CREATED)
async def upload_certificate_endpoint(
    request: Request,
    calibration_event_id: int = Form(...),
    asset_id: int = Form(...),
    certificate_number: str = Form(...),
    issue_date: str = Form(...),
    expiry_date: str = Form(...),
    supplier_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Maintenance Engineer", "Quality Engineer", "Administrator", "maint_eng", "quality_eng", "admin"])),
):
    try:
        dt_issue = datetime.fromisoformat(issue_date.replace("Z", "+00:00"))
        dt_expiry = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be ISO format")
    file_path = await save_uploaded_file(file, subfolder="certificates") if file else None
    cert_in = CertificateCreate(calibration_event_id=calibration_event_id, asset_id=asset_id, supplier_id=supplier_id, certificate_number=certificate_number, issue_date=dt_issue, expiry_date=dt_expiry)
    try:
        cert = create_or_upload_certificate(db=db, cert_in=cert_in, file_path=file_path, actor_id=current_user.id, request_id=get_request_id(request))
        out = CertificateOut.model_validate(cert)
        out.asset_code = cert.asset.asset_code if cert.asset else None
        out.asset_name = cert.asset.asset_name if cert.asset else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[CertificateOut])
def list_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "Maintenance Engineer", "admin", "quality_eng", "maint_eng"])),
    asset_id: Optional[int] = None,
    verification_status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(Certificate)
    if asset_id:
        query = query.filter(Certificate.asset_id == asset_id)
    if verification_status:
        query = query.filter(Certificate.verification_status == verification_status)
    certs = query.order_by(Certificate.id.desc()).offset(offset).limit(limit).all()
    results = []
    for c in certs:
        out = CertificateOut.model_validate(c)
        out.asset_code = c.asset.asset_code if c.asset else None
        out.asset_name = c.asset.asset_name if c.asset else None
        results.append(out)
    return results


@router.get("/{certificate_id}", response_model=CertificateOut)
def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "Maintenance Engineer", "admin", "quality_eng", "maint_eng"])),
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    out = CertificateOut.model_validate(cert)
    out.asset_code = cert.asset.asset_code if cert.asset else None
    out.asset_name = cert.asset.asset_name if cert.asset else None
    return out


@router.patch("/{certificate_id}/verify", response_model=CertificateOut)
def verify_certificate_endpoint(
    certificate_id: int,
    req: CertificateVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Quality Engineer", "Administrator", "quality_eng", "admin"])),
):
    try:
        cert = verify_certificate(db=db, cert_id=certificate_id, decision=req.verification_status, verifier_name=current_user.full_name or current_user.username, actor_id=current_user.id, request_id=get_request_id(request))
        out = CertificateOut.model_validate(cert)
        out.asset_code = cert.asset.asset_code if cert.asset else None
        out.asset_name = cert.asset.asset_name if cert.asset else None
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{certificate_id}/download")
def download_certificate_file(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "Maintenance Engineer", "admin", "quality_eng", "maint_eng"])),
):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="No certificate file available for download")
    return FileResponse(cert.file_path, filename=os.path.basename(cert.file_path))
