<?php

require_once "DBConnection.php";

class BadRequestException extends Exception {}

class Message {

  function Message($id, $guild_id, $delivery_channel_id, $delivery_time, $author_id, $repeats, $content, $description, $repeat_until, $special_handling, $save=false){
    $this->id = $id;
    $this->guild_id = strval($guild_id);
    $this->delivery_channel_id = strval($delivery_channel_id);
    $this->delivery_time = $delivery_time;
    $this->author_id = strval($author_id);
    $this->repeats = $repeats;
    $this->content = $content;
    $this->description = $description;
    $this->repeat_until = $repeat_until;
    $this->special_handling = $special_handling;
    if($save){
      $db = new DBConnection();
      $db->create_or_update_message($id, $guild_id, $delivery_channel_id, $delivery_time, $author_id, $repeats, $content, $description, $repeat_until, $special_handling);
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

  function command(){
    if(is_null($this->delivery_time))
      $command_str = "~giggle template";
    else
      $command_str = "~giggle ".date("Y-m-d H:i:s",$this->delivery_time);
    $command_str.= " channel=".$this->channel;
    if(!is_null($this->repeats))
      $command_str.= " repeat=".$this->repeats;
      if(!is_null($this->repeat_until))
        $duration_minutes = intval(($this->repeat_until-$this->delivery_time)/60);
        if($duration_minutes > 0)
          $command_str.= " duration=minutes:".$duration_minutes;
    if($this->special_handling == 1)
      $command_str.= " pin=true";
    if($this->description != "")
      $command_str.= " desc=\"".$this->description."\"";
    return $command_str;
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
    $this->command = $this->command();
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
    if(!preg_match("/^(~g(iggle)? +((\d{4}-)?\d{1,2}-\d{1,2} \d{1,2}:\d{2}(:\d{2})?|\d+))/", $command, $matches)){
      throw new BadRequestException("Invalid command:\n".$command);
    }
    if(preg_match("/\/\/\//", $content)){
      throw new BadRequestException("Placeholder `///` found in message body!");
    }
    // ~giggle 2021-02-05 18:00 channel=truth-wanted desc=\"TW NOW - Show Channel\"
    $date_str = $matches[3];
    if(preg_match("/^\d+$/", $date_str)){
      $delay = intval($date_str);
      if($delay == 0) $time = 0;
      else $time = time() + intval($date_str) * 60;
    } else {
      if(!$matches[4]) $date_str = date("Y")."-".$date_str;
      if(!$time = strtotime($date_str)){
        throw new BadRequestException("Invalid time format:\n".$date_str);
      }
    }
    $remaining_args = preg_replace("/".preg_quote($matches[1])."/", "", $command);

    if(!preg_match("/(channel\s*=\s*(\S+))/", $remaining_args, $matches)){
      throw new BadRequestException("channel is required!\n".$command);
    }
    $channel_id = $db->get_channel_by_name($matches[2], $guild_id);
    if(is_null($channel_id)){
      throw new BadRequestException("Cannot find channel ".$matches[2] ." in ".$db->get_guild_name($guild_id)." server");
    }
    $remaining_args = preg_replace("/".preg_quote($matches[1])."/", "", $remaining_args);

    $desc = null;
    if(preg_match("/(desc\s*=\s*[\"\”]([^\"\”]+)[\"\”])/u", $remaining_args, $matches)){
      $desc = $matches[2];
    }
    $remaining_args = preg_replace("/".preg_quote($matches[1])."/", "", $remaining_args);

    $special_handling = null;
    if(preg_match("/(pin\s*=\s*(\S+))/", $remaining_args, $matches)){
      if(preg_match("/t(rue)?|y(es)?/i", $matches[2])) $special_handling = 1;
      elseif(!preg_match("/f(alse)?|n(o)?/i", $matches[2]))
        throw new BadRequestException("Invalid value for pin:  ".$matches[2]);
    }
    $remaining_args = preg_replace("/".preg_quote($matches[1])."/", "", $remaining_args);
    if(preg_match("/(set-topic\s*=\s*(\S+))/", $remaining_args, $matches)){
      if(preg_match("/t(rue)?|y(es)?/i", $matches[2])) $special_handling = 2;
      elseif(!preg_match("/f(alse)?|n(o)?/i", $matches[2]))
        throw new BadRequestException("Invalid value for set-topic:  ".$matches[2]);
    }
    $remaining_args = preg_replace("/".preg_quote($matches[1])."/", "", $remaining_args);
    if(preg_match("/(set-channel-name\s*=\s*(\S+))/", $remaining_args, $matches)){
      if(preg_match("/t(rue)?|y(es)?/i", $matches[2])) $special_handling = 3;
      elseif(!preg_match("/f(alse)?|n(o)?/i", $matches[2]))
        throw new BadRequestException("Invalid value for set-channel-name:  ".$matches[2]);
    }
    $remaining_args = preg_replace("/".preg_quote($matches[1])."/", "", $remaining_args);
    if(!preg_match("/^\s*$/", $remaining_args))
        throw new BadRequestException("Unrecognized parameter(s):\n".$remaining_args);

    $msg_id = substr(md5(rand().time()),0,8);
    $message = new Message($msg_id, $guild_id, $channel_id, $time, $_SESSION['user_id'], null, $content, $desc, null, $special_handling, true);
    return $message;
  }

  static function delete_message_by_id($id){
    $db = new DBConnection();
    $db->delete_message($id);
  }
}
?>
