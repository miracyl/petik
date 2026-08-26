import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy import text

def connect_to_db():
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
		print(f"Connection is ready IN ELT")
		return engine
	except Exception as e:
		print(f"Connection is failed IN ELT: {e}")
		return None

def return_analysis(engine):
	print(f"Starting of creating table: return_analysis")
	try:
		with engine.connect() as conn:
			conn.execute(
				text(
					"""DROP TABLE IF EXISTS return_analysis"""
				)
			)
			conn.execute(
				text(
					"""
						CREATE TABLE return_analysis AS
						WITH modify AS (
							SELECT 
								s.*
						FROM sales s
						)
						SELECT 
							s."Country",
							s."StockCode",
							ROUND(AVG(s."UnitPrice")::DECIMAL,2) AS avg_unit_price,
							SUM(s."Quantity") FILTER (WHERE s."Quantity" > 0) AS total_sold,
							ABS(COALESCE(SUM(s."Quantity") FILTER (WHERE s."Quantity" < 0),0)) AS total_returns,
							ABS(
								ROUND(
									COALESCE(SUM(s."Quantity") FILTER (WHERE s."Quantity" < 0)::DECIMAL, 0) 
									/ NULLIF(SUM(s."Quantity") FILTER (WHERE s."Quantity" > 0)::DECIMAL, 0) * 100.0,
								2)
							) AS return_rate_percent,
							ABS(ROUND(
								COALESCE(SUM(s."Quantity" * s."UnitPrice") FILTER (WHERE s."Quantity" < 0)::DECIMAL,0),
							2)) AS revenue_lost_from_returns
						FROM sales s
						WHERE s."CustomerID" IS NOT NULL
						GROUP BY s."Country", s."StockCode"
						ORDER BY return_rate_percent DESC NULLS LAST
					"""
				)
			)
			conn.commit()
			return True
	except Exception as e:
		print(f"Table return_analysis is not executed: {e}")
		return None

def customer_rfm_segments(engine):
	print(f"Starting of crearing table: customer_rfm_segments")
	try:
		with engine.connect() as conn:
			conn.execute(
				text(
					"""DROP TABLE IF EXISTS customer_rfm_segments"""
				)
			)
			conn.execute(
				text(
					"""
						CREATE TABLE customer_rfm_segments AS
						WITH mod AS (
							SELECT 
								s."Country",
								s."CustomerID",
								ROUND(SUM(s."UnitPrice" * s."Quantity")::DECIMAL,2) AS monetary,
								COUNT(DISTINCT s."InvoiceNo") AS frequency,
								EXTRACT(DAY FROM NOW() - MAX(s."InvoiceDate"::TIMESTAMP)) AS recency
							FROM sales s 
							GROUP BY s."CustomerID", s."Country"
						),
						modi AS (
							SELECT
								m.*,
								NTILE(3) OVER(PARTITION BY m."Country" ORDER BY monetary DESC) AS monetary_score,
								NTILE(3) OVER(PARTITION BY m."Country" ORDER BY frequency DESC) AS frequency_score,
								NTILE(3) OVER(PARTITION BY m."Country" ORDER BY recency ASC) AS recency_score
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
						ORDER BY m."Country" ASC ,m."CustomerID" ASC;
					"""
				)
			)
			conn.commit()
			return True
	except Exception as e:
		print(f"Table customer_rfm_segments is not executed: {e}")
		return None

def product_sale_analysis(engine):
	print(f"Starting of creating table: product_sale_analysis")
	try:
		with engine.connect() as conn:
			conn.execute(
				text(
					"DROP TABLE IF EXISTS product_sale_analysis"
				)
			)
			conn.execute(
				text(
					"""
						CREATE TABLE product_sale_analysis AS
						WITH modify AS (						
								SELECT 
										s.*,
										SUM(s."Quantity" * s."UnitPrice") OVER(PARTITION BY s."Country") AS country_revenue
								FROM sales s
						)
						SELECT
								m."Country",
								m."StockCode",
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
						ORDER BY total_revenue DESC;
					"""
				)
			)
			conn.commit()
			print("Table product_sale_analysis was created")
			return True
	except Exception as e:
		print(f"Table product_sale_analysis is not executed: {e}")
		return None


def sale_monthly_trend(engine):
	print(f"Starting of creating table: sale_monthly_trend")
	try:
		with engine.connect() as conn:
			conn.execute(
				text(
					"DROP TABLE IF EXISTS sale_monthly_trend"
				)
			)
			conn.execute(
				text(
					"""
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
										TO_CHAR(DATE_TRUNC('month', m."InvoiceDate"::DATE), 'YYYY-MM') AS year_month,
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
										(monthly_revenue - LAG(monthly_revenue, 1, 0) OVER (PARTITION BY country ORDER BY year_month))::DECIMAL
										/ NULLIF(LAG(monthly_revenue, 1, 0) OVER (PARTITION BY country ORDER BY year_month), 0)::DECIMAL * 100.0,
										2
								) AS revenue_growth_percent
						FROM monthly_stats ms;
					"""
				)
			)
			conn.commit()
			print("Table sale_monthly_trend was created")
			return True
	except Exception as e:
		print(f"Table sale_monthly_trend is not executed: {e}")
		return None

def analysis_of_sells_of_country(engine):
	print("Starting of creating table: analys of sells in countrys")
	try:
		with engine.connect() as conn:
			conn.execute(
				text(
					"""
						DROP TABLE IF EXISTS sale_analysis_by_country
					"""
				)
			)
			conn.execute(
				text(
					"""
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
								m."Country",
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
					"""
				)
			)
			conn.commit()
			print("Table analysis_of_sells_of_country was created")
			return True
	except Exception as e:
		print(f"Table sale_analysis_by_country is not executed: {e}")
		return None


def main():
	print(f"Запуск третьей части!")
	engine = connect_to_db()
	res = analysis_of_sells_of_country(engine)
	if res == None :
		print(f"Problem with function: analysis_of_sells_of_country")
	res = sale_monthly_trend(engine)
	if res == None :
		print(f"Problem with function: sale_monthly_trend")
	res = product_sale_analysis(engine)
	if res == None :
		print(f"Problem with function: product_sale_analysis")
	res = customer_rfm_segments(engine)
	if res == None :
		print(f"Problem with function: customer_rfm_segments")
	res = return_analysis(engine)
	if res == None :
		print(f"Problem with function: return_analysis")

if __name__ == "__main__":
	main()
