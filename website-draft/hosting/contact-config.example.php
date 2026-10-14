<?php
// Install OUTSIDE public_html as optimizeit-private/contact-config.php.
// Replace placeholders on the server; never put actual credentials in Git.
return [
 'dsn' => 'mysql:host=localhost;dbname=CPANEL_DATABASE;charset=utf8mb4',
 'user' => 'CPANEL_DATABASE_USER',
 'password' => 'SET_ON_SERVER_ONLY',
 'rate_secret' => 'SET_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS',
 'allowed_origins' => ['https://optimizeit.co', 'https://www.optimizeit.co'],
 'consent_version' => 'privacy-2026-10',
];
