"""Initial patient history and dashboard data transformations."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from .bioimpedance import save_initial_exam_if_missing


PATIENT = {
    "name": "Maria Helena Menezes Albuquerque Sessak",
    "sex": "Feminino",
    "height_m": 1.69,
    "started_at": pd.Timestamp("2026-07-26"),
}

MEASUREMENTS = [
    {"data": "2026-07-26", "peso_kg": 80.0, "cintura_abdomen_cm": 102.0, "quadril_cm": 119.0, "coxa_direita_cm": 69.0, "coxa_esquerda_cm": 70.0, "braco_direito_cm": 31.0, "braco_esquerdo_cm": 30.0, "busto_cm": 98.0},
    {"data": "2026-08-21", "peso_kg": 76.0, "cintura_abdomen_cm": 96.5, "quadril_cm": 115.0, "coxa_direita_cm": 69.0, "coxa_esquerda_cm": 70.0, "braco_direito_cm": 30.0, "braco_esquerdo_cm": 31.0, "busto_cm": 97.0},
    {"data": "2026-09-18", "peso_kg": 70.7, "cintura_abdomen_cm": 94.0, "quadril_cm": 112.0, "coxa_direita_cm": 64.0, "coxa_esquerda_cm": 64.5, "braco_direito_cm": 30.0, "braco_esquerdo_cm": 29.0, "busto_cm": 95.0},
]

INITIAL_EXAMS = [
    {"evaluated_at": datetime(2026, 7, 24, 15, 25, 12), "source_filename": "Bioimpedância Maria Helena.pdf", "metrics": {"peso_kg": 80.0, "percentual_gordura": 42.6, "massa_gordura_kg": 34.1, "massa_livre_gordura_kg": 41.2, "massa_muscular_esqueletica_kg": 22.0, "agua_corporal_l": 30.1, "agua_intracelular_l": 22.5, "agua_extracelular_l": 7.7, "imc": 28.0, "gordura_visceral_nivel": 14.0, "proteina_kg": 12.6, "minerais_kg": 3.2, "taxa_metabolica_basal_kcal": 1545.0, "indice_apendicular_kg_m2": 7.06, "idade_metabolica_anos": 41.0}},
    {"evaluated_at": datetime(2026, 9, 18, 12, 0, 0), "source_filename": "Relatório de Avaliações (24).pdf", "metrics": {"peso_kg": 70.7, "percentual_gordura": 34.9, "massa_gordura_kg": 24.7, "massa_livre_gordura_kg": 41.7, "agua_corporal_l": 30.6, "imc": 24.8, "gordura_visceral_nivel": 11.0, "taxa_metabolica_basal_kcal": 1452.0, "indice_apendicular_kg_m2": 6.98, "idade_metabolica_anos": 38.0}},
]


def seed_initial_history(database_path) -> None:
    for exam in INITIAL_EXAMS:
        save_initial_exam_if_missing(database_path, **exam)


def measurements_frame() -> pd.DataFrame:
    frame = pd.DataFrame(MEASUREMENTS)
    frame["data"] = pd.to_datetime(frame["data"])
    return frame.sort_values("data")


def exams_frame(exams: list[dict[str, object]]) -> pd.DataFrame:
    records = []
    for exam in exams:
        records.append({"data": pd.Timestamp(exam["evaluated_at"]), **exam["metrics"]})
    return pd.DataFrame(records).sort_values("data") if records else pd.DataFrame()
