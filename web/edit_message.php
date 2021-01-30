<?php
include "login_check.inc";
include "header.inc";
include "settings.inc";

require_once "DBConnection.php";

$db = new DBConnection();

date_default_timezone_set($_SESSION['timezone']);

$msg_id = $_GET['id'];
$msg_guild_id = $db->get_message_guild_id($msg_id);
$msg_delivery_channel_id = $db->get_message_delivery_channel_id($msg_id);
$msg_repeats = $db->get_message_repeats($msg_id);
$repeat_frequency_full = preg_replace("/;.*/", "", $msg_repeats);
$repeat_frequency = preg_replace("/:.*/", "", $repeat_frequency_full);
$repeat_frequency_num = preg_replace("/.*:/", "", $repeat_frequency_full);
if(preg_match("/=/", $msg_repeats)){
  $repeat_skip_if_num = preg_replace("/.*=/", "", $msg_repeats);
} else {
  $repeat_skip_if_num = "";
}
$msg_repeat_until = $db->get_message_repeat_until($msg_id);
if($msg_repeat_until != ""){
  $msg_repeat_until = date("Y-m-d\TG:i", $msg_repeat_until);
}

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button onclick=\"edit_message()\" >Save</button>\n";
print "<button onclick=\"location.href='message.php?id=".$msg_id."'\" >Cancel</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";

$connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
$connection->set_charset("utf8mb4");

$channels = array();
$templates = array();
$servers = $connection->query("SELECT g.id, g.guild_name FROM user_guilds AS u, guilds AS g WHERE u.guild_id = g.id AND u.user_id = ".$_SESSION['user_id'])->fetch_all();

foreach($servers as $server){
  $server_channels = $connection->query("SELECT id, name FROM channels WHERE guild_id = ".$server[0])->fetch_all();
  foreach($server_channels as $channel){
    $channels[$server[0]][] = array($channel[0], $channel[1]);
  }
  $templates[$server[0]][] = "None";
  $server_templates = $connection->query("SELECT id FROM messages WHERE delivery_time is NULL AND guild_id = ".$server[0])->fetch_all();
  foreach($server_templates as $template){
    $templates[$server[0]][] = $template[0];
  }
}

print "<table>\n";
print "  <tr>\n";
print "    <th id='id_table_header'>Message ID</th>\n";
print "    <td id='msg_id'>".$msg_id."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Author</th>\n";
print "    <td>".$_SESSION['USER']."</td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Server</th>\n";
print "    <td>\n";
print "      <select id='server' style='display:table-cell; width:100%' onchange='server_select_updated()'>\n";
foreach($servers as $server){
  print "        <option value='".$server[0]."'";
  if($server[0] == $msg_guild_id){
    print " selected";
  }
  print ">$server[1]</option>\n";
}
print "      </select>\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Channel</th>\n";
print "    <td>\n";
print "      <select id='channel' name='channel' style='display:table-cell; width:100%'>\n";
foreach($channels[$msg_guild_id] as $channel){
  print "        <option value='".$channel[0]."'";
  if($channel[0] == $msg_delivery_channel_id){
    print " selected";
  }
  print ">$channel[1]</option>\n";
}
print "    </td>\n";
print "  </tr>\n";
print "  <tr id='delivery_time_row'>\n";
print "    <th>Delivery Time</th>\n";
print "    <td><input id='delivery_time' type=datetime-local value='".date("Y-m-d\TG:i",$db->get_message_delivery_time($msg_id))."' /></td>\n";
print "  </tr>\n";
print "  <tr id='from_template_row'>\n";
print "    <th>From Template</th>\n";
print "    <td>\n";
print "      <select id='from_template' style='display:table-cell; width:100%' onchange='update_content_from_template()'>\n";
foreach($templates[$msg_guild_id] as $template){
  print "        <option value='".$template."'>$template</option>\n";
}
print "    </td>\n";
print "      </select>\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr id='repeats_row'>\n";
print "    <th>Repeats</th>\n";
print "    <td>\n";
print "      <select id='repeats_select' style='display:table-cell; width:50%' onchange='update_repeats_select()'>\n";
print "        <option value='None'";
if($repeat_frequency == ""){ print " selected"; }
print ">None</option>\n";
print "        <option value='minutes'";
if($repeat_frequency == "minutes"){ print " selected"; }
print ">minutes</option>\n";
print "        <option value='hours'";
if($repeat_frequency == "hours"){ print " selected"; }
print ">hours</option>\n";
print "        <option value='daily'";
if($repeat_frequency == "daily"){ print " selected"; }
print ">daily</option>\n";
print "        <option value='weekly'";
if($repeat_frequency == "weekly"){ print " selected"; }
print ">weekly</option>\n";
print "        <option value='monthly'";
if($repeat_frequency == "monthly"){ print " selected"; }
print ">monthly</option>\n";
print "      </select>\n";
print "      <input id='repeats_num' style='display:table-cell; width:20%;' value='$repeat_frequency_num' />\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr id='skip_if_row'>\n";
print "    <th>Skip if</th>\n";
print "    <td>\n";
print "      <input id='skip_if_checkbox' type='checkbox' onchange='toggle_skip_if_num()' />\n";
print "      <input id='skip_if_num' style='display:table-cell; width:20%' value='$repeat_skip_if_num' />\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr id='repeat_until_row'>\n";
print "    <th>Repeat Until</th>\n";
print "    <td>\n";
print "      <input id='repeat_until_checkbox' type='checkbox' onchange='toggle_repeat_until_datetime()' />\n";
print "      <input id='repeat_until_datetime' type=datetime-local value='$msg_repeat_until'/>\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Description</th>\n";
print "    <td><input id='description' style='display:table-cell; width:100%' value='".$db->get_message_description($msg_id)."' /></td>\n";
print "  </tr>\n";
print "</table>\n";
print "<br><br>\n";
print "<textarea id='content' cols='124' rows='24' maxlength='1992'>\n";
print $db->get_message_content($msg_id);
print "</textarea>\n";
print "</center><br>\n";

$connection->close();

print "<script>\n";
$js_channels = json_encode($channels);
echo "var channels = ". $js_channels . ";\n";
$js_templates = json_encode($templates);
echo "var templates = ". $js_templates . ";\n";
echo "var msg_id = '" . $msg_id . "';\n";
?>
setInputFilter(document.getElementById("repeats_num"), function(value) {
  return /^\d?\d?\d?$/.test(value); // Allow digits and '.' only, using a RegExp
});
setInputFilter(document.getElementById("skip_if_num"), function(value) {
  return /^\d?\d?\d?$/.test(value); // Allow digits and '.' only, using a RegExp
});

function server_select_updated(){
  update_channel_select();
  update_from_template_select();
}

$(function(){
<?php
if($repeat_frequency == ""){
  print "  $('#repeat_until_row').hide()\n";
  print "  $('#skip_if_row').hide()\n";
}
if($repeat_frequency_num == ""){ print "  $('#repeats_num').hide()\n"; }
if($repeat_skip_if_num == ""){
  print "  $('#skip_if_num').hide()\n";
} else {
  print "  $('#skip_if_checkbox').prop('checked', true)\n";
}
if($msg_repeat_until == ""){
  print "  $('#repeat_until_datetime').hide()\n";
} else {
  print "  $('#repeat_until_checkbox').prop('checked', true)\n";
}
?>
});
</script>
