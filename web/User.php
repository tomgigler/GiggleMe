<?php

require_once "DBConnection.php";

class User {

  function reset_password($user)
  {
    $db = new DBConnection();
    $db->connect() or die('There was an error connecting to the database.');
    $result = $db->run_query("UPDATE user SET password=PASSWORD('changeme') WHERE username='".$user."'");
    $db->close();
  }

  function change_password($password)
  {
    $db = new DBConnection();
    $db->connect() or die('There was an error connecting to the database.');

    $stmt = $db->connection->prepare("UPDATE users SET password=PASSWORD(?) WHERE name=?");
    $stmt->bind_param('ss', $password, $_SESSION['USER']);
    $stmt->execute();
    $stmt->close();

    $db->close();
  }

} //User
?>
