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

  function create_message($msg_id, $guild_id, $delivery_channel_id, $delivery_time, $description, $content){
    $this->connect();
    $timestamp = time();
    $stmt = $this->connection->prepare("INSERT INTO messages VALUES ( ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL )");
    $stmt->bind_param('siiiiss', $msg_id, $guild_id, $delivery_channel_id, $delivery_time, $_SESSION['user_id'], $content, $description);
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
