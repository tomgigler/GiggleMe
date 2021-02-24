<?php

require_once "DBConnection.php";

class BadRequestException extends Exception {}

class Message {

  function Message($id, $guild_id, $delivery_channel_id, $delivery_time, $author_id, $repeats, $content, $description, $repeat_until, $pin_message, $save=false){
    $this->id = $id;
    $this->guild_id = strval($guild_id);
    $this->delivery_channel_id = strval($delivery_channel_id);
    $this->delivery_time = $delivery_time;
    $this->author_id = strval($author_id);
    $this->repeats = $repeats;
    $this->content = $content;
    $this->description = $description;
    $this->repeat_until = $repeat_until;
    $this->pin_message = $pin_message;
    if($save){
      $db = new DBConnection();
      $db->create_or_update_message($id, $guild_id, $delivery_channel_id, $delivery_time, $author_id, $repeats, $content, $description, $repeat_until, $pin_message);
    }
    $this->set_all();
  }

  function guild_name(){
    $db = new DBConnection();
    return $db->get_guild_name($this->guild_id);
  }

  function delivery_channel_name(){
    $db = new DBConnection();
    return $db->get_channel_name($this->delivery_channel_id);
  }

  function author_name(){
    $db = new DBConnection();
    return $db->get_user_name($this->author_id);
  }

  function message_type(){
    if(is_null($this->delivery_time)) return "template";
    elseif($this->delivery_time < 0) return "proposal";
    else return "message";
  }

  function delivery_time_format(){
    if(is_null($this->delivery_time) || $this->delivery_time < 0) return null;
    return date("g:i:s A D M j, Y T",$this->delivery_time);
  }

  function delivery_time_java_format(){
    if(is_null($this->delivery_time) || $this->delivery_time < 0) return null;
    return date("Y-m-d\TH:i",$this->delivery_time);
  }

  function repeat_until_format(){
    if(is_null($this->repeat_until) || $this->repeat_until < 0) return null;
    return date("g:i:s A D M j, Y T",$this->repeat_until);
  }

  function repeat_until_java_format(){
    if(is_null($this->repeat_until) || $this->repeat_until < 0) return null;
    return date("Y-m-d\TH:i",$this->repeat_until);
  }

  function repeat_frequency(){
    $repeat_frequency_full = preg_replace("/;.*/", "", $this->repeats);
    return preg_replace("/:.*/", "", $repeat_frequency_full);
  }

  function repeat_frequency_num(){
    $repeat_frequency_full = preg_replace("/;.*/", "", $this->repeats);
    $repeat_frequency = preg_replace("/:.*/", "", $repeat_frequency_full);
    if(preg_match("/:/", $repeat_frequency_full))
      return preg_replace("/.*:/", "", $repeat_frequency_full);
    return "";
  }

  function repeat_skip_if(){
    if(preg_match("/=/", $this->repeats))
      return preg_replace("/.*=/", "", $this->repeats);
    return "";
  }

  function set_all(){
    $this->author = $this->author_name();
    $this->server = $this->guild_name();
    $this->channel = $this->delivery_channel_name();
    $this->delivery_time_format = $this->delivery_time_format();
    $this->delivery_time_java_format = $this->delivery_time_java_format();
    $this->repeat_until_format = $this->repeat_until_format();
    $this->repeat_until_java_format = $this->repeat_until_java_format();
    $this->repeat_frequency = $this->repeat_frequency();
    $this->repeat_frequency_num = $this->repeat_frequency_num();
    $this->repeat_skip_if = $this->repeat_skip_if();
    $this->message_type = $this->message_type();
  }

  static function get_message_by_id($id){
    $db = new DBConnection();
    $msg = $db->get_message_by_id($id);
    $message = new Message($msg[0], $msg[1], $msg[2], $msg[3], $msg[4], $msg[5], $msg[7], $msg[8], $msg[9], $msg[10]);
    return $message;
  }

  static function get_messages(){
    $db = new DBConnection();
    $msgs = $db->get_messages();
    $messages = array();
    foreach($msgs as $msg){
      $message = new Message($msg[0], $msg[1], $msg[2], $msg[3], $msg[4], $msg[5], $msg[7], $msg[8], $msg[9], $msg[10]);
      array_push($messages, $message);
    }
    return $messages;
  }

  static function create_message_from_command($cmd, $guild_id){
    $db = new DBConnection();
    [ $command, $content ] = explode("\n", $cmd, 2);
    if(!preg_match("/^~giggle +(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(:\d{2})?) +channel=([^ ]+) +desc=\"(.+)\" *$/", $command, $matches)){
      throw new BadRequestException("Invalid command:\n".$command);
    }
    // ~giggle 2021-02-05 18:00 channel=truth-wanted desc=\"TW NOW - Show Channel\"
    if(!$time = strtotime($matches[1])){
      throw new BadRequestException("Invalid time format:\n".$matches[1]);
    }
    $channel_id = $db->get_channel_by_name($matches[3], $guild_id);
    if(is_null($channel_id)){
      throw new BadRequestException("Cannot find channel ".$matches[3] ." in ".$db->get_guild_name($guild_id)." server");
    }
    $msg_id = substr(md5(rand().time()),0,8);
    $message = new Message($msg_id, $guild_id, $channel_id, $time, $_SESSION['user_id'], null, $content, $matches[4], null, true);
    return $message;
  }

  static function delete_message_by_id($id){
    $db = new DBConnection();
    $db->delete_message($id);
  }
}
?>
