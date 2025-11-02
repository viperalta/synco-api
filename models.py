"""
Modelos de datos para MongoDB usando Pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return {"type": "string"}

class ItemModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool = True

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None

class CalendarEventModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    google_event_id: str
    summary: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    location: Optional[str] = None
    status: str
    html_link: str
    is_all_day: bool = False
    calendar_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CalendarModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    google_calendar_id: str
    summary: str
    description: Optional[str] = None
    primary: bool = False
    access_role: str
    background_color: Optional[str] = None
    foreground_color: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class EventAttendanceModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    event_id: str  # ID del evento de Google Calendar
    attendees: List[str] = []  # Lista de nombres de usuarios que asistirán
    non_attendees: List[str] = []  # Lista de nombres de usuarios que NO asistirán
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AttendanceRequest(BaseModel):
    event_id: str
    user_name: str
    will_attend: bool = True  # True si asiste, False si no asiste

class AttendanceResponse(BaseModel):
    event_id: str
    attendees: List[str]
    non_attendees: List[str]
    total_attendees: int
    total_non_attendees: int
    message: str

# Modelos para autenticación
class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None
    nickname: Optional[str] = ""  # Nombre que se mostrará en la interfaz
    roles: List[str] = []  # Lista de roles del usuario
    tipo_eventos: List[str] = []  # Lista de tipos de eventos en los que participa
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserModel

class GoogleUserInfo(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    verified_email: bool = True

class RefreshTokenModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    token: str
    is_active: bool = True
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenRevokeRequest(BaseModel):
    refresh_token: str

# Modelos para administración de usuarios
class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    roles: Optional[List[str]] = None
    tipo_eventos: Optional[List[str]] = None
    is_active: Optional[bool] = None

class UserListResponse(BaseModel):
    users: List[UserModel]
    total: int
    skip: int
    limit: int

class UserRoleUpdateRequest(BaseModel):
    roles: List[str]

class UserNicknameUpdateRequest(BaseModel):
    nickname: str

# Modelos para gestión de eventos
class EventCreateRequest(BaseModel):
    summary: str
    description: Optional[str] = None
    start_datetime: str  # ISO format datetime
    end_datetime: str    # ISO format datetime
    location: Optional[str] = None
    calendar_id: str = "primary"

class EventUpdateRequest(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    location: Optional[str] = None

class EventDeleteResponse(BaseModel):
    message: str
    event_id: str
    deleted: bool

# Modelos para gestión de pagos
class PaymentModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId  # ID del usuario que realizó el pago
    user_name: str  # Nombre del usuario
    user_nickname: Optional[str] = None  # Nickname del usuario
    amount: float  # Monto del pago
    period: str  # Período en formato YYYYMM (ej: 202510)
    payment_date: datetime  # Fecha exacta del pago
    receipt_image_url: Optional[str] = None  # URL del comprobante en S3
    receipt_image_key: Optional[str] = None  # Clave del archivo en S3
    status: str = "pending"  # pending, verified, rejected
    notes: Optional[str] = None  # Notas adicionales
    verified_by: Optional[PyObjectId] = None  # ID del usuario que verificó el pago
    verified_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class PaymentCreateRequest(BaseModel):
    amount: float
    period: str  # Formato YYYYMM
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

class PaymentUpdateRequest(BaseModel):
    amount: Optional[float] = None
    period: Optional[str] = None
    payment_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_nickname: Optional[str] = None
    amount: float
    period: str
    payment_date: datetime
    receipt_image_url: Optional[str] = None
    status: str
    notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class PaymentListResponse(BaseModel):
    payments: List[PaymentResponse]
    total: int
    skip: int
    limit: int

class PaymentVerificationRequest(BaseModel):
    status: str  # verified, rejected
    notes: Optional[str] = None

class S3UploadResponse(BaseModel):
    upload_url: str
    file_key: str
    expires_in: int

class S3DownloadResponse(BaseModel):
    download_url: str
    expires_in: int

class ConfirmUploadRequest(BaseModel):
    file_key: str

class BulkDeletePaymentsRequest(BaseModel):
    payment_ids: List[str]  # Lista de IDs de pagos a eliminar

class BulkVerifyPaymentsRequest(BaseModel):
    payment_ids: List[str]  # Lista de IDs de pagos a verificar
    status: str  # "verified" o "rejected"
    notes: Optional[str] = None  # Notas de verificación

# Modelos para gestión de deudas
class DebtorInfo(BaseModel):
    user_id: str
    user_name: str
    user_nickname: Optional[str] = None
    amount: float

class DebtModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    period: str  # Período en formato YYYYMM (ej: 202510)
    debtors: List[DebtorInfo]  # Lista de deudores con sus deudas
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DebtCreateRequest(BaseModel):
    period: str
    debtors: List[DebtorInfo]

class DebtUpdateRequest(BaseModel):
    debtors: List[DebtorInfo]

class DebtResponse(BaseModel):
    id: str
    period: str
    debtors: List[DebtorInfo]
    total_debt: float
    created_at: datetime
    updated_at: datetime

class DebtListResponse(BaseModel):
    debts: List[DebtResponse]
    total: int
    skip: int
    limit: int

class PlayerDebtResponse(BaseModel):
    period: str
    amount: float
    user_name: str
    user_nickname: Optional[str] = None
