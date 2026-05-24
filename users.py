"""
User Management Service
=======================
Handles User CRUD, Profile Management, Lifecycle States, and Directory Search.
Follows the Controller-Service-Repository pattern.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, select, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

# Simulated dependencies from auth.py (Authentication Service)
def get_db_session() -> Session:
    pass  # Placeholder for FastAPI Dependency

def get_current_admin() -> str:
    return "admin-id-123"  # Placeholder: requires JWT with 'ADMIN' role

def get_current_user() -> str:
    return "user-id-456"  # Placeholder: requires valid JWT


# ============================================================================
# 1. DATABASE SCHEMA (ORM MODELS)
# ============================================================================

class Base(DeclarativeBase):
    pass

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AccountStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending_verification"
    SUSPENDED = "suspended"
    BANNED = "banned"

class User(Base):
    """Core User Identity Table."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    
    # Sensitive fields - NEVER serialized to API
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Lifecycle Management
    status: Mapped[AccountStatus] = mapped_column(SQLEnum(AccountStatus), default=AccountStatus.PENDING, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships (1-to-1)
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped["UserPreferences"] = relationship("UserPreferences", back_populates="user", cascade="all, delete-orphan")
    
    # Simple roles representation (In a real app, this might be a many-to-many table)
    role: Mapped[str] = mapped_column(String(64), default="user")


class UserProfile(Base):
    """Public/semi-public user profile data."""
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    user: Mapped[User] = relationship("User", back_populates="profile")


class UserPreferences(Base):
    """Flexible NoSQL-style preferences storage via JSONB."""
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    # Stores flexible settings e.g. {"theme": "dark", "email_notifications": True}
    settings: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=lambda: {"theme": "light", "marketing_emails": False})

    user: Mapped[User] = relationship("User", back_populates="preferences")


# ============================================================================
# 2. SERIALIZATION & DTOs (PYDANTIC SCHEMAS)
# ============================================================================

