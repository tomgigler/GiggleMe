<?php

require_once "Login.php";

   include "settings.inc";

   session_start();

   $log = new Login();

   if(isset($_COOKIE['USER']) && isset($_COOKIE[$db_name])){
      $log->reset_user($_COOKIE['USER'], $db_name);
   }
   elseif (isset($_POST['USER']) && isset($_POST['PASS']))
   {
      if(!$log->verify($_POST['USER'], $_POST['PASS'], $_POST['PERSIST'], $db_name))
      {
         $message = "<center><font color='red'><b>--Incorrect username or password--</b></font></center><br>\n";
      }
   }

   if (!isset($_SESSION['USER']) || $_SESSION['DATABASE'] != $db_name) 
   {
      include "header.inc";

      if (isset($message))
      {
         print $message;
         unset($message);
      } else {
         print "<br><br>\n";
      }

      print "      <form name='form' method='POST' enctype='multipart/form-data' autocomplete='off'>\n";
      print "         <center>\n";
      print "   <b>Username:</b>   <input type='text' name='USER'/><br>\n";
      print "         <br>\n";
      print "   <b>Password:</b>   <input type='password' name='PASS'/><br>\n";
      print "         <br>\n";
      print "   <input type='checkbox' name='PERSIST'/>&nbsp;<b>Keep me signed in</b> \n";
      print "         <br><br>\n";
      print "   <button onclick=submit()>Login</buton>\n";
      print "         </center>\n";
      print "      </form>\n";
      print "   </body>\n";
      print "</html>";   
   } 
   else
   {
      $host = $_SERVER['HTTP_HOST'];
      $uri = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
      header("Location: home.php");
      exit;
   }
?> 
