<?php
require_once "Message.php";

session_start();

if (!isset($_SESSION['username'])) {
  exit;
}

if (!isset($_POST['msg_ids'])) {
  http_response_code(400);
  echo "Missing msg_ids";
  exit;
}

$msg_ids = json_decode($_POST['msg_ids'], true);

if (!is_array($msg_ids)) {
  http_response_code(400);
  echo "Invalid msg_ids format";
  exit;
}

$deleted = [];

foreach ($msg_ids as $id) {
  // Assuming hashes are alphanumeric and 8 chars
  if (preg_match('/^[a-zA-Z0-9]{8}$/', $id)) {
    Message::delete_message_by_id($id);
    $deleted[] = $id;
  }
}

$_SESSION['message'] = "<center><font color='green' size='+2'><b>--Deleted: " . implode(', ', $deleted) . "--</b></font></center><br>\n";

echo "Success";
