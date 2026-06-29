# fetchers/__init__.py

from .arbeitnow_fetcher import fetch_arbeitnow_jobs
from .bundesagentur_fetcher import fetch_bundesagentur_jobs
from .job_fetcher import Job, fetch_adzuna_jobs, fetch_adzuna_multi

__all__ = [
    "Job",
    "fetch_adzuna_jobs",
    "fetch_adzuna_multi",
    "fetch_arbeitnow_jobs",
    "fetch_bundesagentur_jobs",
]
