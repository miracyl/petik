CREATE OR REPLACE FUNCTION return_analysis_report(
    p_country TEXT DEFAULT NULL,
    p_stock_code TEXT DEFAULT NULL,
    p_min_sold NUMERIC DEFAULT NULL,
    p_min_returns NUMERIC DEFAULT NULL,
    p_min_return_rate NUMERIC DEFAULT NULL,
    p_min_revenue_lost NUMERIC DEFAULT NULL,
    p_order_by TEXT DEFAULT NULL,
    p_sort_order TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT NULL
)
RETURNS TABLE (
       country TEXT,
       stock_code TEXT,
       avg_unit_price NUMERIC,
       total_sold NUMERIC,
       total_returns NUMERIC,
       return_rate_percent NUMERIC,
       revenue_lost_from_returns NUMERIC
)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    v_order_by TEXT;
    v_sort_order TEXT;
BEGIN
    v_order_by = COALESCE(p_order_by , 'total_sold');
    v_sort_order = CASE WHEN COALESCE(p_sort_order , 'ASC') = 'ASC' THEN 'ASC' ELSE 'DESC' END;
    RETURN QUERY EXECUTE format(
        $f$
            SELECT *
            FROM return_analysis
            WHERE
                ($1 IS NULL OR country= $1)
                AND ($2 IS NULL OR stock_code = $2)
                AND ($3 IS NULL OR total_sold >= $3)
                AND ($4 IS NULL OR total_returns >= $4)
                AND ($5 IS NULL OR return_rate_percent >= $5)
                AND ($6 IS NULL OR revenue_lost_from_returns >= $6)
            ORDER BY %I %s NULLS LAST
            LIMIT $7
        $f$, v_order_by, v_sort_order
    )
    USING
        p_country,
        p_stock_code,
        p_min_sold,
        p_min_returns,
        p_min_return_rate,
        p_min_revenue_lost,
        p_limit;
END;
$$;