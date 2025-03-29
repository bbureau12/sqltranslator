import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

class SqlRepository:
    def init(self, connectionString):
        self.connectionString = connectionString
    def __init__(self, connectionString):
        self.connectionString = connectionString

    def getSchema(self):
        try:
            with sqlite3.connect(self.connectionString) as conn:
                c = conn.cursor()
                c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                schemas = c.fetchall()
                schema_str = "\n\n".join([schema[0] for schema in schemas if schema[0] is not None])
                return schema_str
        except sqlite3.Error as e:
            logging.error("Error retrieving schema: %s", e)
            return f"Error retrieving schema: {e}"

    def getSqlResult(self, command, params=None):
        try:
            with sqlite3.connect(self.connectionString) as conn:
                c = conn.cursor()
                if params:
                    c.execute(command, params)
                else:
                    c.execute(command)

                rows = c.fetchall()
                if not rows:
                    return []

                column_names = [desc[0] for desc in c.description]
                return [dict(zip(column_names, row)) for row in rows]

        except sqlite3.Error as e:
            logging.error("SQL Execution Error: %s", e)
            return {"error": str(e)}

    def listTables(self):
        try:
            with sqlite3.connect(self.connectionString) as conn:
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                return [row[0] for row in c.fetchall()]
        except sqlite3.Error as e:
            logging.error("Error listing tables: %s", e)
            return {"error": str(e)}

    def describeTable(self, tableName):
        try:
            with sqlite3.connect(self.connectionString) as conn:
                c = conn.cursor()
                c.execute(f"PRAGMA table_info({tableName})")
                return c.fetchall()
        except sqlite3.Error as e:
            logging.error("Error describing table %s: %s", tableName, e)
            return {"error": str(e)}
# Example usage:
connectionString = "users.db"
retriever = SqlRepository(connectionString)
tableName = "user"
print("\n--- Schema ---")
print(retriever.getSchema())

print("\n--- Tables ---")
print(retriever.listTables())

print("\n--- Describe 'user' Table ---")
print(retriever.describeTable("user"))