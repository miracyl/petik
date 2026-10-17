CREATE OR REPLACE FUNCTION customer_rfm_segments_report(
    p_country TEXT DEFAULT NULL,
    p_segment TEXT DEFAULT NUll,
    p_customer_id INTEGER DEFAULT NUll,
    p_min_monetary NUMERIC DEFAULT NUll,
    p_min_frequency BIGINT DEFAULT NULL,
    p_max_recency NUMERIC DEFAULT NUll,
    p_order_by TEXT DEFAULT NUll,
    p_sort_order TEXT DEFAULT NUll,
    p_limit INTEGER DEFAULT NUll
)
RETURNS TABLE (
    country TEXT,
    customer_id INTEGER,
    monetary NUMERIC,
    frequency BIGINT,
    recency NUMERIC,
    monetary_score INTEGER,
    frequency_score INTEGER,
    recency_score INTEGER,
    segment TEXT
)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
       v_order_by TEXT;
       v_sort_order TEXT;
BEGIN
    v_order_by := COALESCE(p_order_by, 'monetary');
    v_sort_order := CASE WHEN COALESCE(p_sort_order, 'ASC') = 'ASC' THEN 'ASC' ELSE 'DESC' END;
    RETURN QUERY EXECUTE format( $f$
        SELECT *
        FROM customer_rfm_segments
        WHERE
            ($1 IS NULL OR country = $1)
            AND ($2 IS NULL OR segment = $2)
            AND ($3 IS NULL OR customer_id = $3)
            AND ($4 IS NULL OR monetary >= $4)
            AND ($5 IS NULL OR frequency >= $5)
            AND ($6 IS NULL OR recency <= $6)
        ORDER BY %I %s NULLS LAST
        LIMIT $7
    $f$, v_order_by, v_sort_order
    )
    USING
        p_country,
        p_segment,
        p_customer_id,
        p_min_monetary,
        p_min_frequency,
        p_max_recency,
        p_limit;
END;
$$;