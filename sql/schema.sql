CREATE TABLE IF NOT EXISTS orders (
    order_id            INTEGER PRIMARY KEY,
    order_date          DATE NOT NULL,
    order_time          TIME NOT NULL,
    customer_segment    VARCHAR(50),
    order_value         NUMERIC(10, 2),
    cuisine_type        VARCHAR(50),
    delivery_time_mins  INTEGER,
    promo_code_used     BOOLEAN,
    is_reorder          BOOLEAN
);
