function load_message_page(action, repeat_until){
  update_channel_select();
  update_from_template_select();
  $('#repeats_num').hide();
  $('#skip_if_num').hide();
  $('#skip_if_row').hide();
  $('#repeat_until_datetime').hide();
  $('#special_handling_row').hide();
  if(action=='' && $('#display_repeats_cell').text()==''){
    $('#repeats_row').hide();
    $('#repeat_until_row').hide();
  }
  if(repeat_until==''){
    $('#repeat_until_row').hide();
  }
  if(action=='create' || $('#display_special_handling_cell').text()=='True' || $('#special_handling_header').text() == 'Wildcard'){
    $('#special_handling_row').toggle(true);
  }
}

function server_select_updated(){
  update_channel_select();
  update_from_template_select();
}

function show_as_command_click(){
  msg_id = $('#message_id_cell').text()
  $.ajax({
    url: "get_message_by_id.php",
    data: {
      msg_id: msg_id
    },
    success: function( response ) {
      var message = JSON.parse(response);
      if($('#show_as_command_chkbx').prop('checked'))
        $('#display_content_pre').text(message.command+"\n"+message.content);
      else
        $('#display_content_pre').text(message.content);
    }
  });
}

function edit_button_click(){
  $('#server_select').val(guild_id);
  server_select_updated();
  $('.display_element').toggle(false);
  $('.edit_element').toggle(true);
  $('#channel_select').val(channel_id);
  $('#delivery_time').val(delivery_time_java_format);
  $('#description').val($('#display_description_cell').text());
  if($('#message_type_select').val() == 'message'){
    $('#repeats_row').toggle(true);
    if($('#special_handling_header').text() == 'Pin' || $('#special_handling_header').text() == 'Wildcard'){
      $('#special_handling_row').toggle(true);
      if($('#display_special_handling_cell').text()=='True') $('#skip_if_checkbox').prop('checked', true)
      else $('#pin_message_checkbox').prop('checked', false)
    }
    else
      $('#special_handling_row').toggle(false);
    if(repeat_frequency){
      $('#repeats_select').val(repeat_frequency);
      if(repeat_frequency_num){
        $('#repeats_num').val(repeat_frequency_num);
        $('#repeats_num').toggle(true);
      }
      $('#skip_if_num').val(repeat_skip_if);
      if(repeat_skip_if){
        $('#skip_if_checkbox').prop('checked', true)
        $('#skip_if_num').toggle(true);
      } else {
        $('#skip_if_checkbox').prop('checked', false)
        $('#skip_if_num').toggle(false);
      }
      $('#repeat_until_row').toggle(true);
      $('#repeat_until_datetime').val(repeat_until_java_format);
      if(repeat_until_java_format){
        $('#repeat_until_checkbox').prop('checked', true);
        $('#repeat_until_datetime').toggle(true);
      } else {
        $('#repeat_until_checkbox').prop('checked', false);
        $('#repeat_until_datetime').toggle(false);
      }
    } else {
      $('#repeats_select').val('None');
      $('#repeats_num').val('');
      $('#repeats_num').toggle(false);
      $('#skip_if_num').val(repeat_skip_if);
      $('#skip_if_checkbox').prop('checked', false)
      $('#skip_if_num').toggle(false);
      $('#repeat_until_datetime').val(repeat_until_java_format);
      $('#repeat_until_checkbox').prop('checked', false);
      $('#repeat_until_datetime').toggle(false);
    }
  }
}

function cancel_button_click(){
  if(creating_new_message) window.location.href='home.php';
  else {
    $('.display_element').toggle(true);
    $('.edit_element').toggle(false);
    $('#skip_if_row').hide()
    if(!$('#display_repeats_cell').text()){
      $('#repeats_row').toggle(false);
      $('#repeat_until_row').toggle(false);
    }
    if($('#display_repeat_until_cell').text()){
      $('#repeat_until_row').toggle(true);
    } else {
      $('#repeat_until_row').toggle(false);
    }
    if(!$('#pin_message_checkbox').prop('checked')){
      $('#special_handling_row').toggle(false);
    }
    if($('#special_handling_header').text() != 'Pin' || $('#special_handling_header').text() != 'Wildcard'){
      $('#special_handling_row').toggle(true);
    }
  }
}

