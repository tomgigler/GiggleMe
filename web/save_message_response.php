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

require_once "Message.php";

session_start();

if(!isset($_SESSION['username'])){
  http_response_code(401);
  print "It looks like your session has expired\nPlease refresh the page";
  exit;
}

date_default_timezone_set($_SESSION['timezone']);

if($_POST['message_type']=='message' || $_POST['message_type']=='template'){
  if(preg_match("/\/\/\//", $_POST['content'])){
    http_response_code(400);
    print "Placeholder '///' found in message body!";
    exit();
  }

  $repeats = $_POST['repeats'] == '' ? null : $_POST['repeats'];
  $special_handling = $_POST['pin_message'] == 0 ? null : $_POST['pin_message'];
  $delivery_time = $_POST['delivery_time'] == '' ? null : strtotime($_POST['delivery_time']);
  $repeat_until = $_POST['repeat_until'] == '' ? null : strtotime($_POST['repeat_until']);
  $message = new Message($_POST['message_id'], $_POST['server_id'], $_POST['channel_id'], $delivery_time, $_SESSION['user_id'], $repeats, $_POST['content'], $_POST['description'], $repeat_until, $special_handling, true);

  http_response_code(201);

  $myJSON = json_encode($message);
  print $myJSON;

} elseif($_POST['message_type']=='batch'){
  $delim = substr(md5(time()),0,18);
  $input = preg_replace("/\n\s*\n\+{20}\++\n\s*\n/", $delim, $_POST['content']);
  $obj = explode($delim, $input);

  $messages = array();
  foreach($obj as $msg){
    try {
      $message = Message::create_message_from_command($msg, $_POST['server_id']);
    }
    catch(BadRequestException $e) {
      foreach($messages as $msg_id){
        Message::delete_message_by_id($msg_id);
      }
      http_response_code(400);
      print $e->getMessage();
      exit();
    }
    array_push($messages, $message->id);
  }
  print "Created ".count($messages)." messages\n".json_encode($messages);
}
?>
