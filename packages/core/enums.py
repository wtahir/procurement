from enum import StrEnum


class InputModality(StrEnum):
    TEXT = "text"
    VOICE = "voice"


class Locale(StrEnum):
    EN = "en"
    AR = "ar"


class ApprovalLevel(StrEnum):
    AUTO = "auto"
    PROJECT_MANAGER = "project_manager"
    DIRECTOR = "director"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PipelineStatus(StrEnum):
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class SupplierChannel(StrEnum):
    REST = "rest"
    SOAP = "soap"
    GRAPHQL = "graphql"
    SFTP_BATCH = "sftp_batch"
    EDI_WEBHOOK = "edi_webhook"
    MAINFRAME = "mainframe"
