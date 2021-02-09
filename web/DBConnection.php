<?php 

class DBConnection {
  var $connection;
   
  function DBConnection(){
  } //DBConnection

  function connect(){
    include "settings.php";
    $this->connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
    $this->connection->set_charset("utf8mb4");
    return $this->connection;
  } //connect

  function close(){
    $this->connection->close();
  } //close

  function get_message_col($col, $msg_id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT m.$col FROM messages AS m, user_guilds AS g WHERE m.id = ? AND m.guild_id = g.guild_id AND g.user_id = ?");
    $stmt->bind_param('si', $msg_id, $_SESSION['user_id']);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_user_timezone($user_id){
    $this->connect();
    $sql = "SELECT timezones.name FROM users, timezones WHERE users.user = ? AND users.timezone = timezones.id";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('i', $user_id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all()[0][0];
    $this->close();
    return $ret;
  }

  function get_message($msg_id){
    $this->connect();
    $sql = "SELECT m.id, u.name, g.guild_name, c.name, m.delivery_time, m.repeats, m.repeat_until, m.description, m.content, g.id, c.id ";
    $sql .= "FROM messages AS m, guilds AS g, users AS u, channels AS c, user_guilds AS ug ";
    $sql .= "WHERE m.id = ? AND m.delivery_channel_id = c.id AND m.guild_id = g.id AND u.user = m.author_id AND ug.user_id = ?";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('si', $msg_id, $_SESSION['user_id']);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all()[0];
    $this->close();
    return $ret;
  }

  function get_user_guilds(){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT g.id, g.guild_name FROM user_guilds AS u, guilds AS g WHERE u.guild_id = g.id AND u.user_id = ?");
    $stmt->bind_param('i', $_SESSION['user_id']);
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
    $this->connect();
    $sql = "SELECT m.id, g.guild_name, c.name, u.name, m.delivery_time, m.repeats, m.repeat_until, m.description ";
    $sql .= "FROM messages AS m, guilds AS g, users AS u, channels AS c ";
    $sql .= "WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time > 0 AND c.id = m.delivery_channel_id ";
    $sql .= "AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = ? ) ";
    $sql .= "ORDER BY delivery_time";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('i', $_SESSION['user_id']);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function get_templates(){
    $this->connect();
    $sql = "SELECT m.id, g.guild_name, c.name, u.name, m.description, g.id, c.id ";
    $sql .= "FROM messages AS m, guilds AS g, users AS u, channels AS c ";
    $sql .= "WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time is NULL AND c.id = m.delivery_channel_id ";
    $sql .= "AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = ? ) ";
    $sql .= "ORDER BY delivery_time";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('i', $_SESSION['user_id']);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function create_message($msg_id, $guild_id, $delivery_channel_id, $delivery_time, $description, $content, $repeats, $repeat_until){
    $this->connect();
    $timestamp = time();
    $sql = "INSERT INTO messages VALUES ( ?, ?, ?, NULL, ?, NULL, NULL, ?, ?, NULL ) ";
    $sql .= "ON DUPLICATE KEY UPDATE guild_id = ?, delivery_channel_id = ?, author_id = ?, content = ?, description = ?";
    $sql = $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('siiissiiiss', $msg_id, $guild_id, $delivery_channel_id, $_SESSION['user_id'], $content, $description, $guild_id, $delivery_channel_id, $_SESSION['user_id'], $content, $description);
    $stmt->execute();
    if($delivery_time != ''){
      $stmt = $this->connection->prepare("UPDATE messages SET delivery_time = ? WHERE id = ?");
      $stmt->bind_param('is', $delivery_time, $msg_id);
      $stmt->execute();
    }
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
    $this->connection->query("INSERT INTO request_queue values ('".$msg_id."', 'create', ".time().") ON DUPLICATE KEY UPDATE request_time = ".time());
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
