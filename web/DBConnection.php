<?php 

class DBConnection {
  var $user_name;
  var $password;
  var $database_name;
  var $result;
  var $connection;
  var $output;
  var $db;
   
  function DBConnection(){
  } //DBConnection

  function connect(){
    include "settings.inc";
    $this->connection = new mysqli("localhost", $db_user, $db_pass, $db_name);
    return $this->connection;
  } //connect

  function close(){
    $this->connection->close();
  } //close

   /*
  function query($SQL) {
    // print "<debug>$SQL</debug>\n";
    $_SESSION['sql_count']++;
    $result = $this->connection->query($SQL);
    return $result;
  } //query

   function set_query($SQL) {
      $SQL = ereg_replace("table", "table if not exists", $SQL);
      $result = @mysql_db_query($this->database_name, $SQL, $this->connection);
      unset ($SQL);
      return $result;
   }//set_query

   function insert_id() {
      return mysql_insert_id();
   }

   function fetch_row($result){
      $output = @mysql_fetch_row($result);
      unset($result);
      return $output;
   }//fetch_row

   function next_row($result){
      $output = @mysql_fetch_row($result);
      unset($result);
      return $output;
   }//next_row


  function num_rows($result){
    return mysqli_num_rows($result);
  } //num_row


   function error(){
      $output = @mysql_error();
      return $output;
   }//error

   function free_result($result){
      @mysql_free_result($result);
   }

 */
}//class
?>
