function deleteMessage(msg_id, msg_type){
  if(!confirm("Delete " + msg_type + " " + msg_id + "?")) return
  myRequest = new Request("delete_message.php");
  data = new FormData()
  data.append('msg_id', msg_id)
  fetch(myRequest ,{
    method: 'POST',
    body: data,
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    location.href='home.php'
  })
}

function edit_message(){
  if($('#content').val()==''){ alert('Message content is required!'); return; }

  data = new FormData()
  data.append('msg_id', $('#msg_id').text())
  data.append('server_id', $('#server').val())
  data.append('channel_id', $('#channel').val())
  data.append('content', $('#content').val())
  data.append('description', $('#description').val())

  if($('#delivery_time').val()==''){ alert('Delivery Time is required!'); return; }
  repeats_str = '';
  repeat_until = '';
  if(!is_template && $('#repeats_select').val()!='None'){
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
  if(!is_template){
    data.append('delivery_time', $('#delivery_time').val())
    data.append('repeats', repeats_str)
    data.append('repeat_until', repeat_until)
  }

  myRequest = new Request("edit_message_response.php");

  fetch(myRequest ,{
    method: 'POST',
    body: data,
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    if(is_template){
      location.href='template.php?id='+$('#msg_id').text()
    } else {
      location.href='message.php?id='+$('#msg_id').text()
    }
  });
}

function create_message(){
  if($('#content').val()==''){ alert('Message content is required!'); return; }

  data = new FormData()
  data.append('msg_id', $('#msg_id').text())
  data.append('server_id', $('#server').val())
  data.append('channel_id', $('#channel').val())
  data.append('content', $('#content').val())
  data.append('description', $('#description').val())

  if($('#msg_type_select').find(":selected").val() == 'message'){
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
    data.append('delivery_time', $('#delivery_time').val())
    data.append('repeats', repeats_str)
    data.append('repeat_until', repeat_until)

    myRequest = new Request("create_message_response.php");
  } else {
    myRequest = new Request("create_template_response.php");
  }

  fetch(myRequest ,{
    method: 'POST',
    body: data,
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    if($('#msg_type_select').find(":selected").val() == 'message'){
      location.href='message.php?id='+$('#msg_id').text()
    } else {
      location.href='template.php?id='+$('#msg_id').text()
    }
  });
}

function update_content_by_message_id(msg_id){
  $.ajax({
    url: "get_message_content.php",
    data: {
      msg_id: msg_id
    },
    success: function( result ) {
      $('#content').val(result);
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
  var server = $('#server').find(":selected").val();
  var channel_select = $('#channel');
  channel_select.empty();
  for(var j = 0 ; j < channels[server].length ; j++){
      $('#channel').append("<option value='"+channels[server][j][0]+"'>"+channels[server][j][1]+"</option>")
  }
}

function update_from_template_select(){
  var server = $('#server').find(":selected").val();
  var from_template_select = $('#from_template');
  from_template_select.empty();
  for(var j = 0 ; j < templates[server].length ; j++){
      $('#from_template').append("<option value='"+templates[server][j]+"'>"+templates[server][j]+"</option>")
  }
}

function message_type_updated(){
  if($('#msg_type_select').find(":selected").val() == 'template'){
    $('#id_table_header').text('Template ID');
    $('#delivery_time_row').toggle(false)
    $('#from_template_row').toggle(false)
    $('#repeats_row').toggle(false)
    $('#skip_if_row').toggle(false)
    $('#repeat_until_row').toggle(false)
  } else {
    $('#id_table_header').text('Message ID');
    $('#delivery_time_row').toggle(true)
    $('#from_template_row').toggle(true)
    $('#repeats_row').toggle(true)
    if($('#repeats_select').val()!='None'){
      $('#skip_if_row').toggle(true)
      $('#repeat_until_row').toggle(true)
    }
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
