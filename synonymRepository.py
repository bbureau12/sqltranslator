import sqlite3
import logging
logging.basicConfig(level=logging.INFO)

class SynonymRepository:
    def __init__(self, connectionString):
        self.connectionString = connectionString

    def getSynonymMap(self):
        try:
            with sqlite3.connect(self.connectionString) as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT 
                        ts.table_name AS tableName,
                        ts.synonym AS tableSynonym,
                        cs.column_name AS columnName,
                        cs.synonym AS columnSynonym
                    FROM Table_Synonyms ts
                    LEFT JOIN Column_Synonyms cs
                    ON ts.table_name = cs.table_name
                    ORDER BY ts.table_name
                """)
                rows = c.fetchall()
                if not rows:
                    return []

                # Build the structured synonym map
                result = {}
                for tableName, tableSynonym, columnName, columnSynonym in rows:
                    if tableName not in result:
                        result[tableName] = {
                            "tableName": tableName,
                            "aliases": set(),
                            "columns": {}
                        }
                    result[tableName]["aliases"].add(tableSynonym)
                    if columnName:
                        if columnName not in result[tableName]["columns"]:
                            result[tableName]["columns"][columnName] = set()
                        result[tableName]["columns"][columnName].add(columnSynonym)

                # Convert sets to lists and format columns into list of dicts
                output = []
                for table in result.values():
                    formatted_columns = [
                        {"columnName": col, "synonym": list(syns)}
                        for col, syns in table["columns"].items()
                    ]
                    output.append({
                        "tableName": table["tableName"],
                        "aliases": list(table["aliases"]),
                        "columns": formatted_columns
                    })

                return output
        except sqlite3.Error as e:
            logging.error("Error building synonym map: %s", e)
            return {"error": str(e)}