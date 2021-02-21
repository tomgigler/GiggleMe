<?php

require_once "Message.php";

session_start();

print Message::get_message_by_id($_GET['msg_id'])->delivery_channel_id;
