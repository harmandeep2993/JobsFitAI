# src/utils/config.py
"""
Configuration loader for JobFitAI.

Loads configuration from:
1. config.yaml
2. environment variables (.env)

The configuration is loaded once when the module is imported
and exposed as constants across the application.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before reading env vars
# .env sits in project root next to config.yaml
load_dotenv()


def load_config(config_path="config.yaml"):
    """
    Load configuration from yaml file.

    Parameters:
        config_path : str
        Path to config.yaml.

    Args:
        config_path (str): Path to config.yaml

    Returns:
        dict: Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file not found.
        ValueError: If config file is invalid or empty.
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

        return config

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid config.yaml: {e}")


# Load configuration once when module is imported
config = load_config()

# LLM Configuration
LLM_PROVIDER    = config["llm"]["provider"]
LLM_MODEL       = config["llm"]["model"]

# API key priority:
# 1. config.yaml
# 2. environment variable (LLM_API_KEY)
LLM_API_KEY = config["llm"].get("api_key") or os.getenv("LLM_API_KEY", "")

LLM_TIMEOUT     = config["llm"]["timeout"]
LLM_TEMPERATURE = config["llm"]["temperature"]
LLM_MAX_TOKENS  = config["llm"]["max_tokens"]

# Ollama Configuration
OLLAMA_URL        = config["ollama"]["url"]
OLLAMA_HEALTH_URL = config["ollama"]["health_url"]

# Parser Limit
# Check if the text is extracted from pdf
MIN_TEXT_LIMIT = config["parser"]["min_text_parser_limit"]

# Extractor Limits
RESUME_MAX_CHARS = config["extractor"]["resume_max_chars"]
JD_MAX_CHARS     = config["extractor"]["jd_max_chars"]

# Matcher Configuration
WEIGHTS    = config["matcher"]["weights"]
THRESHOLDS = config["matcher"]["thresholds"]

# Logging
# Controls console log level — DEBUG | INFO | WARNING | ERROR
# File handler always logs DEBUG and above regardless of this setting
LOG_LEVEL = config.get("logging", {}).get("level", "DEBUG")