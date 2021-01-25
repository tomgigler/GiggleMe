<?php

require_once "DBConnection.php";

class Login {

   var $db;

   function Login(){

   }//Login

   function verify($user, $pass){

      $this->db = new DBConnection();
      $this->db->connect() or die('There was an error connecting to the database.');

      $stmt = $this->db->connection->prepare("SELECT * FROM users WHERE name = ? AND password = PASSWORD(?)");
      $stmt->bind_param('ss', $user, $pass);
      $stmt->execute();
      $result = $stmt->get_result();
      $ret = mysqli_num_rows($result);
      $this->db->close();

      return $ret;

   }//verify

}//Login

?>