function deleteMessage(msg_id, msg_type){
  if(!confirm("Delete " + msg_type + " " + msg_id + "?")) return;
  myRequest = new Request("delete_message.php");
  data = new FormData();
  data.append('msg_id', msg_id);
  fetch(myRequest ,{
    method: 'POST',
    body: data
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    location.href='home.php';
  });
}

function save_message(){
  if($('#edit_content').val()==''){ alert('Message content is required!'); return; }

  var requestURL = "save_message_response.php";
  var data = {};
  data['message_type'] = $('#message_type_select').find(":selected").val();
  data['server_id'] = $('#server_select').val();
  data['content'] = $('#edit_content').val();

  if($('#message_type_select').find(":selected").val() !== 'batch'){
    data['message_id'] = $('#message_id_cell').text();
    if($('#message_type_select').find(":selected").val() == 'autoreply'){
      if($('#trigger_text').val()==''){
        alert('Trigger is required!'); return;
      }
      data['repeats'] = $('#trigger_text').val();
    }
    data['channel_id'] = $('#channel_select').val();
    data['description'] = $('#description').val();
    if($('#special_handling_header').text() == 'Wildcard')
      if($('#pin_message_checkbox').prop('checked')) data['pin_message'] = 1
      else data['pin_message'] = 0
  }

  if($('#message_type_select').find(":selected").val() == 'message'){
    if($('#delivery_time').val()==''){ alert('Delivery Time is required!'); return; }
    repeats_str = '';
    repeat_until = '';
    if($('#repeats_select').val()!='None'){
      repeats_str += $('#repeats_select').val();
      if($('#repeats_select').val()=='minutes' || $('#repeats_select').val()=='hours'){
        if($('#repeats_num').val()==''){
          alert('A number of ' + $('#repeats_select').val() + ' is required for Repeats!');
          return;
        }
        if($('#repeats_num').val()==0){
          alert('Number of ' + $('#repeats_select').val() + ' must be greater than 0!');
          return;
        }
        repeats_str += ':' + $('#repeats_num').val();
      }
      if($('#skip_if_checkbox').prop('checked')){
        if($('#skip_if_num').val() == ''){
          alert('A value for Skip if is required!');
          return;
        }
        repeats_str += ';skip_if=' + $('#skip_if_num').val();
      }
      if($('#repeat_until_checkbox').prop('checked')){
        if($('#repeat_until_datetime').val() == ''){
          alert('A date is required for Repeat Until!');
          return;
        }
        repeat_until = $('#repeat_until_datetime').val();
      }
    }
    data['delivery_time'] = $('#delivery_time').val();
    data['repeats'] = repeats_str;
    data['repeat_until'] = repeat_until;
    if($('#special_handling_header').text() == 'Pin')
      if($('#pin_message_checkbox').prop('checked')) data['pin_message'] = 1
      else data['pin_message'] = 0
    if($('#special_handling_header').text() == 'Set Topic')
      data['pin_message'] = 2
    if($('#special_handling_header').text() == 'Set Channel Name')
      data['pin_message'] = 3
  }

  $.ajax({
    type: "POST",
    url: requestURL,
    data: data,
    success: function(response){
      if($('#message_type_select').find(":selected").val() == 'batch'){
        alert(response);
        $('#edit_content').val("");
      } else {
        creating_new_message = false;
        var message = JSON.parse(response);
        $('#message_type_row').toggle(false);
        $('#display_server_cell').text(message.server);
        $('#display_channel_cell').text(message.channel);
        $('#display_delivery_time_cell').text(message.delivery_time_format);
        if(!message.repeats || $('#message_type_select').find(":selected").val() == 'autoreply'){
          $('#repeats_row').toggle(false)
          $('#repeat_until_row').toggle(false)
          if($('#message_type_select').find(":selected").val() == 'autoreply'){
            $('#display_trigger_cell').text(message.repeats);
	  }
        } else {
          $('#repeats_row').toggle(true)
          $('#display_repeats_cell').text(message.repeats)
          if(!message.repeat_until){
            $('#repeat_until_row').toggle(false)
          } else {
            $('#repeat_until_row').toggle(true)
            $('#display_repeat_until_cell').text(message.repeat_until_format)
	  }
        }
        $('#display_description_cell').text(message.description);
        $('#display_content_pre').html(message.content)
        $('.display_element').toggle(true);
        $('.edit_element').toggle(false);
        $('#skip_if_row').toggle(false)
        $('#from_template_row').toggle(false)
        $('#show_as_command_chkbx').prop('checked', false)
        guild_id = message.guild_id;
        channel_id = message.delivery_channel_id;
        delivery_time_java_format = message.delivery_time_java_format;
        repeat_until_java_format = message.repeat_until_java_format;
        repeat_frequency = message.repeat_frequency;
        repeat_frequency_num = message.repeat_frequency_num;
        repeat_skip_if = message.repeat_skip_if;
        if(message.special_handling){
	  $('#display_special_handling_cell').text('True')
          $('#special_handling_row').toggle(true);
	} else if($('#message_type_select').find(":selected").val() == 'autoreply'){
	  $('#display_special_handling_cell').text('False')
          $('#special_handling_row').toggle(true);
        } else {
          $('#special_handling_row').toggle(false);
	  $('#display_special_handling_cell').text('False')
	}
      }
    },
    error: function(error){ alert(error.responseText) },
  });
}

