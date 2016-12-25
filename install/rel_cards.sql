CREATE TABLE `rel_cards` (
  `id_cr` varchar(50) DEFAULT NULL,
  `id_sdk` varchar(50) DEFAULT NULL,
  UNIQUE KEY `id_cr` (`id_cr`),
  UNIQUE KEY `id_sdk` (`id_sdk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='Transition table for edition IDs between SDK and CR.';
