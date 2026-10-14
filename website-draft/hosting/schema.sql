CREATE TABLE IF NOT EXISTS optimizeit_contacts (
 id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
 request_id CHAR(32) NOT NULL UNIQUE,
 name VARCHAR(120) NOT NULL,
 company VARCHAR(160) NOT NULL,
 email VARCHAR(254) NOT NULL,
 phone VARCHAR(40) NOT NULL DEFAULT '',
 service VARCHAR(64) NOT NULL,
 message TEXT NOT NULL,
 source_path VARCHAR(255) NOT NULL,
 utm_source VARCHAR(200) NOT NULL DEFAULT '',
 utm_medium VARCHAR(200) NOT NULL DEFAULT '',
 utm_campaign VARCHAR(200) NOT NULL DEFAULT '',
 consent_version VARCHAR(64) NOT NULL,
 consent_at DATETIME NOT NULL,
 created_at DATETIME NOT NULL,
 INDEX idx_created_at (created_at),
 INDEX idx_service (service)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS optimizeit_contact_limits (
 bucket CHAR(64) NOT NULL PRIMARY KEY,
 attempts SMALLINT UNSIGNED NOT NULL DEFAULT 0,
 expires_at DATETIME NOT NULL,
 INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
