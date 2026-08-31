CREATE OR REPLACE FUNCTION sale_analysis_by_country_report(

)
RETURNS TABLE (
    Country
) AS  $$
BEGIN
    RETURN QUERY
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
    WHERE 
	GROUP BY m."Country"
	ORDER BY ROUND(SUM(m."UnitPrice" * m."Quantity")::DECIMAL, 2) DESC
 