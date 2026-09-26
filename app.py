from __future__ import annotations

from datetime import date, datetime
import os
from pathlib import Path
import sys

import pandas as pd
import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent / "src"))
from metabotrack.bioimpedance import METRICS, extract_bioimpedance, load_confirmed_exams, save_confirmed_exam
from metabotrack.history import PATIENT, exams_frame, measurements_frame, seed_initial_history
from metabotrack.photos import DIRECTIONS, list_photos, save_photo


DATA_DIR = Path(__file__).parent / "data"
DATABASE_PATH = DATA_DIR / "metabotrack.sqlite3"
EXAMS_DIR = DATA_DIR / "exams"
PHOTOS_DIR = DATA_DIR / "photos"

st.set_page_config(page_title="MetaboTrack | Maria Helena", page_icon="◒", layout="wide", initial_sidebar_state="expanded")


def require_authorized_user() -> None:
    """Protect the deployed dashboard with Google OIDC and an explicit allowlist."""
    if os.getenv("METABOTRACK_AUTH_ENABLED") != "true":
        return
    if not st.user.is_logged_in:
        st.title("🩺 MetaboTrack")
        st.write("Entre com uma conta Google autorizada para acessar o acompanhamento.")
        if st.button("Entrar com Google", type="primary"):
            st.login("google")
        st.stop()
    email = str(st.user.get("email", "")).lower()
    allowed = {item.strip().lower() for item in os.getenv("METABOTRACK_ALLOWED_EMAILS", "").split(",") if item.strip()}
    if email not in allowed:
        st.error("Esta conta não possui acesso ao acompanhamento.")
        if st.button("Sair"):
            st.logout()
        st.stop()


require_authorized_user()


