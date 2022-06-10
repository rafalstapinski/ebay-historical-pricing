# ebay historical prices scraper

**tl;dr** this finds the prices of sold items on ebay

i made this because i want to track the prices of film cameras over time. its pretty simple
1. it searches for items on ebay, filtering by "sold" and "used" (though the particular url format can be changed to exclude the "used" category)
2. collects the name, price, date, and a couple other things
3. persists them idempotently in a postgres table

its not very comprehensive nor robust but should give a good enough set of data over time 🤷

## how to run

### set a couple of env variables
```
PYTHONPATH=.
ENV=dev
DATABASE_URL=postgres://user:pass@host/db
```


### create two tables in your postgres db
```sql
CREATE TABLE item (
    id SERIAL PRIMARY KEY,
    name text NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    deleted_at timestamp without time zone
);
CREATE UNIQUE INDEX item_pkey ON item(id int4_ops);
```
```sql
CREATE TABLE sale (
    id SERIAL PRIMARY KEY,
    item_id bigint NOT NULL REFERENCES item(id),
    listing_price integer NOT NULL,
    sold_at date NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    listing_name text NOT NULL,
    listing_url text NOT NULL UNIQUE,
    listing_image text NOT NULL
);
CREATE UNIQUE INDEX sale_pkey ON sale(id int4_ops);
CREATE UNIQUE INDEX sale_listing_url_key ON sale(listing_url text_ops);
```


### specify the items you want to track
populate some items in the `item` table, specified by the `name` column


### install dependencies
```bash
poetry install
```


### run the script daily
```
poetry run python ehp/app.py
```
