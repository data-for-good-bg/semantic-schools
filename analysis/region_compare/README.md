# Cross municipalities comparison

## Mean DZI scores per municipality compared with municipality containing region capital

```sparql
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX subject: <https://schools.ontotext.com/data/resource/subject/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select * where {
	?cap_mun a :Municipality ;
          geo:sfWithin ?region ;
    	  rdfs:label ?cap_mun_label .
    ?cap_city :capital_of ?region ;
  			 geo:sfWithin ?cap_mun .
    ?oth_mun a :Municipality ;
          geo:sfWithin ?region ;
         rdfs:label ?oth_mun_label ;
    .
    ?region rdfs:label ?region_label .
    filter(lang(?cap_mun_label)="bg")
    filter(lang(?oth_mun_label)="bg")
    filter(lang(?region_label)="bg")
    filter(!sameterm(?oth_mun,?cap_mun))

    ?o :place ?cap_mun ;
       :grade_level 12 ;
       :subject subject:nmb_1 ;
       :date ?date ;
       :eval_score ?avg_grade_cap ;
       :quantity_people ?n_kids_cap ;
    .

    ?o2 :place ?oth_mun ;
       :grade_level 12 ;
       :subject subject:nmb_1 ;
       :date ?date ;
       :eval_score ?avg_grade_oth ;
       :quantity_people ?n_kids_oth ;
    .
    filter(?avg_grade_oth>?avg_grade_cap) # filter ony those with higher scores
} order by ?region_label ?oth_mun_label desc(?date)
```

## Mean DZI scores compared between region and capital municipality

```sparql
PREFIX : <https://schools.ontotext.com/data/resource/ontology/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX subject: <https://schools.ontotext.com/data/resource/subject/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select * where {

    {select ?region ?date (sum(?points) as ?points_oth) (sum(?n_kids_oth) as ?sum_kids_oth) (?points_oth/?sum_kids_oth as ?avg_grade_oth) {

    ?oth_mun a :Municipality ;
          geo:sfWithin ?region ;
    .
    ?cap_city :capital_of ?region .
    filter not exists {?cap_city geo:sfWithin ?oth_mun}
       ?o_oth :place ?oth_mun ;
       :grade_level 12 ;
       :subject subject:nmb_1 ;
       :date ?date ;
       :eval_score ?avg_grade_oth_mun ;
       :quantity_people ?n_kids_oth ;
    .
    bind(?n_kids_oth*?avg_grade_oth_mun as ?points)
    } group by ?region ?date }

	?cap_mun a :Municipality ;
          geo:sfWithin ?region ;
    	  rdfs:label ?cap_mun_label .
    ?cap_city :capital_of ?region ;
  			 geo:sfWithin ?cap_mun .
    ?region rdfs:label ?region_label .
    filter(lang(?cap_mun_label)="bg")
    filter(lang(?region_label)="bg")

    ?o :place ?cap_mun ;
       :grade_level 12 ;
       :subject subject:nmb_1 ;
       :date ?date ;
       :eval_score ?avg_grade_mun ;
       :quantity_people ?n_kids_mun ;
    .

    ?o2 :place ?region ;
       :grade_level 12 ;
       :subject subject:nmb_1 ;
       :date ?date ;
       :eval_score ?avg_grade_reg ;
       :quantity_people ?n_kids_reg ;
    .
} order by ?region_label ?oth_mun_label desc(?date)


```