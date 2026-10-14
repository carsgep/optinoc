<?php
declare(strict_types=1);
// PHP 8.1+ and PDO MySQL. No read/list/export endpoint is exposed.
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, private');
header('X-Content-Type-Options: nosniff');
date_default_timezone_set('UTC');
function respond(int $status, array $data): never {
 http_response_code($status);
 echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
 exit;
}
function field(array $body, string $name, int $max, bool $required = false): string {
 $value = $body[$name] ?? '';
 if (!is_string($value)) respond(422, ['ok'=>false,'error'=>'Revise la información del formulario.']);
 $value = trim($value);
 if (($required && $value === '') || strlen($value) > $max || str_contains($value, "\0")) {
  respond(422, ['ok'=>false,'error'=>'Revise la información del formulario.']);
 }
 return $value;
}
$method = $_SERVER['REQUEST_METHOD'] ?? '';
if (!in_array($method, ['GET','POST'], true)) {
 header('Allow: GET, POST'); respond(405, ['ok'=>false,'error'=>'Método no permitido.']);
}
try {
 $configPath = dirname((string)($_SERVER['DOCUMENT_ROOT'] ?? '')) . '/optimizeit-private/contact-config.php';
 if (!is_file($configPath)) throw new RuntimeException('Configuration unavailable');
 $config = require $configPath;
 if (!is_array($config) || strlen((string)($config['rate_secret'] ?? '')) < 32) throw new RuntimeException('Invalid configuration');
 $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
 if ($origin !== '' && !in_array($origin, $config['allowed_origins'], true)) respond(403, ['ok'=>false,'error'=>'Solicitud no permitida.']);
 session_name('OPTIMIZEIT_CONTACT');
 session_set_cookie_params(['lifetime'=>0,'path'=>'/','secure'=>true,'httponly'=>true,'samesite'=>'Lax']);
 ini_set('session.use_strict_mode','1');
 session_start();
 if ($method === 'GET') {
  if (($_GET['action'] ?? '') !== 'token') respond(404, ['ok'=>false]);
  if (!empty($_SESSION['contact_complete'])) {
   unset($_SESSION['contact_csrf'], $_SESSION['contact_request'], $_SESSION['contact_complete']);
  }
  $_SESSION['contact_csrf'] ??= bin2hex(random_bytes(32));
  $_SESSION['contact_request'] ??= bin2hex(random_bytes(16));
  respond(200, ['ok'=>true,'token'=>$_SESSION['contact_csrf'],'requestId'=>$_SESSION['contact_request']]);
 }
 if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 16384) respond(413, ['ok'=>false,'error'=>'La solicitud es demasiado extensa.']);
 if (stripos($_SERVER['CONTENT_TYPE'] ?? '', 'application/json') !== 0) respond(415, ['ok'=>false,'error'=>'Formato no permitido.']);
 $raw = file_get_contents('php://input', false, null, 0, 16385);
 if ($raw === false || strlen($raw) > 16384) respond(413, ['ok'=>false,'error'=>'La solicitud es demasiado extensa.']);
 $body = json_decode($raw, true, 20, JSON_THROW_ON_ERROR);
 if (!is_array($body)) respond(422, ['ok'=>false,'error'=>'Solicitud inválida.']);
 $token = $body['token'] ?? '';
 if (!is_string($token) || empty($_SESSION['contact_csrf']) || !hash_equals($_SESSION['contact_csrf'], $token)) respond(403, ['ok'=>false,'error'=>'La sesión expiró. Inténtelo nuevamente.']);
 $requestId = $_SESSION['contact_request'];
 if (field($body,'website',200) !== '') respond(422,['ok'=>false,'error'=>'No pudimos validar su solicitud.']);
 if (($body['consent'] ?? false) !== true) respond(422,['ok'=>false,'error'=>'Debe autorizar el tratamiento de los datos para continuar.']);
 $name=field($body,'name',120,true);$company=field($body,'company',160,true);
 $email=field($body,'email',254,true);$phone=field($body,'phone',40);$service=field($body,'service',64,true);$message=field($body,'need',8000,true);
 if (!filter_var($email,FILTER_VALIDATE_EMAIL)) respond(422,['ok'=>false,'error'=>'Ingrese un correo electrónico válido.']);
 $services=['protect-recover','cloud','infrastructure','managed-services','itsm','optinoc','optidesk','backup-as-a-service','cleanshield'];
 if (!in_array($service,$services,true)) respond(422,['ok'=>false,'error'=>'Seleccione un servicio válido.']);
 $source=field($body,'sourcePath',255);if ($source === '' || $source[0] !== '/') $source='/';
 $utmSource=field($body,'utmSource',200);$utmMedium=field($body,'utmMedium',200);$utmCampaign=field($body,'utmCampaign',200);
 $pdo=new PDO($config['dsn'],$config['user'],$config['password'],[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_EMULATE_PREPARES=>false]);
 // A retry after a network failure returns the same stored reference without duplicate leads.
 $existing=$pdo->prepare('SELECT id FROM optimizeit_contacts WHERE request_id=?');$existing->execute([$requestId]);
 if ($existing->fetchColumn() !== false) { $_SESSION['contact_complete']=true; respond(200,['ok'=>true,'reference'=>$requestId]); }
 $bucket=hash_hmac('sha256',($_SERVER['REMOTE_ADDR'] ?? 'unknown').'|'.gmdate('Y-m-d-H'),$config['rate_secret']);
 $pdo->beginTransaction();
 $rate=$pdo->prepare('INSERT INTO optimizeit_contact_limits (bucket,attempts,expires_at) VALUES (?,1,?) ON DUPLICATE KEY UPDATE attempts=attempts+1');
 $rate->execute([$bucket,gmdate('Y-m-d H:i:s',time()+7200)]);
 $count=$pdo->prepare('SELECT attempts FROM optimizeit_contact_limits WHERE bucket=?');$count->execute([$bucket]);
 if ((int)$count->fetchColumn()>5) {$pdo->commit();header('Retry-After: 3600');respond(429,['ok'=>false,'error'=>'Ha realizado varias solicitudes. Inténtelo más tarde.']);}
 $sql='INSERT INTO optimizeit_contacts (request_id,name,company,email,phone,service,message,source_path,utm_source,utm_medium,utm_campaign,consent_version,consent_at,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)';
 $now=gmdate('Y-m-d H:i:s');$insert=$pdo->prepare($sql);
 $insert->execute([$requestId,$name,$company,$email,$phone,$service,$message,$source,$utmSource,$utmMedium,$utmCampaign,$config['consent_version'],$now,$now]);
 $pdo->commit();
 $_SESSION['contact_complete']=true;
 respond(201,['ok'=>true,'reference'=>$requestId]);
} catch (JsonException $e) {
 respond(422,['ok'=>false,'error'=>'Solicitud inválida.']);
} catch (Throwable $e) {
 if (isset($pdo) && $pdo->inTransaction()) $pdo->rollBack();
 // No submitted fields or credentials are printed or written to logs.
 respond(503,['ok'=>false,'error'=>'No pudimos registrar su solicitud. Inténtelo nuevamente.']);
}
