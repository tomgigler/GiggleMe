function load_message_page(action, repeat_until){
  update_channel_select();
  update_from_template_select();
  $('#repeats_num').hide();
  $('#skip_if_num').hide();
  $('#skip_if_row').hide()
  $('#repeat_until_datetime').hide();
  if(action=='' && $('#display_repeats_cell').text()==''){
    $('#repeats_row').hide();
    $('#repeat_until_row').hide();
  }
  if(repeat_until==''){
    $('#repeat_until_row').hide();
  }
}

function server_select_updated(){
  update_channel_select();
  update_from_template_select();
}

function edit_button_click(){
  $('#server_select').val(guild_id);
  server_select_updated();
  $('.display_element').toggle(false);
  $('.edit_element').toggle(true);
  $('#repeats_row').toggle(true);
  $('#channel_select').val(channel_id);
  $('#delivery_time').val(delivery_time_java_format);
  $('#description').val($('#display_description_cell').text());
  $('#edit_content').val($('#display_content_pre').text());
  if($('#message_type_select').val() == 'template'){
    $('#repeats_row').toggle(false);
  } else {
    if(repeat_frequency){
      $('#repeats_select').val(repeat_frequency);
      if(repeat_frequency_num){
        $('#repeats_num').val(repeat_frequency_num);
        $('#repeats_num').toggle(true);
      }
      $('#skip_if_row').toggle(true);
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
  if(creating_new_message) location.href='home.php';
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
    data['channel_id'] = $('#channel_select').val();
    data['description'] = $('#description').val();
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

  }

  $.ajax({
    type: "POST",
    url: requestURL,
    data: data,
    success: function(response){
      creating_new_message = false;
      var message = JSON.parse(response);
      $('#message_type_row').toggle(false);
      $('#display_server_cell').text(message.server);
      $('#display_channel_cell').text(message.channel);
      $('#display_delivery_time_cell').text(message.delivery_time);
      if(message.repeats==''){
        $('#repeats_row').toggle(false)
        $('#repeat_until_row').toggle(false)
      } else {
        $('#repeats_row').toggle(true)
        $('#display_repeats_cell').text(message.repeats)
        if(message.repeat_until==''){
          $('#repeat_until_row').toggle(false)
	} else {
          $('#repeat_until_row').toggle(true)
          $('#display_repeat_until_cell').text(message.repeat_until)
	}
      }
      $('#display_description_cell').text(message.description);
      $('#display_content_pre').html(message.content)
      $('.display_element').toggle(true);
      $('.edit_element').toggle(false);
      $('#skip_if_row').toggle(false)
      $('#from_template_row').toggle(false)
      guild_id = message.guild_id;
      channel_id = message.channel_id;
      delivery_time_java_format = message.delivery_time_java_format;
      repeat_until_java_format = message.repeat_until_java_format;
      repeat_frequency = message.repeat_frequency;
      repeat_frequency_num = message.repeat_frequency_num;
      repeat_skip_if = message.repeat_skip_if;
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

function update_content_from_template(){
  var msg_id = $('#from_template').find(":selected").text();
  if(msg_id != 'None'){
    update_content_by_message_id(msg_id);
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
      $('#from_template').append("<option value='"+templates[server][j]+"'>"+templates[server][j]+"</option>");
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
    $('#skip_if_row').toggle(false);
    $('#repeat_until_row').toggle(false);
    $('#description_row').toggle(true);
    $('#edit_content').prop('maxlength','1992');
    $('#edit_content').val('')
  } else if($('#message_type_select').find(":selected").val() == 'message'){
    $('#new_id_row').toggle(true);
    $('#channel_row').toggle(true);
    $('#id_table_header').text('Message ID');
    $('#delivery_time_row').toggle(true);
    $('#from_template_row').toggle(true);
    $('#repeats_row').toggle(true);
    if($('#repeats_select').val()!='None'){
      $('#skip_if_row').toggle(true);
      $('#repeat_until_row').toggle(true);
    }
    $('#description_row').toggle(true);
    $('#edit_content').prop('maxlength','1992');
    $('#edit_content').val('')
  } else if($('#message_type_select').find(":selected").val() == 'batch'){
    $('#message_id_row').toggle(false);
    $('#channel_row').toggle(false);
    $('#delivery_time_row').toggle(false);
    $('#from_template_row').toggle(false);
    $('#repeats_row').toggle(false);
    $('#skip_if_row').toggle(false);
    $('#repeat_until_row').toggle(false);
    $('#description_row').toggle(false);
    $('#edit_content').prop('maxlength','50000');
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
