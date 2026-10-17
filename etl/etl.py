"""
Модуль ETL (Extract, Transform, Load) / Витрины данных.
Преобразует сырые данные из таблицы 'sales' и формирует 5 аналитических витрин:
1. return_analysis - Аналитика возвратов и потерянной выручки.
2. customer_rfm_segments - RFM-сегментация клиентской базы.
3. product_sale_analysis - Товарная аналитика и доли в продажах по странам.
4. sale_monthly_trend - Помесячный тренд выручки (MoM) и доля новых клиентов.
5. sale_analysis_by_country - Сводная витрина метрик интернет-магазина по странам.
"""

import os
from sqlalchemy import create_engine, text


def connect_to_db():
    """Подключение к PostgreSQL на основе переменных окружения."""
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD")
    host = os.environ.get("PGHOST")
    port = os.environ.get("PGPORT")
    database = os.environ.get("PGDATABASE")

    url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Подключение к базе данных установлено (ETL).")
        return engine
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных (ETL): {e}")
        return None


def return_analysis(engine):
    """
    Витрина return_analysis:
    Анализирует возвраты товаров в разрезе стран:
    - total_sold: количество проданных единиц (Quantity > 0)
    - total_returns: количество возвратов (Quantity < 0)
    - return_rate_percent: процент возвратов от продаж
    - revenue_lost_from_returns: упущенная выручка в денежном выражении
    """
    print("Создание витрины: return_analysis...")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS return_analysis;"))
            conn.execute(
                text("""
                    CREATE TABLE return_analysis AS
                    WITH modify AS (
                        SELECT s.*
                        FROM sales s
                    )
                    SELECT 
                        s."Country" AS country,
                        s."StockCode" AS stock_code,
                        ROUND(AVG(s."UnitPrice")::DECIMAL, 2) AS avg_unit_price,
                        SUM(s."Quantity") FILTER (WHERE s."Quantity" > 0) AS total_sold,
                        ABS(COALESCE(SUM(s."Quantity") FILTER (WHERE s."Quantity" < 0), 0)) AS total_returns,
                        ABS(
                            ROUND(
                                COALESCE(SUM(s."Quantity") FILTER (WHERE s."Quantity" < 0)::DECIMAL, 0) 
                                / NULLIF(SUM(s."Quantity") FILTER (WHERE s."Quantity" > 0)::DECIMAL, 0) * 100.0,
                                2
                            )
                        ) AS return_rate_percent,
                        ABS(
                            ROUND(
                                COALESCE(SUM(s."Quantity" * s."UnitPrice") FILTER (WHERE s."Quantity" < 0)::DECIMAL, 0),
                                2
                            )
                        ) AS revenue_lost_from_returns
                    FROM sales s
                    WHERE s."CustomerID" IS NOT NULL
                    GROUP BY s."Country", s."StockCode"
                    ORDER BY return_rate_percent DESC NULLS LAST;
                """)
            )
        print("✅ Витрина 'return_analysis' успешно создана.")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании return_analysis: {e}")
        return None


