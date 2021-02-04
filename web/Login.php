<?php

require_once "DBConnection.php";

class Login {

   function Login(){

   }//Login

   function verify($user, $pass, $persist, $db_name){

      $db = new DBConnection();

      $user = $db->get_user($user, $pass);
      $_SESSION['USER'] = $user[0];
      $_SESSION['DATABASE'] = $db_name;
      $_SESSION['timezone'] = $user[1];
      $_SESSION['user_id'] = $user[2];

      if($persist){
         $this->set_cookies($user[0], $db_name, $user[1], $user[2]);
      }
      return count($user);

   }

   function reset_user($user, $db_name){

      $db = new DBConnection();

      $user = $db->get_authenticated_user($user);
      $_SESSION['USER'] = $user[0];
      $_SESSION['DATABASE'] = $db_name;
      $_SESSION['timezone'] = $user[1];
      $_SESSION['user_id'] = $user[2];

      $this->set_cookies($user[0], $db_name, $user[1], $user[2]);

   }

   function set_cookies($user, $db_name, $timezone, $user_id){
      setcookie('USER', $user, time()+60*60*24*365);
      setcookie($db_name, '1', time()+60*60*24*365);
      setcookie('timezone', $timezone, time()+60*60*24*365);
      setcookie('user_id', $user_id, time()+60*60*24*365);
   }

}//Login

?>