function update_content_by_message_id(msg_id){
  $.ajax({
    url: "get_message_content.php",
    data: {
      msg_id: msg_id
    },
    success: function( result ) {
      $('#edit_content').val(result);
    }
  });
}

function update_channel_by_message_id(msg_id){
  $.ajax({
    url: "get_message_channel_id.php",
    data: {
      msg_id: msg_id
    },
    success: function( result ) {
      $('#channel_select').val(result);
    }
  });
}

function update_content_from_template(){
  var msg_id = $('#from_template').find(":selected").val();
  if(msg_id != 'None'){
    update_content_by_message_id(msg_id);
    update_channel_by_message_id(msg_id);
  }
}

function toggle_skip_if_num(){
  $('#skip_if_num').toggle($('#skip_if_checkbox').prop('checked'));
}

function toggle_repeat_until_datetime(){
  $('#repeat_until_datetime').toggle($('#repeat_until_checkbox').prop('checked'));
}

function update_repeats_select(){
  $('#repeats_num').toggle($('#repeats_select').find(":selected").text() == 'minutes' || $('#repeats_select').find(":selected").text() == 'hours');
  $('#skip_if_row').toggle($('#repeats_select').find(":selected").text() != 'None');
  $('#repeat_until_row').toggle($('#repeats_select').find(":selected").text() != 'None');
  if($('#repeats_select').val()=='None'){
    $('#skip_if_checkbox').prop('checked', false);
    $('#repeat_until_checkbox').prop('checked', false);
    toggle_skip_if_num();
    toggle_repeat_until_datetime();
  }
}

function update_channel_select(){
  var server = $('#server_select').val();
  var channel_select = $('#channel_select');
  channel_select.empty();
  for(var j = 0 ; j < channels[server].length ; j++){
      $('#channel_select').append("<option value='"+channels[server][j][0]+"'>"+channels[server][j][1]+"</option>");
  }
}

