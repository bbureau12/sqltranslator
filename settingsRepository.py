from enum import Enum
import json
import os
import random
import sqlite3

class PrivateSettings(Enum):
    DataBaseOverride = 1

class SettingRepository:
    def __init__(self):
        self.name=random.randint(1, 100000)
        self.connectionString = self._getDbLocation()

    def getJsonSetting(self, key: str):
        current_directory = os.getcwd()
        files_in_directory = [f for f in os.listdir(current_directory) if os.path.isfile(os.path.join(current_directory, f))]

        print("Files in the current directory:")
        for file in files_in_directory:
            print(file)
        with open('settings.json', 'r') as file:
            settings_data = json.load(file)
            return settings_data.get(key)

    def getSetting(self, key):
        all_settings = self.getAllSettings()
        result =   [d for d in all_settings if d.get('Key') == key]
        if result is None:
            return None
        return result[0].get('Value')
    
    def getAllSettings(self):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        command="Select * from Settings"
        c.execute(command)
        rows=c.fetchall()
        if rows is None or len(rows) == 0:
            conn.close()
            return []
        column_names = [desc[0] for desc in c.description]
        result = [dict(zip(column_names, row)) for row in rows]
        conn.close()
        return result
    
    def updateSettings(self, settings):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        for setting in settings:
            command="UPDATE Settings SET Value = ? WHERE KEY = ?"
            key = setting.get('Key')
            value = setting.get('Value')
            c.execute(command, (value, key))
        conn.commit()
        conn.close()
        return

    
    def _getDbLocation(self):
        return self.getJsonSetting('dbLocation')
    
    # Print or use the setting as needed

