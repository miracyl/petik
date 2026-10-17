CREATE OR REPLACE FUNCTION sale_monthly_trend_report(
    p_country TEXT DEFAULT NULL,
    p_year_month DATE DEFAULT NULL,
    p_min_revenue NUMERIC DEFAULT NULL,
    p_min_growth_percent NUMERIC DEFAULT NULL,
    p_order_by TEXT DEFAULT NULL,
    p_sort_order TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT NULL
)
RETURNS TABLE (
    country TEXT,
    year_month DATE,
    monthly_revenue NUMERIC,
    monthly_orders BIGINT,
    adoption_of_new_clients NUMERIC,
    prev_month_revenue NUMERIC,
    revenue_growth_percent NUMERIC
)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
       v_order_by TEXT;
       v_sort_order TEXT;
BEGIN
    v_order_by := COALESCE(p_order_by, 'monthly_revenue');
    v_sort_order := CASE WHEN UPPER(TRIM(COALESCE(p_sort_order, ''))) = 'ASC' THEN 'ASC' ELSE 'DESC' END;

    RETURN QUERY EXECUTE format($f$
        SELECT *
        FROM sale_monthly_trend
        WHERE
            ($1 IS NULL  OR country = $1)
            AND ($2 IS NULL  OR year_month = $2)
            AND ($3 IS NULL  OR monthly_revenue >= $3)
            AND ($4 IS NULL  OR revenue_growth_percent >= $4)
        ORDER BY %I %s NULLS LAST
        LIMIT $5
    $f$,
    v_order_by, v_sort_order
    )
    USING
        p_country,
        p_year_month,
        p_min_revenue,
        p_min_growth_percent,
        p_limit;
END;
$$;