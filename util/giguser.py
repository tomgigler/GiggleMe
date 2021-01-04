#!/usr/bin/env python
import gigdb

users = {}

class User:
    def __init__(self, name, timezone, last_active, last_message_id=None):
        self.name = name
        self.timezone = timezone
        self.last_active =
        self.last_message_id = last_message_id

    def set_last_active(self, user_id, last_active):
        mydb = gigdb.db_connect()

        sql = "UPDATE users SET last_active = %s WHERE user = %s"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (last_active, user_id))
        self.last_active = last_active
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

    def set_last_message(self, user_id, message_id):
        mydb = gigdb.db_connect()

        sql = "UPDATE users SET last_message_id = %s WHERE user = %s"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (message_id, user_id))
        self.last_message_id = message_id
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

    def save(self, user_id):
        mydb = gigdb.db_connect()

        sql = "INSERT into users values ( %s, %s, %s, %s )"

        mycursor = mydb.cursor()
        mycursor.execute(sql, (user_id, self.name, self.timezone, self.last_message_id))
        mydb.commit()
        mycursor.close()
        mydb.disconnect()

def load_users():
    mydb = gigdb.db_connect()

    mycursor = mydb.cursor()

    mycursor.execute("select * from users")
    for user in mycursor.fetchall():
        users[user[0]] = User(user[1], user[2], user[3], user[4])

    mycursor.close()
    mydb.disconnect()

