# SPARQL Queries 

Per subject and oblast count old teachers compared to all the teachers 
Query showing merging of 2 datasets with 2-step aggregation 

```sparql
select ?region ?region_label ?subj ?subj_label ?total_teachers (sum(?old_teachers) as ?OLD_TEACHERS) {

    {select ?region ?subj (sum(?n_teachers) as ?total_teachers) where { 
  
    bind(subject:nmb_1 as ?subj)
	?o a qb:Observation ; 
    	qb:dataSet <cube/teachers_school_subject/2020-09-15>  ; 
     	:subject ?subj ; 
      	:school ?school ; 
        :quantity_people ?n_teachers ;
   .
    ?school geo:sfWithin+ ?region . 
            ?region a :Region .
	} group by ?region ?subj}
    
    values ?ds {
        <cube/teachers_by_age_region/2020-09-15_F>
        <cube/teachers_by_age_region/2020-09-15_M>
    }
	?o2 a qb:Observation ; 
    		qb:dataSet ?ds  ; 
     		:subject ?subj ; 
      		:place ?region ; 
        	:quantity_people ?old_teachers ;
   	.
    ?region  rdfs:label ?region_label .
    ?subj skos:prefLabel ?subj_label . 
    filter(lang(?region_label)="bg")
} group by ?region ?region_label ?subj ?subj_label ?total_teachers 
```

Death compare 2019-2020

```sparql
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX : <http://edu.ontotext.com/resource/ontology/>
BASE <http://edu.ontotext.com/resource/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select ?place ?place_label (sum(?death_20) as ?total_20) (sum(?death_19) as ?total_19) ((?total_20/?total_19) as ?ratio) where { 
	?s_19 qb:dataSet <cube/nsi_deaths/data> ; :year "2019"^^xsd:gYear ; :quantity_people ?death_19  ; :place ?place ; :week_number ?week .
	?s_20 qb:dataSet <cube/nsi_deaths/data> ; :year "2020"^^xsd:gYear ; :quantity_people ?death_20  ; :place ?place ; :week_number ?week .
    ?place rdfs:label ?place_label .
    filter(lang(?place_label)="bg")
} group by ?place ?place_label order by desc(?ratio)
```

Geo Demo - DZI mean by subj and by jurisdiction on YasGUY

[YasGUY link to query](https://api.triplydb.com/s/DkUQTW-ut)

```sparql
PREFIX : <http://edu.ontotext.com/resource/ontology/>
PREFIX school: <http://edu.ontotext.com/resource/school/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX subject: <http://edu.ontotext.com/resource/subject/>

select ?subjectLabel (concat(?placeLab,"\n",?subjectLabel,"\n Средно: ",(str(avg(?grade))),"\n Общо Ученици: ",(str(sum(?num_students)))) as ?placeLabel) (concat("ranbow,",str((avg(?grade)-1)/5)) as ?placeColor) ?place where { 
	bind(subject:nmb_1 as ?subj) 
    ?p a :Region ; rdfs:label ?placeLab ; :hasShape/geo:asWKT ?place .
    
    ?o :grade_6 ?grade ; :school/geo:sfWithin+ ?p ; :subject ?subj ; :quantity_people ?num_students ; :date ?date .
    
    ?subj skos:prefLabel ?subjectLabel .  
    filter(lang(?placeLab)="bg")
#    filter(year(?date) = 2019)
    filter(lang(?subjectLabel)="bg")
} group by ?placeLab ?subjectLabel ?place 
```

BEL DZI Mapped with Geosparql Nearby

[YasGUY link to query](https://api.triplydb.com/s/xMWAb-JVA)

```sparql
PREFIX omgeo: <http://www.ontotext.com/owlim/geo#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX : <http://edu.ontotext.com/resource/ontology/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX subject: <http://edu.ontotext.com/resource/subject/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT * WHERE {
 bind(xsd:double("42.6799077") as ?my_lat) #MY LATITUDE
 bind(xsd:double("23.3628094") as ?my_lon) #MY LONGITUDE
 ?s a :School ; :hasPoint ?point ; rdfs:label ?schoolName .
 ?point omgeo:nearby(?my_lat ?my_lon "3km") ; geo:asWKT ?school. # DISTANCE FROM ME
    
 ?obs :school ?s ; :rank_percentile ?percentile ; :grade_6 ?grade_dzi ; :date ?date ; :subject subject:nmb_1 .
 
 bind(concat(?schoolName," БЕЛ:",?grade_dzi) as ?schoolLabel)
 bind(concat("warm,",str(?percentile/100)) as ?schoolColor)
 filter(year(?date) = 2020)
    
} order by desc(?percentile) 
```

#ROMA villages

https://api.triplydb.com/s/6zJ44Fxc0

#Correl roma population / 