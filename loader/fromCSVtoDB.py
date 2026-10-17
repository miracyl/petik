"""
Модуль первичной загрузки данных (Data Loader).
Читает исходный CSV-файл с транзакциями, выполняет базовую валидацию
качества данных (Data Quality check) и загружает сырые данные в PostgreSQL (таблица sales).
"""

import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text

error_log = []


def log_error(source: str, row_id: str, reason: str):
    """Логирует ошибку валидации строки датасета."""
    error_log.append({
        "source": source,
        "row_id": row_id,
        "reason": reason,
        "logged_at": datetime.now().isoformat()
    })


def get_db_engine():
    """Создает подключение к базе данных на основе переменных окружения."""
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD")
    host = os.environ.get("PGHOST")
    port = os.environ.get("PGPORT")
    database = os.environ.get("PGDATABASE")

    url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Подключение к базе данных успешно установлено.")
        return engine
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return None


def load_csv_to_db(file_path: str = "data/data.csv"):
    """
    Основная процедура загрузки:
    1. Чтение CSV-файла.
    2. Проверка качества данных (пропуски CustomerID, отрицательные UnitPrice).
    3. Загрузка в таблицу 'sales' в PostgreSQL.
    """
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return None

    try:
        print(f"Попытка чтения {file_path}...")
        raw_data = pd.read_csv(file_path)
        print(f"Успешно прочитано: {len(raw_data)} строк, {len(raw_data.columns)} столбцов.")
    except Exception as e:
        print(f"❌ Ошибка при чтении CSV-файла: {e}")
        return None

    print("Проверка качества данных (Data Quality)...")
    for _, row in raw_data.iterrows():
        if pd.isna(row.get("CustomerID")):
            log_error("sales", row.get("InvoiceNo", "unknown"), "CustomerID is null")
        if row.get("UnitPrice", 0) < 0:
            log_error("sales", row.get("InvoiceNo", "unknown"), "UnitPrice is negative")

    if error_log:
        pd.DataFrame(error_log).to_csv("data/error_log.csv", index=False)
        print(f"⚠️ Найдено {len(error_log)} аномалий в данных. Сохранено в data/error_log.csv")

    engine = get_db_engine()
    if engine is None:
        print("❌ Не удалось получить engine для записи данных.")
        return None

    try:
        raw_data.to_sql("sales", engine, index=False, if_exists="replace")
        print(f"✅ Успешно загружено {len(raw_data)} строк в таблицу 'sales'.")
        return len(raw_data)
    except Exception as e:
        print(f"❌ Ошибка при записи в PostgreSQL: {e}")
        return None
    finally:
        engine.dispose()


def main():
    print("=== Запуск модуля загрузки данных (Loader) ===")
    result = load_csv_to_db()
    if result is None:
        print("❌ Загрузка завершилась с ошибкой.")
        exit(1)
    else:
        print("✅ Загрузка данных успешно завершена.")


if __name__ == "__main__":
    main()