def customer_rfm_segments(engine):
    """
    Витрина customer_rfm_segments:
    Классическая RFM-сегментация клиентов:
    - Recency (R): давность последней покупки (в днях относительно максимальной даты в датасете).
    - Frequency (F): количество уникальных заказов клиента.
    - Monetary (M): суммарная выручка от клиента.
    Метрики разбиваются на перцентили через NTILE(3), после чего клиентам
    присваиваются бизнес-сегменты: VIP, Лояльный, Новый, Постоянный, Спящий, Потерянный.
    """
    print("Создание витрины: customer_rfm_segments...")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS customer_rfm_segments;"))
            conn.execute(
                text("""
                    CREATE TABLE customer_rfm_segments AS
                    WITH mod AS (
                        SELECT 
                            s."Country" AS country,
                            s."CustomerID"::INTEGER AS customer_id, 
                            ROUND(SUM(s."UnitPrice" * s."Quantity")::DECIMAL, 2) AS monetary,
                            COUNT(DISTINCT s."InvoiceNo") AS frequency,
                            ROUND(
                                EXTRACT(DAY FROM (SELECT MAX("InvoiceDate"::TIMESTAMP) FROM sales) - MAX(s."InvoiceDate"::TIMESTAMP))
                            ) AS recency
                        FROM sales s 
                        GROUP BY s."CustomerID", s."Country"
                    ),
                    modi AS (
                        SELECT
                            m.*,
                            NTILE(3) OVER(PARTITION BY m."country" ORDER BY monetary DESC) AS monetary_score,
                            NTILE(3) OVER(PARTITION BY m."country" ORDER BY frequency DESC) AS frequency_score,
                            NTILE(3) OVER(PARTITION BY m."country" ORDER BY recency ASC) AS recency_score
                        FROM mod m
                    )
                    SELECT 
                        m.*,
                        CASE
                            WHEN m."recency_score" = 3 AND m."frequency_score" = 3 AND m."monetary_score" = 3 THEN 'VIP'
                            WHEN m."recency_score" = 3 AND m."frequency_score" >= 2 AND m."monetary_score" >= 2 THEN 'Лояльный'
                            WHEN m."recency_score" = 3 AND m."frequency_score" = 1 THEN 'Новый'
                            WHEN m."recency_score" = 2 AND m."frequency_score" >= 2 AND m."monetary_score" >= 2 THEN 'Постоянный'
                            WHEN m."recency_score" = 2 AND m."frequency_score" <= 1 THEN 'Спящий'
                            WHEN m."recency_score" = 1 THEN 'Потерянный'
                            ELSE 'Другой'
                        END AS segment
                    FROM modi m
                    ORDER BY m."country" ASC, m."customer_id" ASC;
                """)
            )
        print("✅ Витрина 'customer_rfm_segments' успешно создана.")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании customer_rfm_segments: {e}")
        return None


def product_sale_analysis(engine):
    """
    Витрина product_sale_analysis:
    Товарная аналитика по странам:
    - total_quantity_sold: всего продано единиц товара.
    - total_revenue: выручка от товара.
    - unique_buyers: число уникальных покупателей товара.
    - revenue_share_in_country: доля выручки товара в общей выручке страны (%).
    """
    print("Создание витрины: product_sale_analysis...")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS product_sale_analysis;"))
            conn.execute(
                text("""
                    CREATE TABLE product_sale_analysis AS
                    WITH modify AS (						
                        SELECT 
                            s.*,
                            SUM(s."Quantity" * s."UnitPrice") OVER(PARTITION BY s."Country") AS country_revenue
                        FROM sales s
                    )
                    SELECT
                        m."Country" AS country,
                        m."StockCode" AS stock_code,
                        MAX(m."Description") AS description,
                        COALESCE(SUM(m."Quantity") FILTER (WHERE m."Quantity" > 0), 0) AS total_quantity_sold,
                        COALESCE(SUM(m."Quantity") FILTER (WHERE m."Quantity" < 0), 0) AS total_quantity_return,
                        ROUND(SUM(m."Quantity" * m."UnitPrice")::DECIMAL, 2) AS total_revenue,
                        COUNT(DISTINCT m."CustomerID") AS unique_buyers,
                        GREATEST(
                            0,
                            ROUND(
                                COALESCE(SUM(m."Quantity" * m."UnitPrice"), 0)::DECIMAL
                                / NULLIF(MAX(m."country_revenue"), 0)::DECIMAL * 100.0,
                                2
                            )
                        ) AS revenue_share_in_country,
                        ROUND(AVG(m."UnitPrice") FILTER (WHERE m."Quantity" > 0)::DECIMAL, 2) AS avg_price
                    FROM modify m
                    GROUP BY m."Country", m."StockCode"
                    ORDER BY total_revenue DESC NULLS LAST;
                """)
            )
        print("✅ Витрина 'product_sale_analysis' успешно создана.")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании product_sale_analysis: {e}")
        return None


