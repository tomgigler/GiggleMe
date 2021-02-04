<?php
   require_once "Login.php";
   include "settings.inc";

   session_start();

   if (!isset($_SESSION['USER']) || $_SESSION['DATABASE'] != $db_name) 
   {
      if(isset($_COOKIE['USER']) && isset($_COOKIE[$db_name])){
	 $log = new Login();
         $log->reset_user($_COOKIE['USER'], $db_name);
      } else {
         $host = $_SERVER['HTTP_HOST'];
         $uri = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
         header("Location: index.php");
         exit;
      }
   }
?> 
