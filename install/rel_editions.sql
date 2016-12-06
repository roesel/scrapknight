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

-- Exportování struktury pro tabulka scrapknight.rel_editions
DROP TABLE IF EXISTS `rel_editions`;
CREATE TABLE IF NOT EXISTS `rel_editions` (
  `id_cr` varchar(50) DEFAULT NULL,
  `id_sdk` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Transition table for edition IDs between SDK and CR.';

-- Exportování dat pro tabulku scrapknight.rel_editions: ~34 rows (přibližně)
/*!40000 ALTER TABLE `rel_editions` DISABLE KEYS */;
INSERT INTO `rel_editions` (`id_cr`, `id_sdk`) VALUES
	('ZEX', 'EXP'),
	('KLI', 'MPS'),
	('FTV20', 'V13'),
	('MMB', 'MM2'),
	('FTVAnh', 'V14'),
	('FTVAng', 'V15'),
	('FTVD', 'DRB'),
	('FTVE', 'V09'),
	('FTVL', 'V11'),
	('FTVLor', 'V16'),
	('FTVRlm', 'V12'),
	('FTVRlc', 'V10'),
	('FNM', 'pFNM'),
	('P02', 'PO2'),
	('CMA', 'CM1'),
	('DDDVD', 'DDC'),
	('DDAvB', 'DDH'),
	('DDBvC', 'DDQ'),
	('DDEvK', 'DDO'),
	('DDEvT', 'DDF'),
	('DDEvG', 'EVG'),
	('DDGvL', 'DDD'),
	('DDHvM', 'DDL'),
	('DDIvG', 'DDJ'),
	('DDJvC', 'DD2'),
	('DDJvV', 'DDM'),
	('DDKvD', 'DDG'),
	('DDNvO', 'DDR'),
	('DDPvC', 'DDE'),
	('DDSvT', 'DDK'),
	('DDSvC', 'DDN'),
	('DDVvK', 'DDI'),
	('DDZvE', 'DDP'),
	('PDS', 'H09'),
	('PDL', 'PD2'),
	('PDG', 'PD3');
/*!40000 ALTER TABLE `rel_editions` ENABLE KEYS */;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
