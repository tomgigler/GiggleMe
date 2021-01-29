function deleteMessage(msg_id, msg_type){
  if(!confirm("Delete " + msg_type + " " + msg_id)) return
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