def sale_monthly_trend(engine):
    """
    Витрина sale_monthly_trend:
    Помесячная динамика продаж в разрезе стран:
    - monthly_revenue: выручка за месяц.
    - prev_month_revenue: выручка за предыдущий месяц (через оконную функцию LAG).
    - revenue_growth_percent: процент прироста выручки MoM.
    - adoption_of_new_clients: доля клиентов, сделавших первый заказ в данном месяце.
    """
    print("Создание витрины: sale_monthly_trend...")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS sale_monthly_trend;"))
            conn.execute(
                text("""
                    CREATE TABLE sale_monthly_trend AS
                    WITH modify AS (
                        SELECT
                            s.*,
                            MIN(s."InvoiceDate"::DATE) OVER(PARTITION BY s."Country", s."CustomerID") AS first_order_of_client
                        FROM sales s
                    ),
                    monthly_stats AS (
                        SELECT
                            m."Country" AS country,
                            DATE_TRUNC('month', m."InvoiceDate"::DATE)::DATE AS year_month,
                            ROUND(COALESCE(SUM(m."UnitPrice" * m."Quantity"), 0)::DECIMAL, 2) AS monthly_revenue,
                            COUNT(DISTINCT m."InvoiceNo") AS monthly_orders,
                            ROUND(
                                COUNT(DISTINCT m."CustomerID") FILTER (
                                    WHERE DATE_TRUNC('month', m."first_order_of_client"::DATE) = DATE_TRUNC('month', m."InvoiceDate"::DATE)
                                )::DECIMAL
                                / NULLIF(COUNT(DISTINCT m."CustomerID"), 0) * 100,
                                2
                            ) AS adoption_of_new_clients
                        FROM modify m
                        GROUP BY m."Country", DATE_TRUNC('month', m."InvoiceDate"::DATE)
                    )
                    SELECT 
                        *,
                        LAG(monthly_revenue, 1, 0) OVER (PARTITION BY country ORDER BY year_month) AS prev_month_revenue,
                        ROUND(
                            (monthly_revenue - LAG(monthly_revenue, 1, 0) OVER (PARTITION BY country ORDER BY year_month))
                            / NULLIF(LAG(monthly_revenue, 1, 0) OVER (PARTITION BY country ORDER BY year_month), 0) * 100,
                            2
                        ) AS revenue_growth_percent
                    FROM monthly_stats
                    ORDER BY country ASC, year_month ASC;
                """)
            )
        print("✅ Витрина 'sale_monthly_trend' успешно создана.")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании sale_monthly_trend: {e}")
        return None


