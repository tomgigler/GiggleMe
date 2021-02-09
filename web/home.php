<?php
include "login_check.php";
include "header.php";
include "settings.php";
require_once "DBConnection.php";

print "<center>\n";
print "<button id='new_message_button' onclick=\"location.href='message.php?action=create'\">New Message</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";

if(isset($_SESSION['message']))
{
  print $_SESSION['message'];
  unset($_SESSION['message']);
} else {
  print "<br><br>\n";
}


date_default_timezone_set($_SESSION['timezone']);

$db = new DBConnection();
$messages = $db->get_messages();

$templates = $db->get_templates();

?>
<br>
<?php
if(count($messages)){
  print "<table border=1>\n";
  print "  <tr><th colspan=8><b>Messages</b></th></tr>\n";
  print "  <tr>\n";
  print "    <th>Message ID</th>\n";
  print "    <th>Server Name</th>\n";
  print "    <th>Channel</th>\n";
  print "    <th>Author</th>\n";
  print "    <th>Delivery Time</th>\n";
  print "    <th>Repeats</th>\n";
  print "    <th>Repeat Until</th>\n";
  print "    <th>Description</th>\n";
  print "  </tr>\n";
  foreach($messages as $row) {
    print "  <tr class='link-row' onclick=\"location.href='message.php?id=$row[0]'\">\n";
    // 7:00:00 PM Mon Jan 25, 2021 PST
    $delivery_time = date("g:i:s A D M j, Y T",$row[4]);
    if($row[6]) { $repeat_until = date("g:i:s A D M j, Y T",$row[6]); } else { $repeat_until = $row[6]; }
    print "    <td>$row[0]</td>\n";
    print "    <td>".htmlspecialchars($row[1])."</td>\n";
    print "    <td>".htmlspecialchars($row[2])."</td>\n";
    print "    <td>".htmlspecialchars($row[3])."</td>\n";
    print "    <td>$delivery_time</td>\n";
    print "    <td>$row[5]</td>\n";
    print "    <td>$repeat_until</td>\n";
    print "    <td>".htmlspecialchars($row[7])."</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
  print "<br><br>\n";
}

if(count($templates)){
  print "<table border=1>\n";
  print "  <tr><th colspan=5><b>Templates</b></th></tr>\n";
  print "  <tr>\n";
  print "    <th>Template ID</th>\n";
  print "    <th>Server Name</th>\n";
  print "    <th>Channel</th>\n";
  print "    <th>Author</th>\n";
  print "    <th>Description</th>\n";
  print "  </tr>\n";
  foreach($templates as $row) {
    print "  <tr class='link-row' onclick=\"location.href='message.php?id=$row[0]'\">\n";
    print "    <td>$row[0]</td>\n";
    print "    <td>".htmlspecialchars($row[1])."</td>\n";
    print "    <td>".htmlspecialchars($row[2])."</td>\n";
    print "    <td>".htmlspecialchars($row[3])."</td>\n";
    print "    <td>".htmlspecialchars($row[4])."</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
}

if(!$db->get_user_guilds()){
  print "<br><br><br>\n";
  print "<div class='footer'>\n";
  print "<center>\n";
  print "Hi " . $_SESSION['username'] . "!<br><br>\n";
  print "It looks like you don't have access to anything here<br><br>If you've already invited the " .
      "<a href='https://discord.com/api/oauth2/authorize?client_id=".$CLIENT_ID."&permissions=477248&scope=bot'>".$CLIENT_NAME."</a> bot to your server, DM the bot to request access\n";
  print "</center>\n";
  print "</div>\n";
  print "<script>\n";
  print "$('#new_message_button').toggle(false)\n";
  print "</script>\n";
}

?>
