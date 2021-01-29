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

function create_message(){
  if($('#delivery_time').val()==''){ alert('Delivery Time is required!'); return; }
  if($('#content').val()==''){ alert('Message content is required!'); return; }
  myRequest = new Request("create_message_response.php");
  data = new FormData()
  data.append('msg_id', $('#msg_id').text())
  data.append('server_id', $('#server').val())
  data.append('channel_id', $('#channel').val())
  data.append('delivery_time', $('#delivery_time').val())
  data.append('description', $('#description').val())
  data.append('content', $('#content').val())
  fetch(myRequest ,{
    method: 'POST',
    body: data,
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    location.href='message.php?id='+$('#msg_id').text()
  })
;}

function update_channel_select(){
	  var server = $('#server').find(":selected").text();
	  var channel_select = $('#channel');
	  channel_select.empty();
	  for(var j = 0 ; j < channels[server].length ; j++){
		      $('#channel').append("<option value='"+channels[server][j][0]+"'>"+channels[server][j][1]+"</option>")
		    }
}
