<?php 

class DBConnection {
  var $connection;
   
  function DBConnection(){
  } //DBConnection

  function connect(){
    include "settings.inc";
    $this->connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
    return $this->connection;
  } //connect

  function close(){
    $this->connection->close();
  } //close

  function get_messages(){
    $user_id = intval($_SESSION['user_id']);
    $this->connect();
    $sql = <<<SQL
        SELECT m.id, g.guild_name, c.name, u.name, m.delivery_time, m.repeats, m.repeat_until, m.description
        FROM messages AS m, guilds AS g, users AS u, channels AS c
        WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time > 0 AND c.id = m.delivery_channel_id
        AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = $user_id )
        ORDER BY delivery_time
SQL;
    $ret = $this->connection->query($sql)->fetch_all();
    $this->close();
    return $ret;
  }

  function get_templates(){
    $user_id = intval($_SESSION['user_id']);
    $this->connect();
    $sql = <<<SQL
        SELECT m.id, g.guild_name, c.name, u.name, m.description, g.id, c.id
        FROM messages AS m, guilds AS g, users AS u, channels AS c
        WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time is NULL AND c.id = m.delivery_channel_id
        AND g.id in ( SELECT guild_id FROM user_guilds WHERE user_id = $user_id )
        ORDER BY delivery_time
SQL;

    $ret = $this->connection->query($sql)->fetch_all();
    $this->close();
    return $ret;
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
