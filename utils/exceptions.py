class AppError(Exception):
    """Base application error."""


class FileError(AppError):
    """Raised when file operations fail."""


class AnalysisError(AppError):
    """Raised when dataset analysis fails."""


class AIAgentError(AppError):
    """Raised when AI agent operations fail."""


class VisualizationError(AppError):
    """Raised when visualization generation fails."""


class ValidationError(AppError):
    """Raised when validation fails."""
