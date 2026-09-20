"""Extração, revisão e persistência de laudos de bioimpedância."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile

from pypdf import PdfReader


METRICS = {
    "peso_kg": "Peso (kg)",
    "percentual_gordura": "Percentual de gordura (%)",
    "massa_gordura_kg": "Massa de gordura (kg)",
    "massa_livre_gordura_kg": "Massa livre de gordura (kg)",
    "massa_muscular_esqueletica_kg": "Massa muscular esquelética (kg)",
    "agua_corporal_l": "Água corporal (L)",
    "agua_intracelular_l": "Água intracelular (L)",
    "agua_extracelular_l": "Água extracelular (L)",
    "imc": "IMC",
    "gordura_visceral_nivel": "Gordura visceral (nível)",
    "proteina_kg": "Proteína (kg)",
    "minerais_kg": "Minerais (kg)",
    "taxa_metabolica_basal_kcal": "Taxa metabólica basal (kcal)",
    "indice_apendicular_kg_m2": "Índice apendicular (kg/m²)",
    "idade_metabolica_anos": "Idade metabólica (anos)",
}


@dataclass
class ExtractionResult:
    method: str
    text: str
    metrics: dict[str, float]
    messages: list[str]


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract the embedded text layer from a PDF, if it exists."""
    # NamedTemporaryFile stays open on Windows and pypdf cannot reopen it there.
    with tempfile.TemporaryDirectory() as workspace:
        source = Path(workspace) / "laudo.pdf"
        source.write_bytes(pdf_bytes)
        reader = PdfReader(source)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def needs_ocr(text: str) -> bool:
    """PDFs with no meaningful text layer require OCR."""
    return len(re.sub(r"\s+", "", text)) < 80


def ocr_pdf(pdf_bytes: bytes) -> str:
    """Render a PDF and execute local Tesseract OCR when it is installed."""
    pdftoppm = shutil.which("pdftoppm")
    tesseract = shutil.which("tesseract")
    if not pdftoppm or not tesseract:
        missing = []
        if not pdftoppm:
            missing.append("Poppler (pdftoppm)")
        if not tesseract:
            missing.append("Tesseract OCR")
        raise RuntimeError(
            "OCR indisponível: instale " + " e ".join(missing) +
            ". O formulário de revisão continua disponível para preenchimento manual."
        )

    with tempfile.TemporaryDirectory() as workspace:
        source = Path(workspace) / "laudo.pdf"
        prefix = Path(workspace) / "pagina"
        source.write_bytes(pdf_bytes)
        subprocess.run(
            [pdftoppm, "-png", "-r", "220", str(source), str(prefix)],
            check=True,
            capture_output=True,
        )
        pages = sorted(Path(workspace).glob("pagina-*.png"))
        if not pages:
            raise RuntimeError("Não foi possível renderizar as páginas do PDF para OCR.")
        texts = []
        for page in pages:
            result = subprocess.run(
                [tesseract, str(page), "stdout", "-l", "por"],
                check=True,
                capture_output=True,
                text=True,
            )
            texts.append(result.stdout)
        return "\n".join(texts).strip()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_number(value: str, *, thousands: bool = False) -> float:
    value = value.strip().replace(" ", "")
    if thousands:
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(",", ".")
    return float(value)


