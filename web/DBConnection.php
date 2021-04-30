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

  function get_guild_name($id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT guild_name FROM guilds WHERE id = ?");
    $stmt->bind_param('i', $id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret[0][0];
  }

  function get_channel_name($id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT name FROM channels WHERE id = ?");
    $stmt->bind_param('i', $id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret[0][0];
  }

  function get_channel_by_name($channel_name, $guild_id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT id FROM channels WHERE name = ? and guild_id = ?");
    $stmt->bind_param('si', $channel_name, $guild_id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret[0][0];
  }

  function get_user_name($id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT name FROM users WHERE user = ?");
    $stmt->bind_param('i', $id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret[0][0];
  }

  function get_message_by_id($id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT m.* FROM messages AS m, user_guilds AS g WHERE m.id = ? AND m.guild_id = g.guild_id AND g.user_id = ?");
    $stmt->bind_param('si', $id, $_SESSION['user_id']);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret[0];
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

  function get_custom_channels(){
    $this->connect();
    $sql = "SELECT g.guild_name, c.name, c.channel_type, c.screen_name FROM guilds as g, channels as c ";
    $sql .= "WHERE c.channel_type IS NOT NULL AND c.channel_type != 1 AND g.id = c.guild_id ";
    $sql .= "AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = ? )";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('i', $_SESSION['user_id']);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function create_channel($id, $guild_id, $name, $channel_type, $token_key, $token_secret, $user_id, $screen_name){
    $this->connect();
    $sql = "INSERT INTO channels VALUES ( ?, ?, ?, ?, ?, ?, ?, ? ) ON DUPLICATE KEY UPDATE name = ?, token_key = ?, token_secret = ?, user_id = ?, screen_name = ?";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('iisisssssssss', $id, $guild_id, $name, $channel_type, $token_key, $token_secret, $user_id, $screen_name, $name, $token_key, $token_secret, $user_id, $screen_name);
    $stmt->execute();
    $this->close();
  }

  function get_guild_templates($guild_id){
    $this->connect();
    $stmt = $this->connection->prepare("SELECT id, description FROM messages WHERE delivery_time is NULL AND guild_id = ?");
    $stmt->bind_param('i', $guild_id);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function get_messages(){
    $this->connect();
    $sql = "SELECT m.* FROM messages AS m, guilds AS g, users AS u, channels AS c ";
    $sql .= "WHERE m.guild_id = g.id AND m.author_id = u.user AND c.id = m.delivery_channel_id ";
    $sql .= "AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = ? ) ";
    $sql .= "ORDER BY delivery_time";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('i', $_SESSION['user_id']);
    $stmt->execute();
    $ret = $stmt->get_result()->fetch_all();
    $this->close();
    return $ret;
  }

  function create_or_update_message($id, $guild_id, $delivery_channel_id, $delivery_time, $author_id, $repeats, $content, $description, $repeat_until, $special_handling){
    $this->connect();
    $sql = "INSERT INTO messages VALUES ( ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ? ) ";
    $sql .= "ON DUPLICATE KEY UPDATE guild_id = ?, delivery_channel_id = ?, delivery_time = ?, repeats = ?, content = ?, description = ?, repeat_until = ?, special_handling = ?";
    $stmt = $this->connection->prepare($sql);
    $stmt->bind_param('siiiisssiiiiisssii', $id, $guild_id, $delivery_channel_id, $delivery_time, $author_id, $repeats, $content, $description, $repeat_until, $special_handling,
    $guild_id, $delivery_channel_id, $delivery_time, $repeats, $content, $description, $repeat_until, $special_handling);
    $stmt->execute();
    $this->connection->query("INSERT INTO request_queue values ('".$id."', 'create', NOW()) ON DUPLICATE KEY UPDATE request_time = NOW()");
    $this->close();
  }

  function delete_message($msg_id){
    $this->connect();
    $timestamp = time();
    $this->connection->query("DELETE FROM messages WHERE id = '".$msg_id."'");
    $this->connection->query("DELETE FROM request_queue WHERE id = '".$msg_id."'");
    $this->connection->query("INSERT INTO request_queue values ('".$msg_id."', 'delete', ".time().") ON DUPLICATE KEY UPDATE request_time = ".time());
    $this->close();
  }

}
?>
