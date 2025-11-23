"""
OCC Data Transformer Service

Transforms OCC JobOffer models into encrypted JobPosting models
with proper PII handling and validation.

Responsibilities:
1. Validate OCC data
2. Normalize fields
3. Encrypt PII (email, phone)
4. Prepare for storage in database
5. Handle deduplication checks
"""

import logging
from typing import Optional
from datetime import datetime

from sqlmodel import Session

from app.models.job_posting import JobPosting
from app.services.occ_scraper_service import JobOffer


logger = logging.getLogger(__name__)


class OCCDataTransformer:
    """
    Transforms OCC JobOffer data into secure JobPosting records.
    
    Responsibilities:
    1. Validate OCC data completeness
    2. Normalize fields (trim, standardize)
    3. Extract and enrich data (skills already in JobOffer)
    4. Encrypt PII (email, phone) using built-in JobPosting methods
    5. Prepare for storage
    
    Example:
        transformer = OCCDataTransformer()
        job_posting = await transformer.transform(occ_offer, db_session)
        if job_posting:
            db.add(job_posting)
            db.commit()
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def transform(
        self,
        offer: JobOffer,
        db: Session,
    ) -> Optional[JobPosting]:
        """
        Transform JobOffer → JobPosting with encryption.
        
        Args:
            offer: OCC JobOffer data
            db: Database session for duplicate checking
        
        Returns:
            JobPosting model ready for storage, or None if validation fails
            
        Process:
        1. Validate required fields
        2. Check for duplicates in DB
        3. Normalize and clean data
        4. Set encrypted fields using JobPosting methods
        5. Create and return JobPosting
        """
        try:
            # Step 1: Validate required fields
            self._validate_offer(offer)
            
            # Step 2: Check for duplicates
            existing = db.query(JobPosting).filter(
                JobPosting.external_job_id == offer.job_id
            ).first()
            
            if existing:
                self.logger.info(f"Job {offer.job_id} already in DB, updating...")
                return await self._update_existing(existing, offer)
            
            # Step 3: Normalize and clean data
            normalized_email = self._normalize_email(offer.contact_info.get("email"))
            normalized_phone = self._normalize_phone(offer.contact_info.get("phone"))
            
            # Step 4: Create JobPosting with plaintext (will be encrypted by set_* methods)
            job_posting = JobPosting(
                external_job_id=offer.job_id,
                title=offer.title.strip(),
                company=offer.company.strip(),
                location=offer.location.strip(),
                description=offer.description or offer.full_description or "",
                
                # Encrypted PII - use placeholder, will be set below
                email="",
                email_hash="",
                phone=None,
                phone_hash=None,
                
                # Job metadata
                skills="[]",  # Will be set to JSON string below
                work_mode=offer.work_mode or "hybrid",
                job_type=offer.job_type or "full-time",
                salary_min=offer.salary.get("min") if offer.salary else None,
                salary_max=offer.salary.get("max") if offer.salary else None,
                currency="MXN",
                
                # Timestamps
                published_at=offer.publication_date or datetime.utcnow(),
                
                # Source tracking
                source="occ.com.mx",
            )
            
            # Step 5: Set encrypted fields using JobPosting methods
            if normalized_email:
                job_posting.set_email(normalized_email)
            else:
                # Email is required - use placeholder
                job_posting.set_email("no-email@placeholder.local")
                self.logger.warning(f"No email found for job {offer.job_id}, using placeholder")
            
            if normalized_phone:
                job_posting.set_phone(normalized_phone)
            
            # Set skills as JSON
            if offer.skills:
                job_posting.set_skills(offer.skills)
            
            self.logger.info(
                f"✅ JobPosting transformed from OCC job {offer.job_id}: {job_posting.title}"
            )
            return job_posting
            
        except ValueError as e:
            self.logger.error(f"Validation error for job {offer.job_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error transforming job {offer.job_id}: {e}", exc_info=True)
            return None
    
    def _validate_offer(self, offer: JobOffer) -> None:
        """
        Validate required fields in JobOffer.
        
        Args:
            offer: JobOffer to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not offer.job_id or not offer.job_id.strip():
            raise ValueError("job_id is required and must not be empty")
        
        if not offer.title or len(offer.title.strip()) < 4:
            raise ValueError("title is required and must be at least 4 characters")
        
        if not offer.company or not offer.company.strip():
            raise ValueError("company is required and must not be empty")
        
        if not offer.location or not offer.location.strip():
            raise ValueError("location is required and must not be empty")
        
        if not offer.description and not offer.full_description:
            raise ValueError("description or full_description is required")
        
        description_text = (offer.description or offer.full_description).strip()
        if len(description_text) < 10:
            raise ValueError("description must be at least 10 characters")
        
        # At least one contact method
        has_email = offer.contact_info and offer.contact_info.get("email")
        has_phone = offer.contact_info and offer.contact_info.get("phone")
        if not has_email and not has_phone:
            # Note: We're lenient here - use placeholder if neither provided
            self.logger.warning(f"No email or phone provided for job {offer.job_id}")
    
    async def _update_existing(
        self,
        existing: JobPosting,
        offer: JobOffer,
    ) -> JobPosting:
        """
        Update existing job posting with new data from OCC.
        
        Args:
            existing: Existing JobPosting in DB
            offer: New JobOffer data from OCC
            
        Returns:
            Updated JobPosting
        """
        # Update fields that might have changed
        existing.title = offer.title.strip()
        existing.description = offer.description or offer.full_description or ""
        existing.work_mode = offer.work_mode or "hybrid"
        existing.job_type = offer.job_type or "full-time"
        
        # Update salary if available
        if offer.salary:
            existing.salary_min = offer.salary.get("min")
            existing.salary_max = offer.salary.get("max")
        
        # Update skills
        if offer.skills:
            existing.set_skills(offer.skills)
        
        # Update contact info if available
        if offer.contact_info:
            email = self._normalize_email(offer.contact_info.get("email"))
            if email:
                existing.set_email(email)
            
            phone = self._normalize_phone(offer.contact_info.get("phone"))
            if phone:
                existing.set_phone(phone)
        
        existing.updated_at = datetime.utcnow()
        
        self.logger.info(f"✅ Updated existing job {existing.id}: {existing.title}")
        return existing
    
    def _normalize_email(self, email: Optional[str]) -> Optional[str]:
        """
        Normalize email address.
        
        Args:
            email: Email address (possibly with whitespace)
            
        Returns:
            Normalized email or None
        """
        if not email:
            return None
        
        normalized = email.strip().lower()
        
        # Basic email validation
        if "@" not in normalized or "." not in normalized:
            self.logger.warning(f"Invalid email format: {email}")
            return None
        
        return normalized
    
    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """
        Normalize phone number.
        
        Args:
            phone: Phone number (possibly with formatting)
            
        Returns:
            Normalized phone number or None
        """
        if not phone:
            return None
        
        normalized = phone.strip()
        
        # Basic phone validation - should have at least 10 digits
        digits_only = "".join(c for c in normalized if c.isdigit())
        if len(digits_only) < 10:
            self.logger.warning(f"Phone number too short: {phone}")
            return None
        
        return normalized
    
    def batch_transform(
        self,
        offers: list[JobOffer],
        db: Session,
        skip_errors: bool = True,
    ) -> tuple[list[JobPosting], int]:
        """
        Transform multiple JobOffers at once.
        
        Args:
            offers: List of JobOffer objects
            db: Database session
            skip_errors: If True, skip failed transformations; if False, raise on first error
            
        Returns:
            Tuple of (successful_postings, failed_count)
            
        Example:
            postings, failures = transformer.batch_transform(occ_offers, db)
            print(f"Transformed {len(postings)} jobs, {failures} failed")
        """
        successful = []
        failed = 0
        
        for offer in offers:
            try:
                # Note: We're calling async transform without await
                # This is a limitation - should be called from async context
                posting = self.transform_sync(offer, db)
                if posting:
                    successful.append(posting)
                else:
                    failed += 1
            except Exception as e:
                if not skip_errors:
                    raise
                self.logger.error(f"Failed to transform offer {offer.job_id}: {e}")
                failed += 1
        
        return successful, failed
    
    def transform_sync(
        self,
        offer: JobOffer,
        db: Session,
    ) -> Optional[JobPosting]:
        """
        Synchronous version of transform (for use outside async contexts).
        
        Note: Prefer async version when possible.
        
        Args:
            offer: OCC JobOffer data
            db: Database session
            
        Returns:
            JobPosting model or None if validation fails
        """
        try:
            self._validate_offer(offer)
            
            existing = db.query(JobPosting).filter(
                JobPosting.external_job_id == offer.job_id
            ).first()
            
            if existing:
                self.logger.info(f"Job {offer.job_id} already in DB")
                # Return without updating in sync mode
                return existing
            
            normalized_email = self._normalize_email(offer.contact_info.get("email"))
            normalized_phone = self._normalize_phone(offer.contact_info.get("phone"))
            
            job_posting = JobPosting(
                external_job_id=offer.job_id,
                title=offer.title.strip(),
                company=offer.company.strip(),
                location=offer.location.strip(),
                description=offer.description or offer.full_description or "",
                email="",
                email_hash="",
                phone=None,
                phone_hash=None,
                skills="[]",
                work_mode=offer.work_mode or "hybrid",
                job_type=offer.job_type or "full-time",
                currency="MXN",
                published_at=offer.publication_date or datetime.utcnow(),
                source="occ.com.mx",
            )
            
            if normalized_email:
                job_posting.set_email(normalized_email)
            else:
                job_posting.set_email("no-email@placeholder.local")
            
            if normalized_phone:
                job_posting.set_phone(normalized_phone)
            
            if offer.skills:
                job_posting.set_skills(offer.skills)
            
            return job_posting
            
        except Exception as e:
            self.logger.error(f"Sync transform error for {offer.job_id}: {e}")
            return None
