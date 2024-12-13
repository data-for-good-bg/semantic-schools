select e."year", r."name" as region, m."name" as mun, p."name" as place, es.school_id, es.subject, es.people, es.score
from examination e
        inner join examination_score es on e.id = es.examination_id
        inner join school s on s.id = es.school_id
        inner join place p on s.place_id = p.id
        inner join municipality m on p.municipality_id = m.id
        inner join region r on m.region_id = r.id
where e."type" = 'ДЗИ'
--   and e."year" = 2017 and s.id = '400036'
order by e."year", region, mun, place, school_id, subject
