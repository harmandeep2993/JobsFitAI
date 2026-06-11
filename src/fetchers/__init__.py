# src/fetchers/__init__.py

from .job_fetcher import Job, fetch_adzuna_jobs, fetch_adzuna_multi
from .arbeitnow_fetcher import fetch_arbeitnow_jobs

__all__ = ["Job", "fetch_adzuna_jobs", "fetch_adzuna_multi", "fetch_arbeitnow_jobs"]
