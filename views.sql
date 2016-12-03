-- This file is as a history of created views. When exporting from e.g. adminer,
-- the views are translated into algorithms.

DROP VIEW IF EXISTS card_details;
CREATE VIEW card_details(id, name, edition_id, edition_name, manacost, buy, sell, buy_foil, sell_foil, md5)
AS (
SELECT cards.id, cards.name, cards.edition_id, editions.name as edition_name, cards.manacost, costs.buy, costs.sell, costs.buy_foil, costs.sell_foil, cards.md5
FROM cards
LEFT JOIN costs ON cards.id = costs.card_id
LEFT JOIN editions ON cards.edition_id = editions.id
);
