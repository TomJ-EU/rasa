# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import mysql.connector

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello world.")
        userid = tracker.sender_id

        return []

class ActionSaveToDb(Action):

    def name(self) -> Text:
        return "action_save_to_db"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        conn = mysql.connector.connect(
            user='root',
            password='password',
            host='mysql',
            port='3306',
            database='db'
        )
        cur = conn.cursor(prepared=True)
        query = "INSERT INTO names VALUES(%s, %s)"
        queryMatch = [tracker.get_slot("first_name"), tracker.get_slot("last_name")]
        # cur.execute("INSERT INTO names VALUES(?, ?)", (tracker.get_slot("first_name"), tracker.get_slot("last_name")))
        cur.execute(query, queryMatch)
        conn.commit()
        conn.close()

        dispatcher.utter_message(text="Data saved.")

        return []

class GetAllFromDb(Action):

    def name(self) -> Text:
        return "action_get_all_from_db"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        conn = mysql.connector.connect(
            user='root',
            password='password',
            host='db',
            port='3306',
            database='db'
        )
        cur = conn.cursor()
        # cur.execute("CREATE TABLE names(first_name TEXT, last_name TEXT)")
        # cur.execute("INSERT INTO names(first_name, last_name) VALUES('tom', 'jacobs')")
        # cur.execute('SHOW TABLES')
        # stuff = cur.fetchall()
        # conn.commit()
        # print('stuff:')
        # print(stuff)

        cur.execute('SELECT * FROM names')

        stuff = cur.fetchall()

        conn.commit()

        dispatcher.utter_message(text="Data received")

        for row in stuff:
            print(row)

        conn.close()

        return []
