SET @edition = "BFZ";
SELECT * FROM (
(SELECT *
FROM (
	SELECT * FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
) as t1
RIGHT JOIN (
	SELECT 
	   REPLACE(name,'´', '\'') as name_replaced, 
	   id as cr_id, 
		LEFT(REPLACE(name,'´', '\''), LOCATE(' ',REPLACE(name,'´', '\'')) - 1) as strip_name,
		LOCATE('Extended', REPLACE(name,'´', '\'')) as located
	FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %" AND name not like "Emblem - %"
) as t2
ON t1.name = t2.name_replaced)

UNION ALL

(SELECT *
FROM (
	SELECT * FROM sdk_cards WHERE NOT (`layout`="double-faced" and mana_cost is null and `type` !="Land") AND (`set`=@edition)
) as t1
LEFT JOIN (
	SELECT 
	   REPLACE(name,'´', '\'') as name_replaced, 
		id as cr_id, 
		LEFT(REPLACE(name,'´', '\''),LOCATE(' ',REPLACE(name,'´', '\'')) - 1) as strip_name, 
		LOCATE('Extended', REPLACE(name,'´', '\'')) as located
	FROM cards WHERE edition_id=@edition AND id not like "tokens%" AND name not like "Token - %" AND name not like "Emblem - %"
) as t2
ON t1.name = t2.name_replaced)
) as mismatch WHERE (`name` is  null or `name_replaced` is  null)
ORDER BY `strip_name`, `located`;