<?php
include "login_check.inc";
include "header.inc";
require_once "DBConnection.php";

$msg_id = substr(md5(time()),0,8);

print "<center>\n";
print "<button onclick=\"location.href='home.php'\" >Home</button>\n";
print "<button onclick=\"create_message()\" >Save</button>\n";
print "<button onclick=\"location.href='home.php'\" >Cancel</button>\n";
print "<button onclick=\"location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";

date_default_timezone_set($_SESSION['timezone']);

$db = new DBConnection();

$channels = array();
$templates = array();
$servers = $db->get_user_guilds($_SESSION['user_id']);

foreach($servers as $server){
  $server_channels = $db->get_guild_channels($server[0]);
  foreach($server_channels as $channel){
    $channels[$server[0]][] = array(strval($channel[0]), $channel[1]);
  }
  $templates[$server[0]][] = "None";
  $server_templates = $db->get_guild_templates($server[0]);
  foreach($server_templates as $template){
    $templates[$server[0]][] = $template[0];
  }
}

print "<table>\n";
print "  <tr>\n";
print "    <th>Type</th>\n";
print "    <td id='msg_type'>\n";
print "      <select id='msg_type_select' style='display:table-cell; width:100%' onchange='message_type_updated()'>\n";
print "        <option value='message'>Message</option>\n";
print "        <option value='template'>Template</option>\n";
print "      </select>\n";
print "    </td>\n";
print "  </tr>\n";
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
print "      <select id='server' name='server' style='display:table-cell; width:100%' onchange='server_select_updated()'>\n";
foreach($servers as $server){
  print "        <option value='".$server[0]."'>$server[1]</option>\n";
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
print "  <tr id='delivery_time_row'>\n";
print "    <th>Delivery Time</th>\n";
print "    <td><input id='delivery_time' type=datetime-local /></td>\n";
print "  </tr>\n";
print "  <tr id='from_template_row'>\n";
print "    <th>From Template</th>\n";
print "    <td>\n";
print "      <select id='from_template' style='display:table-cell; width:100%' onchange='update_content_from_template()' />\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr id='repeats_row'>\n";
print "    <th>Repeats</th>\n";
print "    <td>\n";
print "      <select id='repeats_select' style='display:table-cell; width:50%' onchange='update_repeats_select()'>\n";
print "        <option value='None'>None</option>\n";
print "        <option value='minutes'>minutes</option>\n";
print "        <option value='hours'>hours</option>\n";
print "        <option value='daily'>daily</option>\n";
print "        <option value='weekly'>weekly</option>\n";
print "        <option value='monthly'>monthly</option>\n";
print "      </select>\n";
print "      <input id='repeats_num' style='display:table-cell; width:20%' />\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr id='skip_if_row'>\n";
print "    <th>Skip if</th>\n";
print "    <td>\n";
print "      <input id='skip_if_checkbox' type='checkbox' onchange='toggle_skip_if_num()' />\n";
print "      <input id='skip_if_num' style='display:table-cell; width:20%' />\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr id='repeat_until_row'>\n";
print "    <th>Repeat Until</th>\n";
print "    <td>\n";
print "      <input id='repeat_until_checkbox' type='checkbox' onchange='toggle_repeat_until_datetime()' />\n";
print "      <input id='repeat_until_datetime' type=datetime-local />\n";
print "    </td>\n";
print "  </tr>\n";
print "  <tr>\n";
print "    <th>Description</th>\n";
print "    <td><input id='description' style='display:table-cell; width:100%' /></td>\n";
print "  </tr>\n";
print "</table>\n";
print "<br><br>\n";
print "<textarea id='content' cols='124' rows='24' maxlength='1992'>\n";
print "</textarea>\n";
print "</center><br>\n";

print "<script>\n";
$js_channels = json_encode($channels);
echo "var channels = ". $js_channels . ";\n";
$js_templates = json_encode($templates);
echo "var templates = ". $js_templates . ";\n";
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
  update_channel_select();
  update_from_template_select();
  $('#repeats_num').hide()
  $('#skip_if_row').hide()
  $('#skip_if_num').hide()
  $('#repeat_until_row').hide()
  $('#repeat_until_datetime').hide()
});
</script>
