# Use a imagem oficial do Python como base
FROM python:3.12.0-slim
RUN pip install uv
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN uv install --no-root
COPY ./app ./app
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
