FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

CMD ["pytest"]
