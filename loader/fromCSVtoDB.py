import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy import text

def dataForConnectToDB():
	user = os.environ.get("PGUSER")
	password = os.environ.get("PGPASSWORD")
	host = os.environ.get("PGHOST")
	port = os.environ.get("PGPORT")
	database = os.environ.get("PGDATABASE")
	print(f"User from environ: {user}")
	print(f"Password from environ: {password}")
	print(f"Host from environ: {host}")
	print(f"Database from environ: {database}")
	print(f"Port from environ: {port}")
	url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
	engine = create_engine(url)
	try:
		with engine.connect() as conn:
			conn.execute(text("SELECT 1"))
		print("Connect success")
		return engine
	except Exception as e:
		print(f"Error of connecting: {e}")
		return None


def connectToDB():
	file_path = "data/data.csv"
	if not os.path.exists(file_path):
			print(f"❌ Файл не найден: {file_path}")
			return None
	try:
		print(f"Attempt for reading of .csv")
		rawData = pd.read_csv(file_path)
		print(f"Reading is success, rows - {len(rawData)},columns - {len(rawData.columns)}")
	except Exception as e:
		print(f"Error with reading of .csv")
		return None
	engine = dataForConnectToDB()
	if engine is None:
		print(f"Error with connecting to DB")
	try:
		rawData.to_sql('sales',engine, index=False, if_exists='replace')
		print(f"✅ Загружено {len(rawData)} строк в таблицу sales")
		return len(rawData) 
	except Exception as e:
		return None
	
def main():
	print(f"Вторая часть запускается")
	res = connectToDB()
	if res is None:
		print("Troubles")
	else:
		print("Success")
	print("✅ Программа завершена")
	print(f"✅ Вторая часть запущена")

if __name__ == "__main__":
    main()