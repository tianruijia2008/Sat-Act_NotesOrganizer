"""
Custom exceptions for the SAT/ACT Notes Organizer.
"""

class NotesOrganizerError(Exception):
    """Base exception for the application."""
    pass

class ConfigurationError(NotesOrganizerError):
    """Raised when there's a configuration issue."""
    pass

class ProcessingError(NotesOrganizerError):
    """Raised when there's an error during processing."""
    pass

class OCRProcessingError(ProcessingError):
    """Raised when there's an error during OCR processing."""
    pass

class AIProcessingError(ProcessingError):
    """Raised when there's an error during AI processing."""
    pass

class FileProcessingError(ProcessingError):
    """Raised when there's an error processing files."""
    pass

class ValidationError(NotesOrganizerError):
    """Raised when there's a validation error."""
    pass