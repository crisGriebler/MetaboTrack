"""Local storage and comparison helpers for progress photos."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re

from PIL import Image


DIRECTIONS = {
    "frente": "Frente",
    "lado_direito": "Lado direito",
    "lado_esquerdo": "Lado esquerdo",
    "costas": "Costas",
}

_PHOTO_NAME = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})_(?P<direction>frente|lado_direito|lado_esquerdo|costas)_[0-9a-f]{12}$"
)


def save_photo(
    storage_dir: Path,
    *,
    captured_on: date,
    direction: str,
    original_name: str,
    content: bytes,
) -> Path:
    """Validate and store a locally uploaded progress photo without overwriting it."""
    if direction not in DIRECTIONS:
        raise ValueError("Direção de foto inválida.")
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except Exception as error:
        raise ValueError("O arquivo enviado não é uma imagem válida.") from error

    suffix = Path(original_name).suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError("Formato não suportado. Envie JPG, JPEG, PNG ou WEBP.")
    storage_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(content).hexdigest()[:12]
    destination = storage_dir / f"{captured_on.isoformat()}_{direction}_{digest}{suffix}"
    if not destination.exists():
        destination.write_bytes(content)
    return destination


def list_photos(storage_dir: Path) -> dict[date, dict[str, Path]]:
    """Return one local photo per direction and evaluation date."""
    grouped: dict[date, dict[str, Path]] = {}
    if not storage_dir.exists():
        return grouped
    for path in sorted(storage_dir.iterdir()):
        if not path.is_file():
            continue
        match = _PHOTO_NAME.match(path.stem)
        if not match:
            continue
        captured_on = date.fromisoformat(match.group("date"))
        grouped.setdefault(captured_on, {}).setdefault(match.group("direction"), path)
    return grouped

