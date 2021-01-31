<?php

require_once "DBConnection.php";

class Login {

   function Login(){

   }//Login

   function verify($user, $pass){

      $db = new DBConnection();

      $user = $db->get_user($user, $pass);
      $_SESSION['timezone'] = $user[1];
      $_SESSION['user_id'] = $user[2];

      return count($user);

   }//verify

}//Login

?>
