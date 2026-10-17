CREATE OR REPLACE FUNCTION product_sale_analysis_report(
    p_country TEXT DEFAULT NULL,
    p_min_revenue NUMERIC DEFAULT NULL,
    p_min_sold NUMERIC DEFAULT NULL,
    p_min_unique_buyers BIGINT DEFAULT NULL,
    p_min_share_percent NUMERIC DEFAULT NULL,
    p_max_returns NUMERIC DEFAULT NULL,
    p_order_by TEXT DEFAULT NULL,
    p_sort_order TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT NULL
)
RETURNS TABLE (
    country TEXT,
    stock_code TEXT,
    description TEXT,
    total_quantity_sold NUMERIC,
    total_quantity_return NUMERIC,
    total_revenue NUMERIC,
    unique_buyers BIGINT,
    revenue_share_in_country NUMERIC,
    avg_price NUMERIC
)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    v_order_by TEXT;
    v_sort_order TEXT;
BEGIN
    v_order_by := COALESCE(p_order_by, 'total_revenue');
    v_sort_order := CASE WHEN UPPER(COALESCE(p_sort_order, 'DESC')) = 'ASC' THEN 'ASC' ELSE 'DESC' END;

    RETURN QUERY EXECUTE format($f$
        SELECT *
        FROM product_sale_analysis
        WHERE
            ($1 IS NULL OR country = $1)
            AND ($2 IS NULL OR total_revenue >= $2)
            AND ($3 IS NULL OR total_quantity_sold >= $3)
            AND ($4 IS NULL OR unique_buyers >= $4)
            AND ($5 IS NULL OR revenue_share_in_country >= $5)
            AND ($6 IS NULL OR total_quantity_return <= $6)
        ORDER BY %I %s NULLS LAST
        LIMIT $7
    $f$, v_order_by, v_sort_order)
    USING
        p_country,
        p_min_revenue,
        p_min_sold,
        p_min_unique_buyers,
        p_min_share_percent,
        p_max_returns,
        p_limit;
END;
$$;