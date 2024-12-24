
# Schools in wikidata which cannot be imported

```sql
SELECT distinct ?school ?bgSchoolId WHERE {
  ?school wdt:P31 wd:Q3914;
          wdt:P9034 ?bgSchoolId.

  FILTER(?bgSchoolId in ('1100334', '200223', '200226', '2400287'))

  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "bg".
  }
}
order by ?bgSchoolId
```

# wd:Q106347916, 2400287 - its wdt:P131 is a _broken_ instance of "с. Хаджидимово"
# wd:Q106347089, 200226 - its wdt:P131 is 'Рудник', which is neither a city nor a village. It is ex-village and also neighbourhood in Burgas
# wd:Q106346062, 200223 - its wdt:P131 is 'Ветрен', which is neither a city nor a village. It is instance of "human settlement" (wdt:Q486972) which I don't know how to treat.
# wd:Q106348231, 1100334 - it does not have wdt:P131