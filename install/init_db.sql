-- Adminer 4.2.5 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';

DROP DATABASE IF EXISTS `scrapknight`;
CREATE DATABASE `scrapknight` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci */;
USE `scrapknight`;

DROP TABLE IF EXISTS `editions`;
CREATE TABLE `editions` (
  `id` varchar(50) COLLATE utf8_general_ci NOT NULL COMMENT 'ID edice (XXX...)',
  `name` varchar(50) COLLATE utf8_general_ci DEFAULT NULL COMMENT 'Plný název edice',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='Seznam zkratek edic a jejich plných názvů.';


DROP TABLE IF EXISTS `cards`;
CREATE TABLE `cards` (
  `id` varchar(20) COLLATE utf8_general_ci NOT NULL COMMENT 'ID karty',
  `name` varchar(100) COLLATE utf8_general_ci DEFAULT NULL COMMENT 'Název karty',
  `edition_id` varchar(50) COLLATE utf8_general_ci DEFAULT NULL COMMENT 'Edice karty (zdratka)',
  `manacost` varchar(10) COLLATE utf8_general_ci DEFAULT NULL COMMENT 'Manacost (formát?)',
  `md5` varchar(50) COLLATE utf8_general_ci DEFAULT NULL COMMENT 'MD5 hash jména karty',
  PRIMARY KEY (`id`),
  KEY `edition_id` (`edition_id`),
  KEY `name` (`name`),
  KEY `manacost` (`manacost`),
  KEY `md5` (`md5`),
  FULLTEXT `name_fulltext` (`name`),
  CONSTRAINT `cards_ibfk_2` FOREIGN KEY (`edition_id`) REFERENCES `editions` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='Seznam všech karet v databázi.';


DROP TABLE IF EXISTS `costs`;
CREATE TABLE `costs` (
  `card_id` varchar(20) COLLATE utf8_general_ci NOT NULL COMMENT 'ID karty',
  `buy` smallint(5) unsigned DEFAULT NULL,
  `buy_foil` smallint(5) unsigned DEFAULT NULL,
  `sell` smallint(5) unsigned DEFAULT NULL,
  `sell_foil` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`card_id`),
  CONSTRAINT `costs_ibfk_3` FOREIGN KEY (`card_id`) REFERENCES `cards` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='Různé ceny jednotlivých karet.';


DROP VIEW IF EXISTS `card_details`;
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

-- 2016-12-03 00:15:11
