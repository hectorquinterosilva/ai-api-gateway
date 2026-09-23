from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ----------------------------
# Base compartida
# ----------------------------
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


# ----------------------------
# Entrada: crear usuario
# ----------------------------
class UserCreate(UserBase):
    role: str = Field(default="user", max_length=50)
    tenant_id: str | None = Field(default=None, max_length=64)


# ----------------------------
# Entrada: actualizar usuario (parcial)
# ----------------------------
class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    role: str | None = Field(default=None, max_length=50)
    tenant_id: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None


# ----------------------------
# Salida: usuario
# ----------------------------
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------
# Salida: lista paginada
# ----------------------------
class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    skip: int
    limit: int
