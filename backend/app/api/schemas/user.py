"""api/schemas/user.py — Pydantic schemas for User Profile and Settings."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    portfolio_url: Optional[str] = ""


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_threshold: int = 70
    nvidia_model: str = "meta/llama-4-maverick-17b-128e-instruct"   # matches config.py Settings default
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    auto_apply: bool = False
    enable_notifications: bool = True
    auto_discover: bool = False


class UserSettingsUpdate(BaseModel):
    match_threshold: Optional[int] = None
    nvidia_model: Optional[str] = None
    embedding_model: Optional[str] = None
    auto_apply: Optional[bool] = None
    enable_notifications: Optional[bool] = None
    auto_discover: Optional[bool] = None
