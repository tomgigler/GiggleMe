<?php 

class DBConnection {
  var $connection;
   
  function DBConnection(){
  } //DBConnection

  function connect(){
    include "settings.inc";
    $this->connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
    $this->connection->set_charset("utf8mb4");
    return $this->connection;
  } //connect

  function close(){
    $this->connection->close();
  } //close

  function get_message_repeat_until($msg_id){
    $this->connect();
    $sql = "SELECT repeat_until FROM messages WHERE id = '$msg_id'";
    $ret = $this->connection->query($sql)->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_message_repeats($msg_id){
    $this->connect();
    $sql = "SELECT repeats FROM messages WHERE id = '$msg_id'";
    $ret = $this->connection->query($sql)->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_message_delivery_time($msg_id){
    $this->connect();
    $sql = "SELECT delivery_time FROM messages WHERE id = '$msg_id'";
    $ret = $this->connection->query($sql)->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_message_description($msg_id){
    $this->connect();
    $sql = "SELECT description FROM messages WHERE id = '$msg_id'";
    $ret = $this->connection->query($sql)->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_message_content($msg_id){
    $this->connect();
    $sql = "SELECT content FROM messages WHERE id = '$msg_id'";
    $ret = $this->connection->query($sql)->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_message_delivery_channel_id($msg_id){
    $this->connect();
    $sql = "SELECT delivery_channel_id FROM messages WHERE id = '$msg_id'";
    $ret = $this->connection->query($sql)->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_message_guild_id($msg_id){
    $this->connect();
    $sql = "SELECT guild_id FROM messages WHERE id = '$msg_id'";
    $ret = $this->connection->query($sql)->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_user($user, $pass){
    $this->connect();
    $sql = "SELECT users.name, timezones.name, users.user FROM users, timezones WHERE users.name = ? AND users.timezone = timezones.id AND users.password = PASSWORD(?)";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('ss', $user, $pass);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all()[0];
    $this->close();
    return $ret;
  }

  function get_message($msg_id){
    $this->connect();
    $sql = "SELECT m.id, u.name, g.guild_name, c.name, m.delivery_time, m.repeats, m.repeat_until, m.description, m.content ";
    $sql .= "FROM messages AS m, guilds AS g, users AS u, channels AS c ";
    $sql .= "WHERE m.id = ? AND m.delivery_channel_id = c.id AND m.guild_id = g.id AND u.user = m.author_id";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('s', $msg_id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all()[0];
    $this->close();
    return $ret;
  }

  function get_user_guilds($user_id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT g.id, g.guild_name FROM user_guilds AS u, guilds AS g WHERE u.guild_id = g.id AND u.user_id = ?");
    $stmt->bind_param('i', $user_id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function get_guild_channels($guild_id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT id, name FROM channels WHERE guild_id = ?");
    $stmt->bind_param('i', $guild_id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function get_guild_templates($guild_id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT id FROM messages WHERE delivery_time is NULL AND guild_id = ?");
    $stmt->bind_param('i', $guild_id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function get_messages(){
    $user_id = intval($_SESSION['user_id']);
    $this->connect();
    $sql = "SELECT m.id, g.guild_name, c.name, u.name, m.delivery_time, m.repeats, m.repeat_until, m.description ";
    $sql .= "FROM messages AS m, guilds AS g, users AS u, channels AS c ";
    $sql .= "WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time > 0 AND c.id = m.delivery_channel_id ";
    $sql .= "AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = $user_id ) ";
    $sql .= "ORDER BY delivery_time";
    $ret = $this->connection->query($sql)->fetch_all();
    $this->close();
    return $ret;
  }

  function get_templates(){
    $user_id = intval($_SESSION['user_id']);
    $this->connect();
    $sql = "SELECT m.id, g.guild_name, c.name, u.name, m.description, g.id, c.id ";
    $sql .= "FROM messages AS m, guilds AS g, users AS u, channels AS c ";
    $sql .= "WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time is NULL AND c.id = m.delivery_channel_id ";
    $sql .= "AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = $user_id ) ";
    $sql .= "ORDER BY delivery_time";

    $ret = $this->connection->query($sql)->fetch_all();
    $this->close();
    return $ret;
  }

  function create_template($msg_id, $guild_id, $delivery_channel_id, $description, $content){
    $this->connect();
    $timestamp = time();
    $stmt = $this->connection->prepare("INSERT INTO messages VALUES ( ?, ?, ?, NULL, ?, NULL, NULL, ?, ?, NULL )");
    $stmt->bind_param('siiiss', $msg_id, $guild_id, $delivery_channel_id, $_SESSION['user_id'], $content, $description);
    $stmt->execute();
    $this->connection->query("INSERT INTO request_queue values ('".$msg_id."', 'create', ".time().") ON DUPLICATE KEY UPDATE request_time = ".time());
    $this->close();
  }

  function create_message($msg_id, $guild_id, $delivery_channel_id, $delivery_time, $description, $content, $repeats, $repeat_until){
    $this->connect();
    $timestamp = time();
    $stmt = $this->connection->prepare("INSERT INTO messages VALUES ( ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL )");
    $stmt->bind_param('siiiiss', $msg_id, $guild_id, $delivery_channel_id, $delivery_time, $_SESSION['user_id'], $content, $description);
    $stmt->execute();
    if($repeats != ''){
      $stmt = $this->connection->prepare("UPDATE messages SET repeats = ? WHERE id = ?");
      $stmt->bind_param('ss', $repeats, $msg_id);
      $stmt->execute();
    }
    if($repeat_until != ''){
      $stmt = $this->connection->prepare("UPDATE messages SET repeat_until = ? WHERE id = ?");
      $stmt->bind_param('is', $repeat_until, $msg_id);
      $stmt->execute();
    }
    $this->connection->query("INSERT INTO request_queue values ('".$msg_id."', 'create', ".time().") ON DUPLICATE KEY UPDATE request_time = ".time());
    $this->close();
  }

  function edit_message($msg_id, $guild_id, $delivery_channel_id, $delivery_time, $description, $content, $repeats, $repeat_until){
    $this->connect();
    $timestamp = time();
    $stmt = $this->connection->prepare("UPDATE messages SET guild_id = ?, delivery_channel_id = ?, delivery_time = ?, author_id = ?, content = ?, description = ? WHERE id = ?");
    $stmt->bind_param('iiiisss', $guild_id, $delivery_channel_id, $delivery_time, $_SESSION['user_id'], $content, $description, $msg_id);
    $stmt->execute();
    if($repeats != ''){
      $stmt = $this->connection->prepare("UPDATE messages SET repeats = ? WHERE id = ?");
      $stmt->bind_param('ss', $repeats, $msg_id);
    } else {
      $stmt = $this->connection->prepare("UPDATE messages SET repeats = NULL WHERE id = ?");
      $stmt->bind_param('s', $msg_id);
    }
    $stmt->execute();
    if($repeat_until != ''){
      $stmt = $this->connection->prepare("UPDATE messages SET repeat_until = ? WHERE id = ?");
      $stmt->bind_param('is', $repeat_until, $msg_id);
    } else {
      $stmt = $this->connection->prepare("UPDATE messages SET repeat_until = NULL WHERE id = ?");
      $stmt->bind_param('s', $msg_id);
    }
    $stmt->execute();
    $this->connection->query("INSERT INTO request_queue values ('".$msg_id."', 'edit', ".time().") ON DUPLICATE KEY UPDATE request_time = ".time());
    $this->close();
  }

  function delete_message($msg_id){
    $this->connect();
    $timestamp = time();
    $this->connection->query("DELETE FROM messages WHERE id = '".$msg_id."'");
    $this->connection->query("INSERT INTO request_queue values ('".$msg_id."', 'delete', ".time().") ON DUPLICATE KEY UPDATE request_time = ".time());
    $this->close();
  }

}
?>
