import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime
error_log = []  # ← Глобальный список для ошибок

def log_error(source, row_id, reason):
    error_log.append({
        "source": source,
        "row_id": row_id,
        "reason": reason,
        "logged_at": datetime.now().isoformat()
    })

def dataForConnectToDB():
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD")
    host = os.environ.get("PGHOST")
    port = os.environ.get("PGPORT")
    database = os.environ.get("PGDATABASE")
    print(f"Пользователь из окружения: {user}")
    print(f"Пароль из окружения: {password}")
    print(f"Хост из окружения: {host}")
    print(f"База данных из окружения: {database}")
    print(f"Порт из окружения: {port}")
    url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Подключение успешно")
        return engine
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None


def connectToDB():
    file_path = "data/data.csv"
    if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return None
    try:
        print(f"Попытка чтения .csv")
        rawData = pd.read_csv(file_path)
        print(f"Чтение успешно, строк - {len(rawData)}, столбцов - {len(rawData.columns)}")
    except Exception as e:
        print(f"Ошибка чтения .csv")
        return None
    print("Проверка качества данных")
    for idx, row in rawData.iterrows():
        if pd.isna(row.get("CustomerID")):
            log_error("sales", row.get("InvoiceNo", "unknown"), "CustomerID is null")

        if row.get("UnitPrice", 0) < 0:
            log_error("sales", row.get("InvoiceNo","unknown"), "UnitPrice is negative")

    if error_log:
        pd.DataFrame(error_log).to_csv("data/error_log.csv", index=False)
        print(f"Найдено {len(error_log)} ошибок. Сохранено в data/error_log.csv")
    
    engine = dataForConnectToDB()
    if engine is None:
        print(f"Ошибка подключения к БД")
    try:
        rawData.to_sql('sales', engine, index=False, if_exists='replace')
        print(f"✅ Загружено {len(rawData)} строк в таблицу sales")
        return len(rawData)
    except Exception as e:
        return None
    finally:
        engine.dispose()

def main():
    print(f"Вторая часть запускается")
    res = connectToDB()
    if res is None:
        print("Проблемы")
    else:
        print("Успешно")
        print("✅ Вторая часть запущена")
        print("✅ Программа завершена")

if __name__ == "__main__":
    main()