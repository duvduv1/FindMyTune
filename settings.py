# settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1) Load .env from project root
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2) Helper to cast environment variables
def _get_env(key: str, default=None, cast=None):
    val = os.getenv(key, default)
    return cast(val) if (cast and val is not None) else val

# 3) Server / Network
SERVER_HOST = _get_env("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(_get_env("SERVER_PORT", "50213"))
USE_SSL     = _get_env("USE_SSL", "true").lower() in ("1", "true", "yes")

# 4) SSL certificates
SSL_CERT_PATH = os.path.join(
    _BASE_DIR,
    _get_env("SSL_CERT_PATH", os.path.join("certs", "localhost+2.pem"))
)
SSL_KEY_PATH = os.path.join(
    _BASE_DIR,
    _get_env("SSL_KEY_PATH", os.path.join("certs", "localhost+2-key.pem"))
)

# 5) Databases & encryption keys
USERS_DB_PATH = os.path.join(
    _BASE_DIR,
    _get_env("USERS_DB_PATH", "database/users.db")
)
SONGS_DB_PATH = os.path.join(
    _BASE_DIR,
    _get_env("SONGS_DB_PATH", "database/songs.db")
)

# 6) Session settings
SESSION_TIMEOUT = int(_get_env("SESSION_TIMEOUT", "1800"))

# 7) Brute‐force protection
MAX_FAILED_LOGIN   = int(_get_env("MAX_FAILED_LOGIN", "5"))
BRUTE_FORCE_WINDOW = int(_get_env("BRUTE_FORCE_WINDOW", "300"))

# 8) Rate‐limiting
RATE_LIMIT        = int(_get_env("RATE_LIMIT", "10"))
RATE_LIMIT_WINDOW = int(_get_env("RATE_LIMIT_WINDOW", "60"))

# 9) Model inference
MODEL_PATH      = os.path.join(
    _BASE_DIR,
    _get_env("MODEL_PATH")
)
NUM_CLASSES     = int(_get_env("NUM_CLASSES", "628"))
MODEL_POOL_SIZE = int(_get_env("MODEL_POOL_SIZE", "4"))

# 10) Audio & game directories
GAME_SONGS_DIR        = os.path.join(
    _BASE_DIR,
    _get_env("GAME_SONGS_DIR")
)
BACKGROUND_NOISES_DIR = os.path.join(
    _BASE_DIR,
    _get_env("AUDIO_BACKGROUND_NOISES")
)
SPECTROGRAM_DIR       = _get_env("SPECTROGRAM_DIR")

# 11) Spotify API credentials
SPOTIFY_CLIENT_ID     = _get_env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = _get_env("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI  = _get_env("SPOTIFY_REDIRECT_URI")
SPOTIFY_SCOPE         = _get_env("SPOTIFY_SCOPE")