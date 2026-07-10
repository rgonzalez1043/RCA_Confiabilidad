"""
Configuración central del backend RCA.

Carga variables desde backend/.env (creado automáticamente por instalar.bat).
Todas las rutas se normalizan a rutas ABSOLUTAS para que el servicio de Windows
(NSSM) funcione sin importar el directorio de trabajo (CWD).
"""
import os
import logging
import secrets
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

logger = logging.getLogger("rca.config")

# ---------------------------------------------------------------------------
# Rutas base (absolutas, independientes del CWD)
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent          # .../RCA_Confiabilidad/backend
BASE_DIR = BACKEND_DIR.parent                          # .../RCA_Confiabilidad
ENV_PATH = BACKEND_DIR / ".env"

# Cargar el .env del backend (no del CWD)
load_dotenv(dotenv_path=ENV_PATH)


def _resolve_path(env_value: str, default: Path) -> Path:
    """Resolver una ruta: si es absoluta se usa tal cual; si es relativa, se
    interpreta desde la raíz del proyecto (BASE_DIR)."""
    p = Path(env_value) if env_value else default
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()
    return p.resolve()


class Config:
    # ---------------- Base de datos ----------------
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "rca_database")

    # ---------------- Servidor ----------------
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8007"))

    # ---------------- Rutas absolutas ----------------
    ARCHIVOS_PATH = str(_resolve_path(os.getenv("ARCHIVOS_PATH", ""), BASE_DIR / "archivos"))
    RESPALDOS_PATH = str(_resolve_path(os.getenv("RESPALDOS_PATH", ""), BASE_DIR / "respaldos"))
    LOGS_PATH = str(_resolve_path(os.getenv("LOGS_PATH", ""), BASE_DIR / "logs"))

    # ---------------- JWT / Seguridad ----------------
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))

    # ---------------- CORS ----------------
    _cors_raw = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()]

    # ---------------- Subida de archivos ----------------
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
    ALLOWED_EXTENSIONS = {
        "jpg", "jpeg", "png", "gif", "bmp", "webp",
        "pdf", "mp4", "mov", "avi", "csv", "xlsx", "docx",
    }

    @property
    def database_url(self) -> str:
        password = quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ""
        return (
            f"mysql+pymysql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_is_wildcard(self) -> bool:
        return "*" in self.CORS_ORIGINS


config = Config()


# ---------------------------------------------------------------------------
# Validación / auto-provisión de SECRET_KEY
# ---------------------------------------------------------------------------
def _persistir_secret_key(env_path: Path, key: str) -> None:
    """Escribir o actualizar SECRET_KEY=... en el archivo .env."""
    lines: list[str] = []
    encontrado = False
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("SECRET_KEY="):
                lines.append(f"SECRET_KEY={key}")
                encontrado = True
            else:
                lines.append(line)
    if not encontrado:
        lines.append(f"SECRET_KEY={key}")
    try:
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        logger.error("No se pudo escribir SECRET_KEY en %s: %s", env_path, exc)


_INSECURE_DEFAULTS = {
    "",
    "tu-clave-secreta-super-segura-cambiar-en-produccion",
    "changeme",
}

if config.SECRET_KEY in _INSECURE_DEFAULTS:
    nueva = secrets.token_urlsafe(48)
    config.SECRET_KEY = nueva
    _persistir_secret_key(ENV_PATH, nueva)
    logger.warning(
        "SECRET_KEY no configurada: se generó una clave aleatoria y se guardó en %s. "
        "Consérvala para no invalidar los tokens entre reinicios.", ENV_PATH
    )
else:
    logger.info("SECRET_KEY cargada desde variables de entorno.")