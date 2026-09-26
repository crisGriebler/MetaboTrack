FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8080
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT} --server.headless=true"]
