<?php

require_once "DBConnection.php";

session_start();

if(!isset($_SESSION['USER'])){ exit; }

date_default_timezone_set($_SESSION['timezone']);

$db = new DBConnection();
$repeat_until == '';
if($_POST['repeat_until'] != ''){ $repeat_until = strtotime($_POST['repeat_until']); }
$db->edit_message($_POST['msg_id'], $_POST['server_id'], $_POST['channel_id'], strtotime($_POST['delivery_time']), $_POST['description'], $_POST['content'], $_POST['repeats'], $repeat_until);
