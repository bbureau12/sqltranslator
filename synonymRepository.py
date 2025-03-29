import sqlite3

class SynonymRepository:
    def __init__(self, connectionString):
        self.connectionString = connectionString

    def getSynonymsForTable(self, tableName, isPlural):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        command = "SELECT synonym FROM Table_Synonyms WHERE table_name = ? and is_plural = ?"
        c.execute(command, (tableName, isPlural,))
        
        rows = c.fetchall()
        conn.close()
        if rows is None or len(rows) == 0:
            return []
        result = [row[0] for row in rows]
        
        return result
    
    def getAllTableSynonyms(self):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        command = "SELECT * FROM Table_Synonyms"
        c.execute(command)
        
        rows = c.fetchall()
        conn.close()
        if rows is None or len(rows) == 0:
            return []
        column_names = [desc[0] for desc in c.description]
        result = [dict(zip(column_names, row)) for row in rows]
        conn.close()
        return result

    def getAllColumnSynonyms(self, tableName):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        command = "SELECT * FROM Column_Synonyms WHERE table_name = ?"
        c.execute(command, (tableName,))
        
        rows = c.fetchall()
        if rows is None or len(rows) == 0:
            return []
        column_names = [desc[0] for desc in c.description]
        result = [dict(zip(column_names, row)) for row in rows]
        conn.close()
        return result
    
    def getSynonymsForColumn(self, tableName, columnName):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        command = "SELECT synonym FROM Column_Synonyms WHERE table_name = ? AND column_name = ?"
        c.execute(command, (tableName, columnName,))
        
        rows = c.fetchall()
        conn.close()
        if rows is None or len(rows) == 0:
            return []
        result = [row[0] for row in rows]
        
        return result

    def getAllImperatives(self):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        command = "SELECT phrase FROM Imperatives"
        c.execute(command)
        
        rows = c.fetchall()
        conn.close()
        if rows is None or len(rows) == 0:
            return []
        result = [row[0] for row in rows]
        
        return result
    
    def getExtraneousWords(self):
        conn = sqlite3.connect(self.connectionString)
        c = conn.cursor()
        command = "SELECT word FROM ExtraneousWords"
        c.execute(command)
        
        rows = c.fetchall()
        conn.close()
        if rows is None or len(rows) == 0:
            return []
        result = [row[0] for row in rows]
        
        return result

# Example usage:
connectionString = "users.db"
retriever = SynonymRepository(connectionString)
tableName = "user"