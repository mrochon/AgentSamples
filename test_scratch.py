from helpers import function_to_schema
from sqlFunctions import get_tables, get_columns, try_query

x = function_to_schema(get_tables)
print(x)