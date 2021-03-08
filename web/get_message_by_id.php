<?php

require_once "Message.php";

session_start();

if(!isset($_SESSION['username'])){
  http_response_code(401);
  print "It looks like your session has expired\nPlease refresh the page";
  exit;
}

date_default_timezone_set($_SESSION['timezone']);

$message = Message::get_message_by_id($_GET['msg_id']);

$myJSON = json_encode($message);
print $myJSON;

?>
