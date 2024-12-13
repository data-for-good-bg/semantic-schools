Initially the DZI-streamlit dashboard works with CSV extract from the postgres
DB.

This CSV file can be created by invoking this:

```bash
echo "year,region,mun,place,school_id,subject,people,score" > dzi-data.csv \
    && psql -h crunch.data-for-good.bg -U eddata-reader -d eddata -t -A -F',' -c "$(cat ./extract_csv.sql)" >> dzi-data.csv
```
