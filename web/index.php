<?php

require_once "Login.php";

   session_start();
   
   include "settings.inc";

   if (isset($_POST['USER']) && isset($_POST['PASS']))
   {
      $log = new Login();
      if($log->verify($_POST['USER'], $_POST['PASS']))
      {
         $_SESSION['USER'] = $_POST['USER'];
         $_SESSION['DATABASE'] = $db_name;
      } 
      else
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
      print "         <br><br>\n";
      // print "   <input class='button' type='submit' value='Login'/>\n";
      print "   <button onclick=submit()>Login</buton>\n";
      print "         </center>\n";
      print "      </form>\n";
      // include "footer.inc";
      print "   </body>\n";
      print "</html>";   
   } 
   else
   {
      $host = $_SERVER['HTTP_HOST'];
      $uri = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
      header("Location: http://$host$uri/home.php");
      exit;
   }
?> 
