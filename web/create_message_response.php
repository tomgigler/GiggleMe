<?php

require_once "DBConnection.php";

session_start();

date_default_timezone_set($_SESSION['timezone']);

$db = new DBConnection();
$db->create_message($_POST['msg_id'], $_POST['server_id'], $_POST['channel_id'], strtotime($_POST['delivery_time']), $_POST['description'], $_POST['content']);