function update_from_template_select(){
  var server = $('#server_select').val();
  var from_template_select = $('#from_template');
  from_template_select.empty();
  for(var j = 0 ; j < templates[server].length ; j++){
      $('#from_template').append("<option value='"+templates[server][j][0]+"'>"+templates[server][j][0]+templates[server][j][1]+"</option>");
  }
}

function message_type_updated(){
  if($('#message_type_select').find(":selected").val() == 'template'){
    $('#message_id_row').toggle(true);
    $('#channel_row').toggle(true);
    $('#id_table_header').text('Template ID');
    $('#delivery_time_row').toggle(false);
    $('#from_template_row').toggle(false);
    $('#repeats_row').toggle(false);
    $('#trigger_row').toggle(false);
    $('#skip_if_row').toggle(false);
    $('#repeat_until_row').toggle(false);
    $('#special_handling_row').toggle(false);
    $('#pin_message_checkbox').prop('checked', false)
    $('#description_row').toggle(true);
    $('#edit_content').prop('maxlength','1992');
    $('#edit_content').val('')
  } else if($('#message_type_select').find(":selected").val() == 'message'){
    $('#new_id_row').toggle(true);
    $('#channel_row').toggle(true);
    $('#id_table_header').text('Message ID');
    $('#delivery_time_row').toggle(true);
    $('#from_template_row').toggle(true);
    $('#trigger_row').toggle(false);
    $('#repeats_row').toggle(true);
    if($('#repeats_select').val()!='None'){
      $('#skip_if_row').toggle(true);
      $('#repeat_until_row').toggle(true);
    }
    $('#special_handling_row').toggle(true);
    $('#pin_message_checkbox').prop('checked', false)
    $('#description_row').toggle(true);
    $('#edit_content').prop('maxlength','1992');
    $('#edit_content').val('')
    $('#special_handling_header').text('Pin')
  } else if($('#message_type_select').find(":selected").val() == 'batch'){
    $('#message_id_row').toggle(false);
    $('#channel_row').toggle(false);
    $('#delivery_time_row').toggle(false);
    $('#from_template_row').toggle(false);
    $('#repeats_row').toggle(false);
    $('#trigger_row').toggle(false);
    $('#skip_if_row').toggle(false);
    $('#repeat_until_row').toggle(false);
    $('#special_handling_row').toggle(false);
    $('#description_row').toggle(false);
    $('#edit_content').prop('maxlength','50000');
  } else if($('#message_type_select').find(":selected").val() == 'autoreply'){
    $('#message_id_row').toggle(true);
    $('#channel_row').toggle(false);
    $('#message_id_header_cell').text('AutoReply ID');
    $('#delivery_time_row').toggle(false);
    $('#from_template_row').toggle(false);
    $('#trigger_row').toggle(true);
    $('#repeats_row').toggle(false);
    $('#skip_if_row').toggle(false);
    $('#repeat_until_row').toggle(false);
    $('#special_handling_row').toggle(false);
    $('#pin_message_checkbox').prop('checked', false)
    $('#description_row').toggle(true);
    $('#edit_content').prop('maxlength','1992');
    $('#edit_content').val('')
    $('#special_handling_row').toggle(true);
    $('#special_handling_header').text('Wildcard')
  }
}

// Restricts input for the given textbox to the given inputFilter function.
function setInputFilter(textbox, inputFilter) {
  ["input", "keydown", "keyup", "mousedown", "mouseup", "select", "contextmenu", "drop"].forEach(function(event) {
    textbox.addEventListener(event, function() {
      if (inputFilter(this.value)) {
        this.oldValue = this.value;
        this.oldSelectionStart = this.selectionStart;
        this.oldSelectionEnd = this.selectionEnd;
      } else if (this.hasOwnProperty("oldValue")) {
        this.value = this.oldValue;
        this.setSelectionRange(this.oldSelectionStart, this.oldSelectionEnd);
      } else {
        this.value = "";
      }
    });
  });
}
