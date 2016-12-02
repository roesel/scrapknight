-- Adminer 4.2.5 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';

DROP DATABASE IF EXISTS `scrapknight`;
CREATE DATABASE `scrapknight` /*!40100 DEFAULT CHARACTER SET utf32 COLLATE utf32_czech_ci */;
USE `scrapknight`;

DROP TABLE IF EXISTS `cards`;
CREATE TABLE `cards` (
  `id` varchar(20) COLLATE utf32_czech_ci NOT NULL COMMENT 'ID karty',
  `name` varchar(100) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Název karty',
  `edition_id` varchar(50) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Edice karty (zkratka)',
  `manacost` varchar(10) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Manacost (formát?)',
  `md5` varchar(50) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'MD5 hash jména karty',
  PRIMARY KEY (`id`),
  KEY `md5` (`md5`),
  KEY `edition_id` (`edition_id`),
  CONSTRAINT `cards_ibfk_2` FOREIGN KEY (`edition_id`) REFERENCES `editions` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf32 COLLATE=utf32_czech_ci COMMENT='Seznam všech karet v databázi.';


DROP TABLE IF EXISTS `costs`;
CREATE TABLE `costs` (
  `card_id` varchar(20) COLLATE utf32_czech_ci NOT NULL COMMENT 'ID karty',
  `buy` smallint(5) unsigned DEFAULT NULL,
  `buy_foil` smallint(5) unsigned DEFAULT NULL,
  `sell` smallint(5) unsigned DEFAULT NULL,
  `sell_foil` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`card_id`),
  CONSTRAINT `costs_ibfk_3` FOREIGN KEY (`card_id`) REFERENCES `cards` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf32 COLLATE=utf32_czech_ci COMMENT='Různé ceny jednotlivých karet.';


DROP TABLE IF EXISTS `editions`;
CREATE TABLE `editions` (
  `id` varchar(50) COLLATE utf32_czech_ci NOT NULL COMMENT 'ID edice (XXX...)',
  `name` varchar(50) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Plný název edice',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf32 COLLATE=utf32_czech_ci COMMENT='Seznam zkratek edic a jejich plných názvů.';


-- 2016-12-02 23:26:11
