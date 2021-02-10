<?php

require_once "DBConnection.php";

class Message {
  var $id;
  var $guild_id;
  var $delivery_channel_id;
  var $delivery_time;
  var $author_id;
  var $repeats;
  var $content;
  var $description;
  var $repeat_until;

  function Message($id, $guild_id, $delivery_channel_id, $delivery_time, $author_id, $repeats, $content, $description, $repeat_until){
    $this->id = $id;
    $this->guild_id = strval($guild_id);
    $this->delivery_channel_id = strval($delivery_channel_id);
    $this->delivery_time = $delivery_time;
    $this->author_id = strval($author_id);
    $this->repeats = $repeats;
    $this->content = $content;
    $this->description = $description;
    $this->repeat_until = $repeat_until;
  }

  static function get_message_by_id($id){
    $db = new DBConnection();
    $msg = $db->get_message_by_id($id);
    return new Message($msg[0], $msg[1], $msg[2], $msg[3], $msg[4], $msg[5], $msg[7], $msg[8], $msg[9]);
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
    if(is_null($delivery_time)) return "template";
    elseif($delivery_time < 0) return "proposal";
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

}

?>
