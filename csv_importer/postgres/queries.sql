select distinct subject 
from examination_score es inner join examination e on e.id = es.examination_id and e."type" = 'ДЗИ' 
order by 1

select distinct examination_id 
from examination_score es 
where es.examination_id like 'nvo%'
order by examination_id


select distinct es.max_possible_score 
from examination_score es 

select * 
from examination_score es inner join examination e on e.id = es.examination_id and e."type" = 'ДЗИ'
where subject = '2ДЗИ'
order by 1 

select * 
from examination_score es inner join examination e on e.id = es.examination_id and e."type" = 'ДЗИ'
where es.school_id like '1000002%' 
order by 1

select concat('Област ', r."name") as "region" , p."name" , s.id , s."name" , e."year", es.subject, es.people, es.score 
from examination_score es 
	inner join examination e on es.examination_id = e.id
	inner join school s on es.school_id = s.id 
	inner join place p on s.place_id = p.id 
	inner join municipality m on p.municipality_id = m.id 
	inner join region r on m.region_id = r.id 
where
	e."type" = 'ДЗИ'
	and es.subject not in ('ОБЩО', '2ДЗИ')
order by "region" , p."name" , s.id , s."name" , e."year"


select province, town, school_wiki_id, school, "year", sub_group, people as tot_pup, score as average_grade 
from (
	select concat('Област ', r."name") as province , p."name" as town, s.id as school_wiki_id , s."name" as school , e."year" as "year", 'БЕЛ' as sub_group, es.people as people, es.score as score
	from examination_score es 
		inner join examination e on es.examination_id = e.id
		inner join school s on es.school_id = s.id 
		inner join place p on s.place_id = p.id 
		inner join municipality m on p.municipality_id = m.id 
		inner join region r on m.region_id = r.id 
	where
		e."type" = 'ДЗИ'
		and es.subject in ('БЕЛ')
) result	
union
select province, town, school_wiki_id, school, "year", sub_group, sum(people) as tot_pup, sum(people*score)/sum(people) as average_grade 
from (
	select concat('Област ', r."name") as province , p."name" as town, s.id as school_wiki_id , s."name" as school , e."year" as "year", 'СТЕМ' as sub_group, es.people as people, es.score as score
	from examination_score es 
		inner join examination e on es.examination_id = e.id
		inner join school s on es.school_id = s.id 
		inner join place p on s.place_id = p.id 
		inner join municipality m on p.municipality_id = m.id 
		inner join region r on m.region_id = r.id 
	where
		e."type" = 'ДЗИ'
		and es.subject in ('БЗО', 'МАТ', 'ФА', 'ИНФ', 'ИТ', 'ХООС')
	) result
group by province, town, school_wiki_id, school, "year", sub_group
union
select province, town, school_wiki_id, school, "year", sub_group, sum(people) as tot_pup, sum(people*score)/sum(people) as average_grade 
from (
	select concat('Област ', r."name") as province , p."name" as town, s.id as school_wiki_id , s."name" as school , e."year" as "year", 'ДРУГИ' as sub_group, es.people as people, es.score as score
	from examination_score es 
		inner join examination e on es.examination_id = e.id
		inner join school s on es.school_id = s.id 
		inner join place p on s.place_id = p.id 
		inner join municipality m on p.municipality_id = m.id 
		inner join region r on m.region_id = r.id 
	where
		e."type" = 'ДЗИ'
		and es.subject not in ('ОБЩО', '2ДЗИ', 'БЕЛ', 'БЗО', 'МАТ', 'ФА', 'ИНФ', 'ИТ', 'ХООС')
) result
group by province, town, school_wiki_id, school, "year", sub_group
order by province, town, school_wiki_id, school, "year", sub_group

--r."name" , p."name" , s.id , s."name" , e."year"	
-- БЕЛ, 
-- БЗО, МАТ, ФА, ИНФ, ИТ, ХООС
