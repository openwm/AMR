import os

OPENWM_URL: str = os.getenv("OPENWM_URL", "http://openwm-api:8000")
AMR_SPEED_DEFAULT: float = float(os.getenv("AMR_SPEED", "2.0"))
TICK_INTERVAL: float = float(os.getenv("TICK_INTERVAL", "0.1"))
CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
