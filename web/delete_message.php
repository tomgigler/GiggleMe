<?php

require_once "DBConnection.php";

session_start();

$db = new DBConnection();
$db->delete_message($_POST['msg_id']);

$_SESSION['message'] = "<center><font color='green' size='+2'><b>--Deleted message ".$_POST['msg_id']."--</b></font></center><br>\n";
