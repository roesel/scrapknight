-- --------------------------------------------------------
-- Hostitel:                     127.0.0.1
-- Verze serveru:                10.1.19-MariaDB - mariadb.org binary distribution
-- OS serveru:                   Win32
-- HeidiSQL Verze:               9.4.0.5125
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- Exportování struktury databáze pro
CREATE DATABASE IF NOT EXISTS `scrapknight` /*!40100 DEFAULT CHARACTER SET utf32 COLLATE utf32_czech_ci */;
USE `scrapknight`;

-- Exportování struktury pro tabulka scrapknight.cards
CREATE TABLE IF NOT EXISTS `cards` (
  `id` varchar(20) COLLATE utf32_czech_ci NOT NULL COMMENT 'ID dané karty XXX1234',
  `name` varchar(100) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Title of the card',
  `edition` varchar(10) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Edition of the card in letter abbreviation.',
  `manacost` varchar(10) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Manacost (format?)',
  `md5` varchar(50) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'MD5 hash of name.',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf32 COLLATE=utf32_czech_ci;

-- Export dat nebyl vybrán.
-- Exportování struktury pro tabulka scrapknight.costs
CREATE TABLE IF NOT EXISTS `costs` (
  `id` varchar(20) COLLATE utf32_czech_ci NOT NULL COMMENT 'ID karty',
  `buy` smallint(5) unsigned DEFAULT NULL,
  `buy_foil` smallint(5) unsigned DEFAULT NULL,
  `sell` smallint(5) unsigned DEFAULT NULL,
  `sell_foil` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf32 COLLATE=utf32_czech_ci COMMENT='Různé ceny jednotlivých karet.';

-- Export dat nebyl vybrán.
-- Exportování struktury pro tabulka scrapknight.editions
CREATE TABLE IF NOT EXISTS `editions` (
  `id` varchar(50) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'ID edice (XXX...)',
  `name` varchar(50) COLLATE utf32_czech_ci DEFAULT NULL COMMENT 'Plný název edice'
) ENGINE=InnoDB DEFAULT CHARSET=utf32 COLLATE=utf32_czech_ci COMMENT='Seznam zkratek edic a jejich plných názvů.';

-- Export dat nebyl vybrán.
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
