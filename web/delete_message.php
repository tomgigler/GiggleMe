<?php

require_once "Message.php";

session_start();

if(!isset($_SESSION['username'])){ exit; }

Message::delete_message_by_id($_POST['msg_id']);

$_SESSION['message'] = "<center><font color='green' size='+2'><b>--Deleted message ".$_POST['msg_id']."--</b></font></center><br>\n";
