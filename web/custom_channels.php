<?php
include "login_check.php";
include "header.php";
require_once "DBConnection.php";

$db = new DBConnection();
if(!$db->get_user_guilds()){
  header("Location: twitter_login.php");
  exit;
}

$channels = $db->get_custom_channels();
$servers = $db->get_user_guilds();

print "<center>\n";
print "<button onclick=\"window.location.href='home.php'\" >Home</button>\n";
print "<button id='new_button' onclick='cc_new_button_click()' >New</button>\n";
print "<button id='save_button' onclick='cc_save_button_click()' >Save</button>\n";
print "<button id='cancel_button' onclick='cc_cancel_button_click()' >Cancel</button>\n";
print "<button onclick=\"window.location.href='logout.php'\" >Logout</button>\n";
print "<br><br>\n";

print "<table id='form_table' border=1>\n";
print "<tr>\n";
print "  <th>Server</th>\n";
print "  <td>\n";
print "  <select id='server_select' style='display:table-cell; width:100%' >\n";
foreach($servers as $server){
  print "    <option selected value=".$server[0].">".$server[1]."</option>\n";
}
print "  </select>\n";
print "  </td>\n";
print "</tr>\n";
print "<tr>\n";
print "  <th>Channel Name</th>\n";
print "  <td><input id='input_channel_name' style='display:table-cell; width:100%' /></td>\n";
print "</tr>\n";
print "<tr>\n";
print "  <th>Channel Type</th>\n";
print "  <td>\n";
print "  <select id='channel_type_select' style='display:table-cell; width:100%' >\n";
print "    <option selected value=2>".Twitter."</option>\n";
print "  </select>\n";
print "  </td>\n";
print "</tr>\n";
print "</table>\n";
print "<br><br>\n";

if(count($channels)){
  print "<table border=1>\n";
  print "  <tr><th colspan=4><b>Custom Channels</b></th></tr>\n";
  print "  <tr>\n";
  print "    <th>Server Name</th>\n";
  print "    <th>Channel Name</th>\n";
  print "    <th>Channel Type</th>\n";
  print "    <th>Screen Name</th>\n";
  print "  </tr>\n";
  foreach($channels as $channel) {
    print "  <tr>\n";
    print "    <td>$channel[0]</td>\n";
    print "    <td>$channel[1]</td>\n";
    print "    <td>Twitter</td>\n";
    print "    <td>$channel[3]</td>\n";
    print "  </tr>\n";
  }
  print "</table>\n";
}

?>

<script>
$('#form_table').toggle(false)
$('#save_button').toggle(false)
$('#cancel_button').toggle(false)

function cc_new_button_click(){
  $('#form_table').toggle(true)
  $('#new_button').toggle(false)
  $('#save_button').toggle(true)
  $('#cancel_button').toggle(true)
}

function cc_cancel_button_click(){
  $('#form_table').toggle(false)
  $('#new_button').toggle(true)
  $('#save_button').toggle(false)
  $('#cancel_button').toggle(false)
  $('#input_channel_name').val("")
}

function cc_save_button_click(){
  if($('#input_channel_name').val()==''){
    alert("Channel Name may not be blank!")
    return
  }
  if(confirm("You will now be redirected to Twitter to authenticate your account"))
    location.href="twitter_login.php?guild_id="+$('#server_select').val()+"&channel_name="+$('#input_channel_name').val()
}

setInputFilter(document.getElementById("input_channel_name"), function(value) {
  return /^\S*$/.test(value);
});
</script>
