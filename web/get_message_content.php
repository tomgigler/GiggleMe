<?php

require_once "DBConnection.php";

session_start();

date_default_timezone_set($_SESSION['timezone']);

$db = new DBConnection();
print $db->get_message_content($_GET['msg_id']);
