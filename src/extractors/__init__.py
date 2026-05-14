# src/extractor/__init__.py

# This module serves as the entry point for all extractors. It imports the main extraction functions from each specific extractor module (e.g., resume, JD) and makes them available for external use. This allows other parts of the application to simply import from 'extractors' without needing to know the internal structure of the extractor modules.
from .resume import extract_resume
from .jd import extract_jd  

# Define __all__ for explicit exports when using 'from extractors import *'
__all__ = ["extract_resume", "extract_jd"]