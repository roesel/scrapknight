CREATE TABLE `rel_editions` (
  `id_cr` varchar(50) DEFAULT NULL,
  `id_sdk` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Transition table for edition IDs between SDK and CR.';

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
