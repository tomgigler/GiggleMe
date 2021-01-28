<?php

require_once "DBConnection.php";

class Login {

   var $db;

   function Login(){

   }//Login

   function verify($user, $pass){

      $this->db = new DBConnection();
      $this->db->connect() or die('There was an error connecting to the database.');

      $stmt = $this->db->connection->prepare("SELECT users.name, timezones.name, users.user FROM users, timezones WHERE users.name = ? AND users.timezone = timezones.id AND users.password = PASSWORD(?)");
      $stmt->bind_param('ss', $user, $pass);
      $stmt->execute();
      $result = $stmt->get_result();
      $ret = mysqli_num_rows($result);
      $row = $result->fetch_row();
      $_SESSION['timezone'] = $row[1];
      $_SESSION['user_id'] = $row[2];

      $this->db->close();

      return $ret;

   }//verify

}//Login

?>
