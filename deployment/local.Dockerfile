FROM ghcr.io/astral-sh/uv:python3.13-alpine

RUN addgroup -g 1000 dev && adduser -u 1000 -G dev -D dev

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

RUN chown dev:dev /app

USER dev

# Копируем файлы зависимостей
COPY --chown=dev:dev pyproject.toml uv.lock ./

# Синхронизируем зависимости
RUN uv sync --frozen --no-cache

# Копируем остальной код
COPY --chown=dev:dev src/ /app/src/

# Добавляем пути к бинарникам окружения в PATH
ENV PATH="/app/.venv/bin:$PATH"

CMD ["sh", "-c", "exec uv run opentelemetry-instrument fastapi run src/main.py --host 0.0.0.0 --port \"${PORT}\""]
