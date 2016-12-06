-- --------------------------------------------------------
-- Hostitel:                     127.0.0.1
-- Verze serveru:                5.7.16-log - MySQL Community Server (GPL)
-- OS serveru:                   Win64
-- HeidiSQL Verze:               9.4.0.5125
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- Exportování struktury databáze pro
CREATE DATABASE IF NOT EXISTS `scrapknight` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `scrapknight`;

-- Exportování struktury pro tabulka scrapknight.cards
CREATE TABLE IF NOT EXISTS `cards` (
  `id` varchar(20) NOT NULL COMMENT 'ID karty',
  `name` varchar(100) DEFAULT NULL COMMENT 'Název karty',
  `edition_id` varchar(50) DEFAULT NULL COMMENT 'Edice karty (zdratka)',
  `manacost` varchar(10) DEFAULT NULL COMMENT 'Manacost (formát?)',
  `md5` varchar(50) DEFAULT NULL COMMENT 'MD5 hash jména karty',
  PRIMARY KEY (`id`),
  KEY `edition_id` (`edition_id`),
  KEY `name` (`name`),
  KEY `manacost` (`manacost`),
  KEY `md5` (`md5`),
  FULLTEXT KEY `name_fulltext` (`name`),
  CONSTRAINT `cards_ibfk_2` FOREIGN KEY (`edition_id`) REFERENCES `editions` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Seznam všech karet v databázi.';

-- Export dat nebyl vybrán.
-- Exportování struktury pro pohled scrapknight.card_details
-- Vytváření dočasné tabulky Pohledu pro omezení dopadu chyb
CREATE TABLE `card_details` (
	`id` VARCHAR(20) NOT NULL COMMENT 'ID karty' COLLATE 'utf8_general_ci',
	`name` VARCHAR(100) NULL COMMENT 'Název karty' COLLATE 'utf8_general_ci',
	`edition_id` VARCHAR(50) NULL COMMENT 'Edice karty (zdratka)' COLLATE 'utf8_general_ci',
	`edition_name` VARCHAR(50) NULL COMMENT 'Plný název edice' COLLATE 'utf8_general_ci',
	`manacost` VARCHAR(10) NULL COMMENT 'Manacost (formát?)' COLLATE 'utf8_general_ci',
	`buy` SMALLINT(5) UNSIGNED NULL,
	`sell` SMALLINT(5) UNSIGNED NULL,
	`buy_foil` SMALLINT(5) UNSIGNED NULL,
	`sell_foil` SMALLINT(5) UNSIGNED NULL,
	`md5` VARCHAR(50) NULL COMMENT 'MD5 hash jména karty' COLLATE 'utf8_general_ci'
) ENGINE=MyISAM;

-- Exportování struktury pro tabulka scrapknight.costs
CREATE TABLE IF NOT EXISTS `costs` (
  `card_id` varchar(20) NOT NULL COMMENT 'ID karty',
  `buy` smallint(5) unsigned DEFAULT NULL,
  `buy_foil` smallint(5) unsigned DEFAULT NULL,
  `sell` smallint(5) unsigned DEFAULT NULL,
  `sell_foil` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`card_id`),
  CONSTRAINT `costs_ibfk_3` FOREIGN KEY (`card_id`) REFERENCES `cards` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Různé ceny jednotlivých karet.';

-- Export dat nebyl vybrán.
-- Exportování struktury pro tabulka scrapknight.editions
CREATE TABLE IF NOT EXISTS `editions` (
  `id` varchar(50) NOT NULL COMMENT 'ID edice (XXX...)',
  `name` varchar(50) DEFAULT NULL COMMENT 'Plný název edice',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Seznam zkratek edic a jejich plných názvů.';

-- Export dat nebyl vybrán.
-- Exportování struktury pro tabulka scrapknight.info
CREATE TABLE IF NOT EXISTS `info` (
  `key` tinyint(3) unsigned NOT NULL COMMENT 'Klíč jen pro snazší práci.',
  `created` datetime DEFAULT NULL COMMENT 'Datum buildu databáze.',
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Informace o databázi a aplikaci. (Časem možná i nastavení?)';

-- Export dat nebyl vybrán.
-- Exportování struktury pro pohled scrapknight.card_details
-- Odebírání dočasné tabulky a vytváření struktury Pohledu
DROP TABLE IF EXISTS `card_details`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `card_details` AS (select `cards`.`id` AS `id`,`cards`.`name` AS `name`,`cards`.`edition_id` AS `edition_id`,`editions`.`name` AS `edition_name`,`cards`.`manacost` AS `manacost`,`costs`.`buy` AS `buy`,`costs`.`sell` AS `sell`,`costs`.`buy_foil` AS `buy_foil`,`costs`.`sell_foil` AS `sell_foil`,`cards`.`md5` AS `md5` from ((`cards` left join `costs` on((`cards`.`id` = `costs`.`card_id`))) left join `editions` on((`cards`.`edition_id` = `editions`.`id`))));

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