class UserCreateDTO(BaseModel):
    """Validation schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserProfileUpdateDTO(BaseModel):
    """Validation schema for updating profile fields."""
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[HttpUrl] = None
    bio: Optional[str] = Field(None, max_length=1000)
    timezone: Optional[str] = Field(None, max_length=50)

class RoleUpdateDTO(BaseModel):
    new_role: str = Field(..., description="The role to assign to the user (e.g., 'developer', 'admin')")

class UserProfileResponse(BaseModel):
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    timezone: str
    model_config = ConfigDict(from_attributes=True)

class UserPreferencesResponse(BaseModel):
    settings: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    """
    STRICT DATA PRIVACY DTO.
    Explicitly defines what is allowed out of the API.
    password_hash and two_factor_secret are naturally dropped.
    """
    id: str
    email: EmailStr
    status: AccountStatus
    role: str
    created_at: datetime
    profile: Optional[UserProfileResponse]
    preferences: Optional[UserPreferencesResponse]
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedUserResponse(BaseModel):
    total_count: int
    page: int
    limit: int
    items: List[UserResponse]


# ============================================================================
# 3. REPOSITORY LAYER
# ============================================================================

class UserRepository:
    """Abstracts database queries and SQLAlchemy interactions."""
    
    def __init__(self, session: Session):
        self.db = session

    def get_by_id(self, user_id: str, include_deleted: bool = False) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email).where(User.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def search_users(self, page: int, limit: int, email: Optional[str], status: Optional[AccountStatus]) -> tuple[int, List[User]]:
        """Handles cursor/offset pagination and dynamic filtering."""
        stmt = select(User).where(User.deleted_at.is_(None))

        # Dynamic Filtering
        if email:
            stmt = stmt.where(User.email.ilike(f"%{email}%"))
        if status:
            stmt = stmt.where(User.status == status)

        # Count Total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = self.db.scalar(count_stmt) or 0

        # Pagination & Sorting
        offset = (page - 1) * limit
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        
        users = self.db.scalars(stmt).all()
        return total_count, list(users)

    def commit(self):
        self.db.commit()


# ============================================================================
# 4. SERVICE LAYER
# ============================================================================

class UserService:
    """Business logic, lifecycle management, and validation checks."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_safe_user(self, user_id: str) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if user.status in (AccountStatus.BANNED, AccountStatus.SUSPENDED):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is currently inactive.")
        return user

    def create_user(self, dto: UserCreateDTO) -> User:
        if self.repo.get_by_email(dto.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
        user = User(
            email=dto.email,
            password_hash=dto.password + "_mock_hash", # Mocked for simplicity
            status=AccountStatus.PENDING,
            role="user"
        )
        self.repo.db.add(user)
        self.repo.commit()
        return user

    def update_profile(self, user_id: str, dto: UserProfileUpdateDTO) -> User:
        user = self.get_safe_user(user_id)
        
        if not user.profile:
            user.profile = UserProfile(user_id=user_id)
            self.repo.db.add(user.profile)
            
        update_data = dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            # Convert HttpUrl to string for DB storage
            if key == 'avatar_url' and value is not None:
                value = str(value)
            setattr(user.profile, key, value)
            
        self.repo.commit()
        return user

    def soft_delete_account(self, user_id: str) -> None:
        """
        Soft Deletion prevents orphaned foreign keys across the system
        while effectively rendering the user 'deleted' from directories.
        """
        user = self.repo.get_by_id(user_id, include_deleted=True)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        if user.deleted_at is not None:
            raise HTTPException(status_code=400, detail="Account is already deleted.")
            
        # Flag as soft deleted, scramble PII if necessary for GDPR
        user.deleted_at = utc_now()
        user.status = AccountStatus.SUSPENDED
        self.repo.commit()

    def change_role(self, user_id: str, new_role: str) -> User:
        """Admin-only business logic for RBAC downgrades/upgrades."""
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        user.role = new_role
        self.repo.commit()
        return user


# ============================================================================
# 5. CONTROLLER LAYER (FASTAPI ROUTES)
# ============================================================================

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

def get_user_service(db: Session = Depends(get_db_session)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateDTO,
    svc: UserService = Depends(get_user_service)
):
    """Register a new user."""
    return svc.create_user(payload)


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user_id: str = Depends(get_current_user),
    svc: UserService = Depends(get_user_service)
):
    """Get the currently authenticated user's profile and preferences."""
    return svc.get_safe_user(current_user_id)


@router.patch("/me/profile", response_model=UserResponse)
def update_my_profile(
    payload: UserProfileUpdateDTO,
    current_user_id: str = Depends(get_current_user),
    svc: UserService = Depends(get_user_service)
):
    """Update public profile fields."""
    return svc.update_profile(current_user_id, payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    current_user_id: str = Depends(get_current_user),
    svc: UserService = Depends(get_user_service)
):
    """
    Soft Delete the user's account.
    Retains database integrity but locks the account and removes from searches.
    """
    svc.soft_delete_account(current_user_id)


# ----------------------------------------------------------------------------
# ADMIN DIRECTORY ENDPOINTS
# ----------------------------------------------------------------------------

@router.get("/directory", response_model=PaginatedUserResponse)
def get_directory(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    email: Optional[str] = Query(None, description="Search by partial email"),
    account_status: Optional[AccountStatus] = Query(None, description="Filter by state"),
    admin_id: str = Depends(get_current_admin), # Security Check
    db: Session = Depends(get_db_session)
):
    """
    Admin-Only Endpoint: Search, filter, and paginate the user directory.
    """
    repo = UserRepository(db)
    total, items = repo.search_users(page, limit, email, account_status)
    
    return PaginatedUserResponse(
        total_count=total,
        page=page,
        limit=limit,
        items=items # Will be automatically serialized cleanly by Pydantic
    )


@router.patch("/{target_user_id}/role", response_model=UserResponse)
def update_user_role(
    target_user_id: str,
    payload: RoleUpdateDTO,
    admin_id: str = Depends(get_current_admin), # Security Check
    svc: UserService = Depends(get_user_service)
):
    """
    Admin-Only Endpoint: Upgrade or downgrade a user's permission tier.
    """
    return svc.change_role(target_user_id, payload.new_role)