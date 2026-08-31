from sqlalchemy import text
import os
from sqlalchemy import create_engine
from sqlalchemy import text

def connect_to_db():
    user = os.environ("PGUSER")
    if user == None:
        print()
    password = os.environ("PGPASSWORD")
    if password == None:
        print()
    host = os.environ("PGHOST")
    if host == None:
        print()
    port = os.environ("PGPORT")
    if port == None:
        print()
    database = os.environ("PGDATABASE")
    url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url)

    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT 1"
                )
            )
        print(f"Connection is Ready")
        return engine
    except Exception as e:
        print("Connection is Failed")
        return None


    
def get_dynamic_report(
    engine,
    country: str = None,
    min_revenue: float = None,
    max_revenue: float = None,
    min_orders: int = None,
    sort_by: str = "total_revenue",
    sort_order: str = "DESC",
    limit: int = 20
):
    query = "SELECT * FROM sale_analysis_by_country WHERE  1 = 1"

def select_type_of_report():
    print("🌟 Добро пожаловать в Генератор Аналитических Отчетов! 🌟")
    print("\n📊 Доступные типы отчетов:")
    print("-" * 70)
    
    print("\n🔹 1. СВОДКА ПО СТРАНАМ (sale_analysis_by_country)")
    print("   📌 Доступные данные:")
    print("      • total_operations    - общее количество операций")
    print("      • total_revenue       - общая выручка")
    print("      • avg_price           - средняя цена товара")
    print("      • unique_clients      - количество уникальных клиентов")
    print("      • unique_products     - количество уникальных товаров")
    print("      • return_orders       - количество возвратов")
    print("      • return_orders_percent - доля возвратов (%)")
    print("      • returns_amount      - сумма возвратов (в деньгах)")
    print("      • returns_percent_of_revenue - доля возвратов в выручке (%)")
    print("      • avg_order_value     - средняя стоимость заказа")
    print("      • avg_items_per_order - среднее количество товаров в заказе")
    print("      • revenue_share_percent - доля страны в общих продажах (%)")
    print("      • first_sale_date     - дата первой продажи")
    print("      • last_sale_date      - дата последней продажи")
    print("      • active_months       - количество активных месяцев")
    print("      • avg_monthly_revenue - среднемесячная выручка")
    print("      • avg_return_per_order - средняя сумма возврата на заказ")
    print("      • active_days         - количество активных дней")
    
    print("\n🔹 2. ДИНАМИКА ПО МЕСЯЦАМ (sale_monthly_trend)")
    print("   📌 Доступные данные:")
    print("      • country             - страна")
    print("      • year_month          - месяц (YYYY-MM)")
    print("      • monthly_revenue     - выручка за месяц")
    print("      • monthly_orders      - количество заказов за месяц")
    print("      • adoption_of_new_clients - доля новых клиентов (%)")
    print("      • prev_month_revenue  - выручка за предыдущий месяц")
    print("      • revenue_growth_percent - процент роста выручки")
    
    print("\n🔹 3. ТОВАРНАЯ АНАЛИТИКА (product_sale_analysis)")
    print("   📌 Доступные данные:")
    print("      • country             - страна")
    print("      • stock_code          - артикул товара")
    print("      • description         - описание товара")
    print("      • total_quantity_sold - общее количество проданных единиц")
    print("      • total_quantity_return - общее количество возвращенных единиц")
    print("      • total_revenue       - общая выручка от товара")
    print("      • unique_buyers       - количество уникальных покупателей")
    print("      • revenue_share_in_country - доля товара в продажах страны (%)")
    print("      • avg_price           - средняя цена товара")
    
    print("\n🔹 4. RFM-СЕГМЕНТАЦИЯ КЛИЕНТОВ (customer_rfm_segments)")
    print("   📌 Доступные данные:")
    print("      • country             - страна")
    print("      • customer_id         - идентификатор клиента")
    print("      • monetary            - общая выручка от клиента")
    print("      • frequency           - количество заказов")
    print("      • recency             - дней с последней покупки")
    print("      • monetary_score      - балл по деньгам (1-3)")
    print("      • frequency_score     - балл по частоте (1-3)")
    print("      • recency_score       - балл по давности (1-3)")
    print("      • segment             - сегмент клиента (VIP, Лояльный, Новый, ...)")
    
    print("\n🔹 5. АНАЛИЗ ВОЗВРАТОВ (return_analysis)")
    print("   📌 Доступные данные:")
    print("      • country             - страна")
    print("      • stock_code          - артикул товара")
    print("      • avg_unit_price      - средняя цена товара")
    print("      • total_sold          - всего продано (шт.)")
    print("      • total_returns       - всего возвращено (шт.)")
    print("      • return_rate_percent - процент возвратов (%)")
    print("      • revenue_lost_from_returns - потерянная выручка от возвратов")
    
    print("\n🔹 6. СЫРЫЕ ДАННЫЕ (sales)")
    print("   📌 Доступные данные:")
    print("      • invoiceno           - номер заказа")
    print("      • stockcode           - артикул товара")
    print("      • description         - описание товара")
    print("      • quantity            - количество")
    print("      • invoicedate         - дата заказа")
    print("      • unitprice           - цена за единицу")
    print("      • customerid          - идентификатор клиента")
    print("      • country             - страна")
    
    print("\n" + "-"*70)
    print("💡 Для каждого отчета доступны:")
    print("   • Фильтрация по стране, дате, сумме выручки и другим параметрам")
    print("   • Сортировка по любому полю (ASC / DESC)")
    print("   • Ограничение количества строк (LIMIT)")
    print("   • Экспорт результатов в CSV")
    print("-"*70)
    print("\n➡️  Введите номер отчета (1-6):")
    type = input()
    return type
    
def check_in_db(word, table, row, engine):
    with engine.connect() as conn:
        query = """SELECT 1 FROM {table} t WHERE  t."{row}" = :word"""
        params = {"word": word}
        result = conn.execute(
            text(
                query
            ),word
        )
        rows = result.fetchall()
        if len(rows) == 0:
            return False
        return True

def main() :
    engine = connect_to_db()
    if engine == None:
        return None
    type = select_type_of_report()
    if type == 1:
        print("Какая страна вас интересует?")
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """SELECT DISTINCT s."Country" FROM sale_analysis_by_country s"""
                )
            )
            rows = result.fetchall()
            print("Доступные страны:")
            for row in rows:
                print(f" - {row[0]}")
            country = input("Введите название страны:")
            status = check_in_db(country, "sale_analysis_by_country", "Country", engine)
            if status == False:
                country = input("Введите название страны:")
                status = check_in_db(country, "sale_analysis_by_country", "Country", engine)
            country = input("Введите дату:")
            status = check_in_db(country, "sale_analysis_by_country", "Country", engine)
            if status == False:
                country = input("Введите название страны:")
                status = check_in_db(country, "sale_analysis_by_country", "Country", engine)
            if status == False:
                country = input("Введите название страны:")
                status = check_in_db(country, "sale_analysis_by_country", "Country", engine)


            

if __name__ == "__main__":
	main()