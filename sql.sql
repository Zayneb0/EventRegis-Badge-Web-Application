CREATE TABLE IF NOT EXISTS `Événement` (
  `id_événement` INT NOT NULL AUTO_INCREMENT,
  `titre` VARCHAR(255) NOT NULL,
  `date_début` DATE NOT NULL,
  `date_fin` DATE NOT NULL,
  `lieu` VARCHAR(255),
  `sponsort` VARCHAR(255),
  `description_courte` TEXT,
  `logo` VARCHAR(255),
  PRIMARY KEY (`id_événement`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `Client` (
  `id_client` INT NOT NULL AUTO_INCREMENT,
  `nom` VARCHAR(255) NOT NULL,
  `prénom` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `tel` VARCHAR(20),
  `date_naissance` DATE,
  `genre` VARCHAR(50),
  `date_creation` DATE,
  `date_modification` DATE,
  `id_événement` INT, 
  PRIMARY KEY (`id_client`),
  FOREIGN KEY (`id_événement`) REFERENCES `Événement`(`id_événement`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `Utilisateurs` (
  `id_utilisateur` INT NOT NULL AUTO_INCREMENT,
  `nom` VARCHAR(255) NOT NULL,
  `prénom` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `téléphone` VARCHAR(20),
  `statut` VARCHAR(100),
  `profile` VARCHAR(100),
  `date_inscription` DATE,
  `date_modification` DATE,
  PRIMARY KEY (`id_utilisateur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;