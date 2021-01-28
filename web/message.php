<?php
include "login_check.inc";
include "header.inc";
include "settings.inc";

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";

date_default_timezone_set($_SESSION['timezone']);
$connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
$connection->set_charset("utf8mb4");
$msg_id = $_GET['id'];
$sql = <<<SQL
SELECT m.id, u.name, g.guild_name, c.name, m.delivery_time, m.repeats, m.repeat_until, m.description, m.content
FROM messages AS m, guilds AS g, users AS u, channels AS c
WHERE m.id = '$msg_id' AND m.delivery_channel_id = c.id AND m.guild_id = g.id AND u.user = m.author_id
SQL;

$message = $connection->query($sql)->fetch_all()[0];

print "<table>\n";
print "  <tr>\n";
print "    <th>Message ID</th>\n";
print "    <td>".$message[0]."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Author</th>\n";
print "    <td>".$message[1]."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Server</th>\n";
print "    <td>".$message[2]."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Channel</th>\n";
print "    <td>".$message[3]."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Delivery Time</th>\n";
print "    <td>".date("g:i:s A D M j, Y T",$message[4])."</td>\n";
print "  </tr>\n";
if($message[5]){
  print "  <tr>\n";
  print "    <th>Repeats</th>\n";
  print "    <td>".$message[5]."</td>\n";
  print "  </tr>\n";
  if($message[6]){
    print "  <tr>\n";
    print "    <th>Repeat Until</th>\n";
    print "    <td>".date("g:i:s A D M j, Y T",$message[6])."</td>\n";
    print "  </tr>\n";
  }
}
if($message[7]){
  print "  <tr>\n";
  print "    <th>Description</th>\n";
  print "    <td>".$message[7]."</td>\n";
  print "  </tr>\n";
}
print "</table>\n";
print "</center><br>\n";
print "<div class='content-div'>\n";
print "  <pre>".htmlspecialchars($message[8])."</pre>\n";
print "</div>\n";
$connection->close();
?>
