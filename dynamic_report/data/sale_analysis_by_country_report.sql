CREATE OR REPLACE FUNCTION sale_analysis_by_country_report(
       p_country TEXT DEFAULT NULL,
       p_min_active_month INTEGER DEFAULT NULL,
       p_max_active_month INTEGER DEFAULT NULL,
       p_first_sale_from DATE DEFAULT NULL,
       p_first_sale_to DATE DEFAULT NULL,
       p_last_sale_from DATE DEFAULT NULL,
       p_last_sale_to DATE DEFAULT NULL,
       p_min_revenue NUMERIC DEFAULT NULL,
       p_min_operations NUMERIC DEFAULT NULL,
       p_min_unique_clients BIGINT DEFAULT NULL,
       p_max_return_percent NUMERIC DEFAULT NULL,
       p_order_by TEXT DEFAULT 'total_revenue',
       p_sort_order TEXT DEFAULT 'ASC',
       p_limit INTEGER DEFAULT NULL

)
RETURNS TABLE (
    country                  TEXT,
    total_operations            BIGINT,
    total_revenue               NUMERIC,
    avg_price                   NUMERIC,
    unique_clients              BIGINT,
    unique_products             BIGINT,
    return_orders               BIGINT,
    return_orders_percent       NUMERIC,
    returns_amount              NUMERIC,
    returns_percent_of_revenue  NUMERIC,
    avg_order_value             NUMERIC,
    avg_items_per_order         NUMERIC,
    revenue_share_percent       NUMERIC,
    first_sale_date             TEXT,
    last_sale_date              TEXT,
    active_months               BIGINT,
    avg_monthly_revenue         NUMERIC,
    avg_return_per_order        NUMERIC,
    active_days                 INTEGER
)
LANGUAGE plpgsql
STABLE
AS  $$
DECLARE
       v_order_by TEXT;
       v_sort_order TEXT;
BEGIN
    v_order_by := COALESCE(p_order_by, 'total_revenue');
    v_sort_order := CASE WHEN COALESCE(p_sort_order, 'ASC') = 'ASC' THEN 'ASC' ELSE 'DESC' END;
    RETURN QUERY EXECUTE format($f$
        SELECT
            *
        FROM sale_analysis_by_country
        WHERE
            ($1 IS NULL OR country = $1)
            AND ($2 IS NULL OR active_months >= $2)
            AND ($3 IS NULL OR active_months <= $3)
            AND ($4 IS NULL OR first_sale_date::DATE >= $4)
            AND ($5 IS NULL OR first_sale_date::DATE <= $5)
            AND ($6 IS NULL OR last_sale_date::DATE >= $6)
            AND ($7 IS NULL OR last_sale_date::DATE <= $7)
            AND ($8 IS NULL OR total_revenue >= $8)
            AND ($9 IS NULL OR total_operations >= $9)
            AND ($10 IS NULL OR unique_clients >= $10)
            AND ($11 IS NULL OR returns_percent_of_revenue <= $11)
            ORDER BY %I %s NULLS LAST
            LIMIT $12
        $f$, v_order_by, v_sort_order)
        USING
            p_country,
            p_min_active_month,
            p_max_active_month,
            p_first_sale_from,
            p_first_sale_to,
            p_last_sale_from,
            p_last_sale_to,
            p_min_revenue,
            p_min_operations,
            p_min_unique_clients,
            p_max_return_percent,
            p_limit;
END;
$$;

 