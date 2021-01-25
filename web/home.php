<?php
include "login_check.inc";
include "header.inc";
include "settings.inc";

print "<center>\n";
print "<button onclick=\"location.href='change_password.php'\" >Change Password</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "</center>\n";
print "<br><br>\n";

date_default_timezone_set("US/Pacific");
$connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
$messages = $connection->query("SELECT m.id, g.guild_name, u.name, m.delivery_time, m.description FROM messages AS m, guilds AS g, users AS u WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time >= 0 ORDER BY delivery_time");

print "<center>\n";
if(mysqli_num_rows($messages)){
print "<table border=1>\n";
print "  <tr><th colspan=5><b>Messages</b></th></tr>\n";
print "  <tr>\n";
print "    <th>Message ID</th>\n";
print "    <th>Server Name</th>\n";
print "    <th>Author</th>\n";
print "    <th>Delivery Time</th>\n";
print "    <th>Description</th>\n";
print "  </tr>\n";
while($row = $messages->fetch_row()) {
  print "  <tr>\n";
  print "<td>$row[0]</td><td>$row[1]</td><td>$row[2]</td><td name=\"delivery_time\">$row[3]</td><td>$row[4]</td>\n";
  print "  </tr>\n";
}
print "</table>\n";
print "<br><br>\n";
}

$templates = $connection->query("SELECT m.id, g.guild_name, u.name, m.description FROM messages AS m, guilds AS g, users AS u WHERE m.guild_id = g.id AND m.author_id = u.user AND m.delivery_time is NULL ORDER BY delivery_time");

if(mysqli_num_rows($templates)){
print "<table border=1>\n";
print "  <tr><th colspan=5><b>Templates</b></th></tr>\n";
print "  <tr>\n";
print "    <th>Template ID</th>\n";
print "    <th>Server Name</th>\n";
print "    <th>Author</th>\n";
print "    <th>Description</th>\n";
print "  </tr>\n";
while($row = $templates->fetch_row()) {
  print "  <tr>\n";
  # 12:30:00 PM Sun Jan 24, 2021 MST
  print "<td>$row[0]</td><td>$row[1]</td><td>$row[2]</td><td>$row[3]</td>\n";
  print "  </tr>\n";
}
print "</table>\n";
}

$connection->close();
?>
<script>

function convert_times(){
  var cells = document.getElementsByName('delivery_time')
  for(var i = 0; i < cells.length; i++){
    var myDate = new Date(parseInt(cells[i].innerHTML)*1000)
    // 12:30:00 PM Sun Jan 24, 2021 MST
    cells[i].innerHTML = myDate
  }
}

window.onload = function() {
  convert_times()
}</script>
</center>
