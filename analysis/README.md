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