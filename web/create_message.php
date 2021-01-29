<?php
include "login_check.inc";
include "header.inc";
include "settings.inc";

$msg_id = substr(md5(time()),0,8);

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button onclick=\"create_message()\" >Save</button>\n";
print "<button onclick=\"location.href='home.php'\" >Cancel</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";

date_default_timezone_set($_SESSION['timezone']);
$connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
$connection->set_charset("utf8mb4");

$channels = array();
$servers = $connection->query("SELECT g.guild_name, g.id FROM user_guilds AS u, guilds AS g WHERE u.guild_id = g.id AND u.user_id = ".$_SESSION['user_id'])->fetch_all();

foreach($servers as $server){
  $server_channels = $connection->query("SELECT id, name FROM channels WHERE guild_id = ".$server[1])->fetch_all();
  foreach($server_channels as $channel){
    $channels[$server[0]][] = array($channel[0], $channel[1]);
  }
}

print "<table>\n";
print "  <tr>\n";
print "    <th>Message ID</th>\n";
print "    <td id='msg_id'>".$msg_id."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Author</th>\n";
print "    <td>".$_SESSION['USER']."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Server</th>\n";
print "    <td>\n";
print "      <select id='server' name='server' style='display:table-cell; width:100%' onchange='update_channel_select()'>\n";
foreach($servers as $server){
  print "        <option value='".$server[1]."'>$server[0]</option>\n";
}
print "      </select>\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Channel</th>\n";
print "    <td>\n";
print "      <select id='channel' name='channel' style='display:table-cell; width:100%' />\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Delivery Time</th>\n";
print "    <td><input id='delivery_time' type=datetime-local /></td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>From Template</th>\n";
print "    <td></td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Repeats</th>\n";
print "    <td></td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Repeat Until</th>\n";
print "    <td></td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Description</th>\n";
print "    <td><input id='description' style='display:table-cell; width:100%' /></td>\n";
print "  </tr>\n";
print "</table>\n";
print "<br><br>\n";
print "<textarea id='content' cols='124' rows='24'>\n";
print "</textarea>\n";
print "</center><br>\n";

$connection->close();

print "<script>\n";
$js_channels = json_encode($channels);
echo "var channels = ". $js_channels . ";\n";
?>
$(function(){
  update_channel_select();
});
</script>