def format_number(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def delta_text(current: float, initial: float, suffix: str) -> str:
    return f"{current - initial:+.1f} {suffix}".replace(".", ",")


def chart_data(frame: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    columns = [column for column in selected if column in frame.columns]
    return frame.set_index("data")[columns] if columns else pd.DataFrame()


def compact_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = source.copy()
    image.thumbnail((260, 360))
    return image


def progress_metric(icon: str, label: str, initial: str, current: str, variation: str) -> None:
    """Show aligned initial/current values without heading anchors inside cards."""
    st.markdown(
        f"""
        <section class="progress-card">
            <div class="progress-title">{icon} {label}</div>
            <div class="progress-values">
                <div><span>Inicial</span><strong>{initial}</strong></div>
                <div><span>Atual</span><strong>{current}</strong></div>
            </div>
            <div class="progress-variation">↘ Variação: {variation}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_new_exam_form() -> None:
    with st.expander("Adicionar novo exame de bioimpedância", expanded=False):
        st.caption("O laudo só entra no histórico após a sua conferência dos valores extraídos.")
        uploaded = st.file_uploader("Enviar novo laudo em PDF", type=["pdf"])
        if uploaded is None:
            return
        file_bytes = uploaded.getvalue()
        fingerprint = f"{uploaded.name}:{len(file_bytes)}"
        if st.session_state.get("exam_fingerprint") != fingerprint:
            with st.spinner("Lendo o laudo..."):
                st.session_state["extraction"] = extract_bioimpedance(file_bytes)
                st.session_state["exam_fingerprint"] = fingerprint
        extraction = st.session_state["extraction"]
        st.info(f"Método utilizado: {extraction.method}")
        for message in extraction.messages:
            st.write(message)
        rows = [{"Métrica": label, "Valor confirmado": extraction.metrics.get(key)} for key, label in METRICS.items()]
        reviewed = st.data_editor(pd.DataFrame(rows), column_config={"Métrica": st.column_config.TextColumn(disabled=True), "Valor confirmado": st.column_config.NumberColumn(format="%.2f")}, hide_index=True, width="stretch", key=f"review_{fingerprint}")
        evaluation_date = st.date_input("Data da avaliação", value=date.today(), key="new_exam_date")
        confirmed = st.checkbox("Conferi os valores no laudo e autorizo adicionar este novo teste ao histórico.")
        if st.button("Salvar novo teste confirmado", type="primary", disabled=not confirmed):
            confirmed_values = {key: float(value) for key, value in zip(METRICS, reviewed["Valor confirmado"]) if pd.notna(value)}
            if not confirmed_values:
                st.error("Informe pelo menos um valor confirmado antes de salvar.")
            else:
                save_confirmed_exam(DATABASE_PATH, EXAMS_DIR, evaluated_at=datetime.combine(evaluation_date, datetime.min.time()), extraction_method=extraction.method, source_filename=uploaded.name, source_bytes=file_bytes, metrics=confirmed_values)
                st.success("Novo teste de bioimpedância adicionado ao histórico local.")


def render_photo_comparison() -> None:
    st.divider()
    st.subheader("Comparação de fotos")
    st.caption("Selecione duas avaliações. A mais antiga é apresentada sempre à esquerda.")
    photos_by_date = list_photos(PHOTOS_DIR)
    dates = sorted(photos_by_date)
    if len(dates) < 2:
        st.info("Adicione fotos em pelo menos duas datas para iniciar a comparação.")
    else:
        selected_dates = st.multiselect("Datas para comparação", options=dates, default=[dates[0], dates[-1]], max_selections=2, format_func=lambda item: item.strftime("%d/%m/%Y"))
        if len(selected_dates) == 2:
            older, newer = sorted(selected_dates)
            tabs = st.tabs(list(DIRECTIONS.values()))
            for (direction, label), tab in zip(DIRECTIONS.items(), tabs):
                with tab:
                    _, left, _, right, _ = st.columns([0.8, 1, 0.2, 1, 1])
                    for column, current_date in ((left, older), (right, newer)):
                        photo = photos_by_date[current_date].get(direction)
                        with column:
                            st.markdown(f"**{label} · {current_date.strftime('%d/%m/%Y')}**")
                            if photo:
                                st.image(compact_image(photo))
                            else:
                                st.warning("Foto não disponível nesta data.")
        else:
            st.info("Selecione exatamente duas datas.")
    with st.expander("Adicionar nova foto", expanded=False):
        upload_date = st.date_input("Data da foto", value=date.today(), key="photo_date")
        upload_direction = st.selectbox("Direção da foto", options=list(DIRECTIONS), format_func=DIRECTIONS.get)
        photo_upload = st.file_uploader("Adicionar foto", type=["jpg", "jpeg", "png", "webp"], key="photo_upload")
        if st.button("Salvar nova foto", disabled=photo_upload is None):
            try:
                save_photo(PHOTOS_DIR, captured_on=upload_date, direction=upload_direction, original_name=photo_upload.name, content=photo_upload.getvalue())
                st.success("Foto adicionada ao acompanhamento.")
            except ValueError as error:
                st.error(str(error))


seed_initial_history(DATABASE_PATH)
measurements = measurements_frame()
exams = exams_frame(load_confirmed_exams(DATABASE_PATH))
latest_measurement, first_measurement = measurements.iloc[-1], measurements.iloc[0]
latest_exam, first_exam = exams.iloc[-1], exams.iloc[0]

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #123b3e; }
    [data-testid="stSidebar"] * { color: #f5fbfa; }
    .patient-label { color: #78d1c7; font-size: .78rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
    .patient-name { font-size: 1.35rem; font-weight: 700; line-height: 1.25; margin: .3rem 0 1.2rem; }
    .progress-card { border: 1px solid #3b4650; border-radius: .6rem; min-height: 192px; padding: 1rem; display: flex; flex-direction: column; box-sizing: border-box; }
    .progress-title { color: #dbe4ea; font-weight: 650; min-height: 1.7rem; }
    .progress-values { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; margin-top: .55rem; }
    .progress-values span { display: block; color: #aab5c0; font-size: .8rem; margin-bottom: .35rem; }
    .progress-values strong { display: block; color: #f6f8fb; font-size: 1.48rem; line-height: 1.18; white-space: nowrap; }
    .progress-variation { color: #bac5ce; font-size: .83rem; margin-top: auto; padding-top: .8rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="patient-label">Paciente em acompanhamento</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="patient-name">{PATIENT["name"]}</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**👤 Perfil**")
    st.write(f"♀️ Sexo: {PATIENT['sex']}")
    st.write(f"📏 Altura: {format_number(PATIENT['height_m'], 2)} m")
    st.write(f"🗓️ Início: {PATIENT['started_at'].strftime('%d/%m/%Y')}")
    st.divider()
    st.markdown("**📚 Registros disponíveis**")
    st.write(f"📏 {len(measurements)} avaliações de medidas")
    st.write(f"🧪 {len(exams)} exames de bioimpedância")
    st.write(f"📸 {len(list_photos(PHOTOS_DIR))} sessões de fotos")

st.title("🩺 Acompanhamento de tratamento")
st.caption("Uma visão amigável das medidas, composição corporal e fotos de evolução.")
st.subheader("✨ Evolução desde o início")
cards = st.columns(4)
with cards[0]:
    progress_metric("⚖️", "Peso", f"{format_number(first_measurement.peso_kg)} kg", f"{format_number(latest_measurement.peso_kg)} kg", delta_text(latest_measurement.peso_kg, first_measurement.peso_kg, "kg"))
with cards[1]:
    progress_metric("📏", "Cintura / abdômen", f"{format_number(first_measurement.cintura_abdomen_cm)} cm", f"{format_number(latest_measurement.cintura_abdomen_cm)} cm", delta_text(latest_measurement.cintura_abdomen_cm, first_measurement.cintura_abdomen_cm, "cm"))
with cards[2]:
    progress_metric("🧬", "Gordura corporal", f"{format_number(first_exam.percentual_gordura)}%", f"{format_number(latest_exam.percentual_gordura)}%", delta_text(latest_exam.percentual_gordura, first_exam.percentual_gordura, "p.p."))
with cards[3]:
    progress_metric("🧬", "Gordura visceral", f"Nível {int(first_exam.gordura_visceral_nivel)}", f"Nível {int(latest_exam.gordura_visceral_nivel)}", delta_text(latest_exam.gordura_visceral_nivel, first_exam.gordura_visceral_nivel, "níveis"))

st.divider()
left_chart, right_chart = st.columns(2)
with left_chart:
    st.subheader("🧪 Bioimpedância no tempo")
    bio_labels = {"peso_kg": "Peso (kg)", "percentual_gordura": "Gordura corporal (%)", "massa_gordura_kg": "Massa de gordura (kg)", "massa_livre_gordura_kg": "Massa livre de gordura (kg)", "imc": "IMC", "gordura_visceral_nivel": "Gordura visceral (nível)"}
    chosen_bio = st.multiselect("Indicadores de bioimpedância", options=list(bio_labels), default=["peso_kg", "percentual_gordura", "massa_gordura_kg"], format_func=bio_labels.get, key="bio_chart")
    data = chart_data(exams, chosen_bio).rename(columns=bio_labels)
    if data.empty:
        st.info("Escolha ao menos um indicador.")
    else:
        st.line_chart(data, height=310)
with right_chart:
    st.subheader("📈 Medidas corporais no tempo")
    measurement_labels = {"peso_kg": "Peso (kg)", "cintura_abdomen_cm": "Cintura / abdômen (cm)", "quadril_cm": "Quadril (cm)", "busto_cm": "Busto (cm)", "coxa_direita_cm": "Coxa direita (cm)", "coxa_esquerda_cm": "Coxa esquerda (cm)", "braco_direito_cm": "Braço direito (cm)", "braco_esquerdo_cm": "Braço esquerdo (cm)"}
    chosen_measurements = st.multiselect("Medidas para visualizar", options=list(measurement_labels), default=["peso_kg", "cintura_abdomen_cm", "quadril_cm"], format_func=measurement_labels.get, key="measurement_chart")
    data = chart_data(measurements, chosen_measurements).rename(columns=measurement_labels)
    if data.empty:
        st.info("Escolha ao menos uma medida.")
    else:
        st.line_chart(data, height=310)

st.subheader("🔎 Detalhes do último exame")
exam_cards = st.columns(4)
with exam_cards[0]:
    progress_metric("🫧", "Massa de gordura", f"{format_number(first_exam.massa_gordura_kg)} kg", f"{format_number(latest_exam.massa_gordura_kg)} kg", delta_text(latest_exam.massa_gordura_kg, first_exam.massa_gordura_kg, "kg"))
with exam_cards[1]:
    progress_metric("💪", "Massa livre de gordura", f"{format_number(first_exam.massa_livre_gordura_kg)} kg", f"{format_number(latest_exam.massa_livre_gordura_kg)} kg", delta_text(latest_exam.massa_livre_gordura_kg, first_exam.massa_livre_gordura_kg, "kg"))
with exam_cards[2]:
    progress_metric("🎯", "IMC", format_number(first_exam.imc), format_number(latest_exam.imc), delta_text(latest_exam.imc, first_exam.imc, ""))
with exam_cards[3]:
    progress_metric("💧", "Água corporal", f"{format_number(first_exam.agua_corporal_l)} L", f"{format_number(latest_exam.agua_corporal_l)} L", delta_text(latest_exam.agua_corporal_l, first_exam.agua_corporal_l, "L"))

render_new_exam_form()
render_photo_comparison()
