# utils/config.py

import yaml
from pathlib import Path


def load_config(config_path="config.yaml"):
    """
    Load configuration from yaml file.

    Args:
        config_path (str): Path to config.yaml

    Returns:
        dict: Configuration dictionary

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config file is invalid
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


# Load once at module level
# All other files import from here
config = load_config()

# Easy access shortcuts
OLLAMA_URL         = config["ollama"]["url"]
OLLAMA_HEALTH_URL  = config["ollama"]["health_url"]
OLLAMA_MODEL       = config["ollama"]["model"]
OLLAMA_TIMEOUT     = config["ollama"]["timeout"]
OLLAMA_TEMPERATURE = config["ollama"]["temperature"]
OLLAMA_MAX_TOKENS  = config["ollama"]["max_tokens"]

RESUME_MAX_CHARS   = config["extractor"]["resume_max_chars"]
JD_MAX_CHARS       = config["extractor"]["jd_max_chars"]

WEIGHTS            = config["matcher"]["weights"]
THRESHOLDS         = config["matcher"]["thresholds"]