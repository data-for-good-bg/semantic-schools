This folder contains analysis of the ethnic population correlation with matura results.

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

#Correl roma population 

```sparql
PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX : <http://edu.ontotext.com/resource/ontology/>
BASE <http://edu.ontotext.com/resource/>
PREFIX ethnic_group: <http://edu.ontotext.com/resource/ethnic_group/>
PREFIX subject: <http://edu.ontotext.com/resource/subject/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select ?place_lab ?population ?roma_pop ?roma_ratio ?avg_dzi
where {
    bind(?roma_pop/?population as ?roma_ratio)
    ?place rdfs:label ?place_lab .
    filter(lang(?place_lab)="bg")
    {
        select ?place (sum(?any) as ?population)  (sum(?roma) as ?roma_pop) {
            ?o_eth qb:dataSet <cube/nsi_ethnicity/2011> ;
                   :quantity_people ?any ;
                   :place ?place ;
                   :ethnic_group ?eg ;
                   .
            bind(if(sameterm(?eg,ethnic_group:roma),?any,0) as ?roma)
        } group by ?place 
    }
    {
        select ?place (avg(?grade) as ?avg_dzi) {
            ?o_dzi qb:dataSet <cube/dzi/2020> ;
                   :grade_6 ?grade ;
#                   :subject subject:nmb_1 
                   :school ?school ;
                   .
            ?school :place ?place .
        } group by ?place 
    }
}
```

Rank schools by number of observations

```sparql 
select ?school ?school_label (COUNT(?obs) AS ?num_obs) 
where { 
	?obs a qb:Observation .
	?obs :school ?school .
	?school rdfs:label ?school_label
} group by ?school ?school_label order by desc (?num_obs)
```

Rank schools by percentile on all subject all years

```sparql
select  
?school ?school_label (avg(?perc) as ?avg_perc) (sum(?kids) as ?KIDS)
where { 
	?o :rank_percentile ?perc ; :school ?school ; :subject ?subj ; :quantity_people ?kids .
    ?school rdfs:label ?school_label .
} 
group by ?school ?school_label order by desc(?avg_grade) 
```

Rank schools by percentile on 1 subject all years

```sparql
PREFIX : <http://edu.ontotext.com/resource/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX subject: <http://edu.ontotext.com/resource/subject/>
select  
?school ?school_label (avg(?perc) as ?avg_perc) (sum(?kids) as ?KIDS)
where { 
    bind(subject:nmb_35 as ?subj)
	?o :rank_percentile ?perc ; :school ?school ; :subject ?subj ; :quantity_people ?kids .
    ?school rdfs:label ?school_label . 
} 
group by ?school ?school_label order by desc(?avg_perc) 
```

# Debug

```sparql
PREFIX : <http://edu.ontotext.com/resource/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX place: <http://edu.ontotext.com/resource/place/>
PREFIX subject: <http://edu.ontotext.com/resource/subject/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
select * where {
#    values ?mun {
#        place:Q2401780 #dupnica
#    	place:Q628050  #blagoevgrad  
#    }
?s a :School; :place/geo:sfWithin ?mun ; rdfs:label ?school_name .
  
    ?mun rdfs:label ?mun_label ; 
         geo:sfWithin place:Q804311 ;
    .
    
       ?o2 :school ?s ;
       :grade_level 12 ;
       :subject subject:nmb_1 ;
       :date "2021-05-19"^^xsd:date ;
       :eval_score ?score ;
       :quantity_people ?n_kids ;
    .
    filter(lang(?mun_label)="bg")
} 
```

## Haskovo School QCs

- attendance NVO MAT vs BG
- timeline avg percentile per school
- scatter plot schools compare attendance/score
 - correlation (small schools <20 attendance)




