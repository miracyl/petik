#!/usr/bin/env bash
set -e

# Переход в директорию проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================================="
echo "🚀 1. Загрузка переменных окружения (.env)"
echo "=================================================="
if [ -f .env ]; then
    # Экспортируем переменные окружения из .env
    set -a
    source .env
    set +a
    echo "✅ Переменные из .env загружены."
else
    echo "⚠️  Файл .env не найден! Используются значения по умолчанию."
fi

echo ""
echo "=================================================="
echo "🧹 2. Очистка старых контейнеров и volumes"
echo "=================================================="
docker compose down -v --remove-orphans

echo ""
echo "=================================================="
echo "📦 3. Скачивание и сборка Docker-образов"
echo "=================================================="
docker compose pull postgres || true
docker compose build

echo ""
echo "=================================================="
echo "🐘 4. Запуск PostgreSQL и ожидание готовности"
echo "=================================================="
docker compose up -d postgres

echo "⏳ Ожидание прохождения healthcheck PostgreSQL..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' petproject 2>/dev/null)" = "healthy" ]; do
    sleep 2
done
echo "✅ PostgreSQL готов к приёму соединений!"

echo ""
echo "=================================================="
echo "🔄 5. Запуск загрузки данных (Loader) и ETL"
echo "=================================================="
# python_loader загрузит CSV в БД, затем python_etl сформирует витрины данных
docker compose up python_loader python_etl

echo ""
echo "=================================================="
echo "📊 6. Запуск аналитического отчёта (dynamic_report)"
echo "=================================================="

# Выбор интерпретатора Python (.venv или системный python3)
if [ -d ".venv" ] && [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# На хосте база доступна через localhost:5432
export PGHOST="localhost"
export PGPORT="${POSTGRES_PORT:-5432}"
export PGUSER="${POSTGRES_USER:-user1}"
export PGPASSWORD="${POSTGRES_PASSWORD:-641997}"
export PGDATABASE="${POSTGRES_DB:-petDB}"

echo "Запуск $PYTHON_CMD dynamic_report/dynamic_report.py..."
$PYTHON_CMD dynamic_report/dynamic_report.py