def analysis_of_sells_of_country(engine):
    """
    Витрина sale_analysis_by_country:
    Агрегированные KPI интернет-магазина по каждой стране:
    - total_operations: общее количество строк/операций.
    - total_revenue: суммарная выручка.
    - unique_clients: количество уникальных покупателей.
    - return_orders_percent: доля возвратов среди заказов.
    - avg_order_value: средняя стоимость заказа (AOV).
    - revenue_share_percent: доля страны в мировых продажах магазина.
    """
    print("Создание витрины: sale_analysis_by_country...")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS sale_analysis_by_country;"))
            conn.execute(
                text("""
                    CREATE TABLE sale_analysis_by_country AS
                    WITH modify AS (
                        SELECT
                            sales.*,
                            COUNT(sales."Quantity") OVER(
                                PARTITION BY sales."Country", DATE_TRUNC('month', sales."InvoiceDate"::DATE)
                            ) AS rows_in_month
                        FROM sales
                    )
                    SELECT 
                        m."Country" AS country,
                        COUNT(*) AS total_operations,
                        ROUND(SUM(m."UnitPrice" * m."Quantity")::DECIMAL, 2) AS total_revenue,
                        ROUND(AVG(m."UnitPrice")::DECIMAL, 2) AS avg_price,
                        COUNT(DISTINCT m."CustomerID") AS unique_clients,
                        COUNT(DISTINCT m."StockCode") AS unique_products,
                        COUNT(*) FILTER (WHERE m."Quantity" < 0) AS return_orders,
                        ROUND(COUNT(*) FILTER (WHERE m."Quantity" < 0)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 2) AS return_orders_percent,
                        ROUND(SUM(ABS(m."Quantity") * m."UnitPrice") FILTER (WHERE m."Quantity" < 0)::DECIMAL, 2) AS returns_amount,
                        ROUND(
                            SUM(ABS(m."Quantity") * m."UnitPrice") FILTER (WHERE m."Quantity" < 0)::DECIMAL 
                            / NULLIF(SUM(m."Quantity" * m."UnitPrice") FILTER (WHERE m."Quantity" > 0), 0)::DECIMAL * 100,
                            2
                        ) AS returns_percent_of_revenue,
                        ROUND(
                            COALESCE(SUM(m."Quantity" * m."UnitPrice") FILTER (WHERE m."Quantity" > 0)::DECIMAL, 0)
                            / NULLIF(COUNT(DISTINCT m."InvoiceNo")::DECIMAL, 0),
                            2
                        ) AS avg_order_value,
                        ROUND(
                            COALESCE(SUM(m."Quantity") FILTER (WHERE m."Quantity" > 0)::DECIMAL, 0)
                            / NULLIF(COUNT(DISTINCT m."InvoiceNo"), 0),
                            2
                        ) AS avg_items_per_order,
                        ROUND(
                            SUM(m."Quantity" * m."UnitPrice")::DECIMAL
                            / NULLIF((SELECT SUM(m."Quantity" * m."UnitPrice") FROM modify m)::DECIMAL, 0) * 100.0,
                            2
                        ) AS revenue_share_percent,
                        TO_CHAR(MIN(m."InvoiceDate"::DATE), 'YYYY-MM-DD') AS first_sale_date,
                        TO_CHAR(MAX(m."InvoiceDate"::DATE), 'YYYY-MM-DD') AS last_sale_date,
                        COUNT(DISTINCT DATE_TRUNC('month', m."InvoiceDate"::DATE)) AS active_months,
                        ROUND(
                            SUM(m."UnitPrice" * m."Quantity")::DECIMAL 
                            / NULLIF(COUNT(DISTINCT DATE_TRUNC('month', m."InvoiceDate"::DATE)), 0),
                            2
                        ) AS avg_monthly_revenue,
                        ROUND(
                            COALESCE(SUM(ABS(m."Quantity" * m."UnitPrice")) FILTER (WHERE m."Quantity" < 0), 0)::DECIMAL
                            / NULLIF(COUNT(DISTINCT m."StockCode"), 0)::DECIMAL,
                            2
                        ) AS avg_return_per_order,
                        MAX(m."InvoiceDate"::DATE) - MIN(m."InvoiceDate"::DATE) AS active_days
                    FROM modify m
                    GROUP BY m."Country"
                    ORDER BY ROUND(SUM(m."UnitPrice" * m."Quantity")::DECIMAL, 2) DESC;
                """)
            )
        print("✅ Витрина 'sale_analysis_by_country' успешно создана.")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании sale_analysis_by_country: {e}")
        return None


def main():
    print("=== Запуск ETL-процесса: построение аналитических витрин ===")
    engine = connect_to_db()
    if engine is None:
        print("❌ Не удалось подключиться к базе данных.")
        exit(1)

    steps = [
        ("Сводка по странам", analysis_of_sells_of_country),
        ("Динамика по месяцам", sale_monthly_trend),
        ("Товарная аналитика", product_sale_analysis),
        ("RFM-сегментация", customer_rfm_segments),
        ("Анализ возвратов", return_analysis),
    ]

    for name, func in steps:
        res = func(engine)
        if res is None:
            print(f"❌ Ошибка на этапе: {name}")
            exit(1)

    print("🎉 Все аналитические витрины успешно построены!")


if __name__ == "__main__":
    main()
