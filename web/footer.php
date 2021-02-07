<?php

  include "settings.php";

  print "<div class='footer'>\n";
  print "<br><br><br>\n";
  print "<center>\n";
  print "Invite <a href='https://discord.com/oauth2/authorize?client_id=".$CLIENT_ID."&permissions=2048&scope=bot' target='_blank'>".$CLIENT_NAME."</a> to your server!\n";
  print "</center>\n";
  print "</div>\n";
  print "   </body>\n";
  print "</html>";

?>
