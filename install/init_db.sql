-- Adminer 4.2.5 MySQL dump + HeidiSQL edits

SET NAMES utf8;
SET time_zone = '+00:00';

DROP DATABASE IF EXISTS `scrapknight`;
CREATE DATABASE `scrapknight` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci */;
USE `scrapknight`;

CREATE TABLE `editions` (
  `id` varchar(50) NOT NULL COMMENT 'ID edice (XXX...)',
  `name` varchar(50) DEFAULT NULL COMMENT 'Plný název edice',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Seznam zkratek edic a jejich plných názvů.';

CREATE TABLE IF NOT EXISTS `sdk_editions` (
  `code` varchar(50) NOT NULL COMMENT 'ID edice (XXX...)',
  `name` varchar(50) DEFAULT NULL COMMENT 'Plný název edice',
  `gatherer_code` varchar(50) DEFAULT NULL COMMENT 'Kód gathereru.',
  `magic_cards_info_code` varchar(50) DEFAULT NULL COMMENT '?',
  `release_date` date DEFAULT NULL COMMENT 'Datum vydání edice.',
  `border` varchar(50) DEFAULT NULL COMMENT 'Barva okraje.',
  `type` varchar(50) DEFAULT NULL COMMENT 'Typ edice.',
  `block` varchar(50) DEFAULT NULL COMMENT 'Block edice.',
  PRIMARY KEY (`code`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Edice natažené z SDK.';

CREATE TABLE `cards` (
  `id` varchar(20) NOT NULL COMMENT 'ID karty',
  `name` varchar(100) DEFAULT NULL COMMENT 'Název karty',
  `edition_id` varchar(50) DEFAULT NULL COMMENT 'Edice karty (zkratka)',
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

CREATE TABLE IF NOT EXISTS `sdk_cards` (
  `name` varchar(100) DEFAULT NULL COMMENT 'Název',
  `mid` mediumint(9) NOT NULL COMMENT 'Multiverse ID',
  `layout` varchar(50) DEFAULT NULL COMMENT 'Rozvržení',
  `mana_cost` varchar(50) DEFAULT NULL COMMENT 'Manacost (formát?)',
  `type` varchar(50) DEFAULT NULL COMMENT 'Typ',
  `rarity` varchar(50) DEFAULT NULL COMMENT 'Rarita',
  `set` varchar(50) DEFAULT NULL COMMENT 'Edice',
  `id` varchar(50) DEFAULT NULL COMMENT 'ID karty (hash)',
  PRIMARY KEY (`mid`),
  KEY `edition_id` (`layout`),
  KEY `manacost` (`mana_cost`),
  KEY `md5` (`id`),
  KEY `name` (`name`),
  FULLTEXT KEY `name_fulltext` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='Seznam všech karet v databázi, bráno z SDK.';

CREATE TABLE `costs` (
  `card_id` varchar(20) NOT NULL COMMENT 'ID karty',
  `buy` smallint(5) unsigned DEFAULT NULL,
  `buy_foil` smallint(5) unsigned DEFAULT NULL,
  `sell` smallint(5) unsigned DEFAULT NULL,
  `sell_foil` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`card_id`),
  CONSTRAINT `costs_ibfk_3` FOREIGN KEY (`card_id`) REFERENCES `cards` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Různé ceny jednotlivých karet.';

CREATE TABLE `info` (
  `key` tinyint(3) unsigned NOT NULL COMMENT 'Klíč jen pro snazší práci.',
  `created` datetime DEFAULT NULL COMMENT 'Datum buildu databáze.',
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Informace o databázi a aplikaci. (Časem možná i nastavení?)';

CREATE VIEW card_details(
  `id`, `name`, `edition_id`, `edition_name`, `manacost`, `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`)
  AS (
    SELECT
      `cards`.`id`,
      `cards`.`name`,
      `cards`.`edition_id`,
      `editions`.`name` as `edition_name`,
      `cards`.`manacost`,
      `costs`.`buy`,
      `costs`.`sell`,
      `costs`.`buy_foil`,
      `costs`.`sell_foil`,
      `cards`.`md5`
    FROM `cards`
    LEFT JOIN `costs` ON `cards`.`id` = `costs`.`card_id`
    LEFT JOIN `editions` ON `cards`.`edition_id` = `editions`.`id`
);
