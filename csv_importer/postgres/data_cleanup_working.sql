select es.school_id, s."name", count(distinct es.examination_id) as ex
from examination_score es 
inner join school s on s.id = es.school_id 
where examination_id like 'dzi%'
group by es.school_id, s."name"
--having count(distinct es.examination_id) < 8
order by 3 asc

select * 
from examination_score es 
where es.examination_id = 'dzi-12-2024'

select distinct subject 
from examination_score


select count(distinct es.examination_id)
from examination_score es 
where examination_id like 'dzi%'

select count(distinct school_id) from examination_score es 
where examination_id = 'dzi-12-2020'

select distinct school_id 
from examination_score es 
where examination_id = 'dzi-12-2020'
order by school_id 


select distinct examination_id
from examination_score es 
where es.school_id like '%.%'

delete from examination_score es
where es.examination_id = 'dzi-12-2021'

select distinct subject
from examination_score es 
where es.examination_id like 'dzi%'
order by 1

select count(*) 
from examination_score es 

select * 
from examination e 
where  e."type" = 'ДЗИ'


select count(distinct id) 
from school s 
where s.id like '%.%'

delete from school 
where id like '%.%'

select count(id), "name", place_id
from school 
group by "name", place_id 
having count(id) >= 2

select * 
from school
where 
(place_id = 324 and "name" = 'Основно училище "Христо Ботев"')
or (place_id = 114 and "name" = 'Професионална гимназия')
or (place_id = 596 and "name" = 'Основно училище "Христо Смирненски"')
or (place_id = 324 and "name" = 'Основно училище " Христо Ботев"')

--SELECT ?item ?itemLabel WHERE {
--  ?item wdt:P31 wd:Q3914;
--     wdt:P9034 "200223"    
--  SERVICE wikibase:label { bd:serviceParam wikibase:language "bg". }
--}