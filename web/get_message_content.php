<?php

require_once "DBConnection.php";

session_start();

$db = new DBConnection();
print $db->get_message_col("content", $_GET['msg_id']);
