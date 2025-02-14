import logging
import os
import pyodbc
from azure.identity.aio import DefaultAzureCredential
import asyncio
import struct
import pandas as pd
import csv
import io
from semantic_kernel.functions.kernel_function_decorator import kernel_function

class SQL:
    """SQL query engine."""    
    def __init__(self):
        self.isOpen = False
        self.connection = None
    
    @kernel_function(description="Open db connection.")    
    async def open(self):
        try:
            token_resp = await DefaultAzureCredential().get_token("https://database.windows.net/.default")
            access_token = token_resp.token
            if not access_token:
                raise Exception("Could not obtain access token")
            server_name = os.environ["DB_SERVER"]
            if not server_name:
                raise Exception("DB_SERVER environment variable is not set")
            db_name = os.environ["DB_NAME"]
            if not db_name:
                raise Exception("DB_NAME environment variable is not set")
            connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={db_name};'
            SQL_COPT_SS_ACCESS_TOKEN = 1256
            exptoken = b'';
            for i in bytes(access_token, "UTF-8"):
                exptoken += bytes({i})
                exptoken += bytes(1)
            tokenstruct = struct.pack("=i", len(exptoken)) + exptoken;
            self.connection = pyodbc.connect(connection_string, attrs_before = { SQL_COPT_SS_ACCESS_TOKEN:tokenstruct })
            self.isOpen = True
            logging.info("Database connection opened.")
        except pyodbc.Error as e:
            logging.error(f"Error opening database connection: {e}")
            self.isOpen = False
            
    @kernel_function(description="Closes db connection.")
    async def close(self):
        if self.connection:
            self.connection.close()
            self.isOpen = False
            logging.info("Database connection closed.")
    
    @kernel_function(description="Executes a query.")        
    def execute(self, query):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()   
            return list_to_csv(rows)
        except pyodbc.Error as e: 
            return e.args[1] 
    
def list_to_csv(data: list):
    """
    Convert a list of lists to a csv string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue().strip()          

async def main() -> None:
    sql = SQL()
    await sql.open()
    print(sql.isOpen)
    d = sql.execute("SELECT TOP 3 FirstName, LastName FROM SalesLT.Customer")
    if isinstance(d, str):
        print(d)
    else:
        resp = list_to_csv(d)
        print(resp)
        # df = pd.DataFrame.from_records(d)
        # print(df)
    await sql.close()
    print(sql.isOpen)
    
if __name__ == "__main__":
    asyncio.run(main())