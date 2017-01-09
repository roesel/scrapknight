-- Adminer 4.2.5 MySQL dump + HeidiSQL edits

SET NAMES utf8;
SET time_zone = '+00:00';

DROP DATABASE IF EXISTS `scrapknight`;
CREATE DATABASE `scrapknight` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci */;
USE `scrapknight`;

CREATE TABLE `editions` (
  `id` VARCHAR(255) NOT NULL COMMENT 'ID edice (XXX...)',
  `name` VARCHAR(255) DEFAULT NULL COMMENT 'Plný název edice',
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
  `id` VARCHAR(255) NOT NULL COMMENT 'ID karty',
  `name` VARCHAR(255) DEFAULT NULL COMMENT 'Název karty',
  `edition_id` VARCHAR(50) DEFAULT NULL COMMENT 'Edice karty (zkratka)',
  `manacost` VARCHAR(50) DEFAULT NULL COMMENT 'Manacost (formát?)',
  `md5` VARCHAR(50) DEFAULT NULL COMMENT 'MD5 hash jména karty',
  PRIMARY KEY (`id`),
  KEY `edition_id` (`edition_id`),
  KEY `name` (`name`),
  KEY `manacost` (`manacost`),
  KEY `md5` (`md5`),
  FULLTEXT KEY `name_fulltext` (`name`),
  CONSTRAINT `cards_ibfk_2` FOREIGN KEY (`edition_id`) REFERENCES `editions` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Seznam všech karet v databázi.';

CREATE TABLE IF NOT EXISTS `sdk_cards` (
  `name` VARCHAR(255) DEFAULT NULL COMMENT 'Název',
  `mid` mediumint(9) DEFAULT NULL COMMENT 'Multiverse ID',
  `layout` varchar(50) DEFAULT NULL COMMENT 'Rozvržení',
  `mana_cost` varchar(50) DEFAULT NULL COMMENT 'Manacost (formát?)',
  `type` varchar(50) DEFAULT NULL COMMENT 'Typ',
  `rarity` varchar(50) DEFAULT NULL COMMENT 'Rarita',
  `set` varchar(50) DEFAULT NULL COMMENT 'Edice',
  `id` varchar(50) NOT NULL COMMENT 'ID karty (hash)',
  PRIMARY KEY (`id`),
  KEY `mid` (`mid`),
  KEY `layout` (`layout`),
  KEY `mana_cost` (`mana_cost`),
  KEY `id` (`id`),
  KEY `name` (`name`),
  FULLTEXT KEY `name_fulltext` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='Seznam všech karet v databázi, bráno z SDK.';

CREATE TABLE `costs` (
  `card_id` VARCHAR(255) NOT NULL COMMENT 'ID karty',
  `buy` INT unsigned DEFAULT NULL,
  `buy_foil` INT unsigned DEFAULT NULL,
  `sell` INT unsigned DEFAULT NULL,
  `sell_foil` INT unsigned DEFAULT NULL,
  PRIMARY KEY (`card_id`),
  CONSTRAINT `costs_ibfk_3` FOREIGN KEY (`card_id`) REFERENCES `cards` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Různé ceny jednotlivých karet.';

CREATE TABLE `info` (
  `key` tinyint(3) unsigned NOT NULL COMMENT 'Klíč jen pro snazší práci.',
  `created` datetime DEFAULT NULL COMMENT 'Datum buildu databáze.',
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Informace o databázi a aplikaci. (Časem možná i nastavení?)';

CREATE TABLE `rel_cards` (
  `id_cr` varchar(50) DEFAULT NULL,
  `id_sdk` varchar(50) DEFAULT NULL,
  UNIQUE KEY `id_cr` (`id_cr`),
  UNIQUE KEY `id_sdk` (`id_sdk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='Transition table for edition IDs between SDK and CR.';

CREATE TABLE `rel_editions` (
  `id_cr` varchar(50) DEFAULT NULL,
  `id_sdk` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Transition table for edition IDs between SDK and CR.';

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

CREATE VIEW card_details_extended(
  `id`, `name`, `edition_id`, `edition_name`, `manacost`, `buy`, `sell`, `buy_foil`, `sell_foil`, `md5`,
  `mid`, `layout`, `type`, `rarity`)
  AS (
    SELECT
      `card_details`.`id`,
      `card_details`.`name`,
      `card_details`.`edition_id`,
      `card_details`.`edition_name`,
      `card_details`.`manacost`,
      `card_details`.`buy`,
      `card_details`.`sell`,
      `card_details`.`buy_foil`,
      `card_details`.`sell_foil`,
      `card_details`.`md5`,
      `sdk_cards`.`mid`,
      `sdk_cards`.`layout`,
      `sdk_cards`.`type`,
      `sdk_cards`.`rarity`
    FROM `rel_cards`
    INNER JOIN `card_details` ON `card_details`.`id` = `rel_cards`.`id_cr`
    INNER JOIN `sdk_cards` ON `sdk_cards`.`mid` = `rel_cards`.`id_sdk`
);

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `avatar` varchar(200) DEFAULT NULL,
  `tokens` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='List of app users.';

CREATE TABLE `users_cards` (
  `user_id` INT NOT NULL,
  `card_id` VARCHAR(255) NOT NULL,
  `count` INT NOT NULL,
  PRIMARY KEY (`user_id`, `card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='List of cards belonging to users';

ALTER TABLE `users_cards`
ADD UNIQUE INDEX `card_user_unique` (`user_id` ASC, `card_id` ASC);

CREATE TABLE `users_decks` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `name` VARCHAR(255)  DEFAULT NULL,
  `info` TEXT,
  PRIMARY KEY (`id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT = 'Decks belonging to users.';

CREATE TABLE `users_decks_cards` (
  `deck_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `card_id` VARCHAR(255) NOT NULL,
  `count` INT NOT NULL,
  PRIMARY KEY (`deck_id`, `user_id`, `card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT = 'Cards belonging to decks.';
