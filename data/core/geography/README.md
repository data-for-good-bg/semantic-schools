# Geography 

This folder contains the queries that generate the bulgarian administrative hierarchy and its geographical elements.

N.B that there is an unclear overlap between populated places and jurisdictions in Bulgaria. Large metropolitan areas such as Sofia Plovdiv and Varna are considered one City but are composed of Municipal Districts (`:District`). Moreover these districts sometimes contain also more than one places. This is why we differentiate between jurisdictions `:District` > `:Municipality` > `:Region` and the set of populate places `:Place`. Thus a feature, such as a school can be in both a `:Place` and the lowermost relevant jurisdiction.

## Generating Places and Jurisdictions 

All places are generated form wikidata using federated construct [queries](queries). Jurisdictions are based on these Wikidata types:

* wd:Q1906268 -> :Municipality
* wd:Q209824 -> :Region
* wd:Q7553685 -> :District

Places are all subtypes of wd:Q95993392 (City of Bulgaria and Village of Bulgaria)

**These queries will generate the entire geography from scratch every time. Thus corrections in Wikidata will always be reflected in the resulting graph.** 

## Point and polygons
Points and polygons are represented as WKT literals attached to objects of type `sf:Polygon` and `sf:Point`, containing respectively the centroid coordinates of each object and its shape.
### Points

Points correspond to the coordinates of a given feature. For large features such as regions they should represent the centroid of that feature. They are retrieved from wikidata using the P625 relation.

### Polygons 

Polygons are fetched from Open Street Maps using the identifiers stored as P402 in Wikidata. 
The list olf ids is exported to Open Refine using this [query](queries/osm-ids.rq)

As large areas can have very complex borders, the service at <http://polygons.openstreetmap.fr>.  will generate simplified polygons for easy display and retrieval

First this request generates the simplified polygons. **Use abundant throttling for good results**

`http://polygons.openstreetmap.fr/?id={{OSM_ID}}&x=0.004000&y=0.001000&z=0.001000&generate=Submit"` 

Next this request fetches them as WKT

```http://polygons.openstreetmap.fr/get_wkt.py?id={{OSM_ID}}&params=0.004000-0.001000-0.001000```