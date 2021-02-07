<?php

require_once "DBConnection.php";

session_start();

if(!isset($_SESSION['username'])){ exit; }

$db = new DBConnection();
$db->create_template($_POST['msg_id'], $_POST['server_id'], $_POST['channel_id'], $_POST['description'], $_POST['content']);
