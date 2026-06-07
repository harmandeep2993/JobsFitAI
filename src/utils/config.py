# src/utils/config.py
"""
Configuration loader for JobFitAI.

Loads configuration from:
    1. config.yaml — static provider configs, weights, limits
    2. .env — API keys (never hardcode in config.yaml)

Provider selection and API key are set at runtime via UI
through src/utils/session.py — not from this file.

The configuration is loaded once when the module is imported
and exposed as constants across the application.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

import logging
_logger = logging.getLogger(__name__)

status = load_dotenv()
_logger.info("Loaded .env file: %s", "success" if status else "not found")


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load and return configuration from YAML file.

    Args:
        config_path (str): Path to config.yaml

    Returns:
        dict: Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config file is invalid or empty
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Make sure config.yaml exists in project root"
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            raise ValueError("Config file is empty")

        _logger.info("Loaded config from %s", config_path)
        return config

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid config.yaml: {e}")


config = load_config()

# Common LLM parameters
_llm = config["llm_config"]

LLM_TIMEOUT            = _llm["timeout"]
LLM_TEMPERATURE        = _llm["temperature"]
LLM_MAX_OUTPUT_TOKENS  = _llm["max_output_tokens"]
RESUME_MAX_CHARS       = _llm["resume_max_input_chars"]
JD_MAX_CHARS           = _llm["jd_max_input_chars"]

# Provider configs
OPENAI_CONFIG      = config["openai_provider"]
GROQ_CONFIG        = config["groq_provider"]
GEMINI_CONFIG      = config["gemini_provider"]
HUGGINGFACE_CONFIG = config["huggingface_provider"]
OLLAMA_CONFIG      = config["ollama_provider"]

# All providers indexed by name
PROVIDER_CONFIGS = {
    "openai":      OPENAI_CONFIG,
    "groq":        GROQ_CONFIG,
    "gemini":      GEMINI_CONFIG,
    "huggingface": HUGGINGFACE_CONFIG,
    "ollama":      OLLAMA_CONFIG,
}

# Parser
MIN_TEXT_LIMIT = config["parser"]["min_text_parser_limit"]

# Validator
MAX_FILE_SIZE_MB = config["validator"]["max_file_size_mb"]
SUPPORTED_EXTENSIONS = set(config["validator"]["supported_extensions"])

# Matcher
WEIGHTS = config["matcher"]["weights"]
THRESHOLDS = config["matcher"]["thresholds"]

# Job search — target roles + entry-level filtering
_job_search = config.get("job_search", {})
SEARCH_COUNTRY        = _job_search.get("default_country", "de")
SEARCH_PER_TITLE      = _job_search.get("per_title_results", 5)
MAX_EXPERIENCE_YEARS  = _job_search.get("max_experience_years", 2)
MAX_AGE_DAYS          = _job_search.get("max_age_days", 45)
TARGET_TITLES         = _job_search.get("target_titles", [])
EXCLUDE_KEYWORDS      = _job_search.get("exclude_keywords", [])
ENTRY_KEYWORDS        = _job_search.get("entry_keywords", [])

# Logging
LOG_LEVEL = config.get("logging", {}).get("level", "INFO")