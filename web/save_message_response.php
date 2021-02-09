<?php
////////////////////////////////////////////////////////////////////////////////////////////////////////
//
// Success responses
// 200 OK: The request has succeeded
// 201 Created: The request has succeeded and a new resource has been created as a result
//
// Client error resonses
// 400 Bad Request: The server could not understand the request due to invalid syntax
// 401 Unauthorized: Although the HTTP standard specifies "unauthorized", semantically this response
//     means "unauthenticated". That is, the client must authenticate itself to get the requested response
// 403 Forbidden: The client does not have access rights to the content; that is, it is unauthorized, so the
//     server is refusing to give the requested resource. Unlike 401, the client's identity is known to the server
// 404 Not Found: The server can not find the requested resource
//
// Server error responses
// 500 Internal Server Error: The server has encountered a situation it doesn't know how to handle.
// 501 Not Implemented: The request method is not supported by the server and cannot be handled.
//     The only methods that servers are required to support (and therefore that must not return this code) are GET and HEAD.
//
////////////////////////////////////////////////////////////////////////////////////////////////////////

require_once "DBConnection.php";

session_start();

if(!isset($_SESSION['username'])){
  http_response_code(401);
  exit;
}

date_default_timezone_set($_SESSION['timezone']);

if($_POST['message_type']=='message' || $_POST['message_type']=='template'){
  $db = new DBConnection();
  $repeat_until == '';
  if($_POST['repeat_until'] != ''){ $repeat_until = strtotime($_POST['repeat_until']); }
  if($_POST['message_type']=='message'){
    $db->create_message($_POST['message_id'], $_POST['server_id'], $_POST['channel_id'], strtotime($_POST['delivery_time']), $_POST['description'], $_POST['content'], $_POST['repeats'], $repeat_until);
  } else {
    $db->create_message($_POST['message_id'], $_POST['server_id'], $_POST['channel_id'], '', $_POST['description'], $_POST['content'], '', '');
  }

  $message = $db->get_message($_POST['message_id']);
  http_response_code(201);

  $messageObj->message_id = $message[0];
  $messageObj->author = $message[1];
  $messageObj->server = $message[2];
  $messageObj->channel = $message[3];
  if($message[4]){
    $messageObj->delivery_time = date("g:i:s A D M j, Y T",$message[4]);
    $messageObj->delivery_time_java_format = date("Y-m-d\TH:i",$message[4]);
  } else {
    $messageObj->delivery_time = '';
  }
  if($message[5]){
    $messageObj->repeats = $message[5];
  } else {
    $messageObj->repeats = '';
  }
  if($message[6]){
    $messageObj->repeat_until = date("g:i:s A D M j, Y T",$message[6]);
    $messageObj->repeat_until_java_format = date("Y-m-d\TH:i",$message[6]);
  } else {
    $messageObj->repeat_until = '';
  }
  $messageObj->description = $message[7];
  $messageObj->content = $message[8];
  $messageObj->guild_id = strval($message[9]);
  $messageObj->channel_id = strval($message[10]);

  $repeat_frequency_full = preg_replace("/;.*/", "", $messageObj->repeats);
  $repeat_frequency = preg_replace("/:.*/", "", $repeat_frequency_full);
  if(preg_match("/:/", $repeat_frequency_full)){
	    $repeat_frequency_num = preg_replace("/.*:/", "", $repeat_frequency_full);
  } else {
	    $repeat_frequency_num = "";
  }
  if(preg_match("/=/", $messageObj->repeats)){
	    $repeat_skip_if = preg_replace("/.*=/", "", $messageObj->repeats);
  } else {
	    $repeat_skip_if = "";
  }

  $messageObj->repeat_frequency = $repeat_frequency;
  $messageObj->repeat_frequency_num = $repeat_frequency_num;
  $messageObj->repeat_skip_if = $repeat_skip_if;

  $myJSON = json_encode($messageObj);
  print $myJSON;

} elseif($_POST['message_type']=='batch'){
  http_response_code(501);
  print "TODO: Implement batch processing";
}
?>
