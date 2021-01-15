#!/usr/bin/env python
import settings
import mysql.connector

def db_connect():
    return mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
            )

def db_get_rows(sql, **kwargs):
    mydb = db_connect()

    mycursor = mydb.cursor()

    mycursor.execute(sql, tuple(kwargs.values()))

    rows =  mycursor.fetchall()

    mycursor.close()
    mydb.disconnect()

    return rows

def get_messages():
    return db_get_rows("select * from messages")