def last_number_after(text: str, label_pattern: str, window: int = 180) -> float | None:
    match = re.search(label_pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    remaining = text[match.end():]
    next_heading = re.search(
        r"Peso\s*\(\s*kg\s*\)|Percentual\s+de\s*Gordura|"
        r"Massa\s+(?:Livre\s+de|de)\s*Gordura|Água\s+Corporal|"
        r"\bIMC\b|Taxa\s+Metabólica|Índice\s*Apendicular|"
        r"Idade\s*Metabólica|Nível\s+de\s+Gordura\s+Visceral",
        remaining,
        flags=re.IGNORECASE,
    )
    fragment = remaining[:next_heading.start()] if next_heading else remaining[:window]
    values = re.findall(r"(?<!\d)(\d{1,3}(?:[.,]\d+)?)(?!\d)", fragment)
    return parse_number(values[-1]) if values else None


def value_from_report_row(text: str, label_pattern: str) -> float | None:
    """Read the measured value printed on the line below a report's reference scale."""
    match = re.search(
        label_pattern + r"[^\n]*\n\s*(\d{1,3}(?:[.,]\d+)?)",
        text,
        flags=re.IGNORECASE,
    )
    return parse_number(match.group(1)) if match else None


def parse_avabio_380(text: str) -> dict[str, float]:
    """Parse the main metrics from AVABIO-380/AUANUTRI Portuguese reports.

    Results must always be reviewed by a person because OCR and report layouts vary.
    """
    flat = normalize_text(text)
    patterns = {
        "peso_kg": r"Peso\s*\(\s*kg\s*\)",
        "percentual_gordura": r"Percentual\s+de\s*Gordura",
        "massa_gordura_kg": r"Massa\s+de\s*Gordura\s*\(\s*kg\s*\)",
        "massa_livre_gordura_kg": r"Massa\s+Livre\s+de\s*Gordura\s*\(\s*kg\s*\)",
        "agua_corporal_l": r"Água\s+Corporal\s*\(\s*L\s*\)",
        "imc": r"\bIMC\b",
        "taxa_metabolica_basal_kcal": r"Taxa\s+Metabólica\s*Basal",
        "indice_apendicular_kg_m2": r"Índice\s*Apendicular",
        "idade_metabolica_anos": r"Idade\s*Metabólica",
    }
    metrics: dict[str, float] = {}
    for key, pattern in patterns.items():
        value = value_from_report_row(text, pattern) if key == "imc" else None
        if value is None:
            value = last_number_after(flat, pattern)
        if value is not None:
            metrics[key] = value

    visceral = re.search(r"Nível\s+de\s+Gordura\s+Visceral.{0,80}?Nível\s+(\d+)", flat, re.I)
    if visceral:
        metrics["gordura_visceral_nivel"] = float(visceral.group(1))

    # The basal rate uses a period as a thousands separator in this report.
    basal = re.search(r"Taxa\s+Metabólica\s*Basal.{0,80}?(\d{1,2}\.\d{3})\s*kcal", flat, re.I)
    if basal:
        metrics["taxa_metabolica_basal_kcal"] = parse_number(basal.group(1), thousands=True)
    return metrics


def extract_bioimpedance(pdf_bytes: bytes) -> ExtractionResult:
    embedded_text = extract_pdf_text(pdf_bytes)
    if not needs_ocr(embedded_text):
        metrics = parse_avabio_380(embedded_text)
        return ExtractionResult(
            method="Texto do PDF",
            text=embedded_text,
            metrics=metrics,
            messages=["A camada de texto do PDF foi extraída. Confira os valores antes de confirmar."],
        )

    try:
        ocr_text = ocr_pdf(pdf_bytes)
        metrics = parse_avabio_380(ocr_text)
        return ExtractionResult(
            method="OCR local",
            text=ocr_text,
            metrics=metrics,
            messages=["O PDF não contém texto extraível. A leitura veio de OCR e exige conferência humana."],
        )
    except RuntimeError as error:
        return ExtractionResult(
            method="Revisão manual",
            text="",
            metrics={},
            messages=[str(error), "Preencha os campos manualmente e confirme somente após comparar com o laudo."],
        )


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bioimpedance_exams (
                id INTEGER PRIMARY KEY,
                evaluated_at TEXT NOT NULL,
                extraction_method TEXT NOT NULL,
                source_filename TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                confirmed_metrics_json TEXT NOT NULL,
                saved_at TEXT NOT NULL
            )
            """
        )


def load_confirmed_exams(database_path: Path) -> list[dict[str, object]]:
    """Load saved assessments in chronological order for dashboard charts."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT evaluated_at, extraction_method, source_filename, confirmed_metrics_json
            FROM bioimpedance_exams
            ORDER BY evaluated_at
            """
        ).fetchall()
    return [
        {
            "evaluated_at": datetime.fromisoformat(evaluated_at),
            "extraction_method": extraction_method,
            "source_filename": source_filename,
            "metrics": json.loads(metrics_json),
        }
        for evaluated_at, extraction_method, source_filename, metrics_json in rows
    ]


def save_initial_exam_if_missing(
    database_path: Path,
    *,
    evaluated_at: datetime,
    source_filename: str,
    metrics: dict[str, float],
) -> None:
    """Register a previously reviewed assessment once, without duplicating it."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        exists = connection.execute(
            "SELECT 1 FROM bioimpedance_exams WHERE evaluated_at = ? AND source_filename = ?",
            (evaluated_at.isoformat(), source_filename),
        ).fetchone()
        if exists:
            return
        connection.execute(
            """
            INSERT INTO bioimpedance_exams
            (evaluated_at, extraction_method, source_filename, source_sha256, confirmed_metrics_json, saved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                evaluated_at.isoformat(),
                "Registro inicial revisado",
                source_filename,
                f"initial-{evaluated_at.date().isoformat()}",
                json.dumps(metrics, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )


def save_confirmed_exam(
    database_path: Path,
    storage_dir: Path,
    *,
    evaluated_at: datetime,
    extraction_method: str,
    source_filename: str,
    source_bytes: bytes,
    metrics: dict[str, float],
) -> None:
    """Persist only user-confirmed values and keep a local copy of the source file."""
    initialize_database(database_path)
    digest = sha256(source_bytes).hexdigest()
    storage_dir.mkdir(parents=True, exist_ok=True)
    source_path = storage_dir / f"{digest}.pdf"
    if not source_path.exists():
        source_path.write_bytes(source_bytes)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO bioimpedance_exams
            (evaluated_at, extraction_method, source_filename, source_sha256, confirmed_metrics_json, saved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                evaluated_at.isoformat(),
                extraction_method,
                source_filename,
                digest,
                json.dumps(metrics, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )
