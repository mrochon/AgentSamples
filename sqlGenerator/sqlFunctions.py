import csv
import io

columns = {
    "Address": [["AddressID", "AddressLine1", "AddressLine2", "City", "StateProvinceID", "PostalCode", "rowguid", "ModifiedDate"]],
    "Customer": [["CustomerID", "PersonID", "FirstName", "LastName", "AccountNumber", "rowguid", "ModifiedDate"]],
    "CustomerAddress": [["CustomerID", "AddressID", "AddressTypeID", "rowguid", "ModifiedDate"]],
    "Product": [["ProductID", "Name", "ProductNumber", "MakeFlag", "FinishedGoodsFlag", "Color", "SafetyStockLevel", "ReorderPoint", "StandardCost", "ListPrice", "Size", "SizeUnitMeasureCode", "WeightUnitMeasureCode", "Weight", "DaysToManufacture", "ProductLine", "Class", "Style", "ProductSubcategoryID", "ProductModelID", "SellStartDate", "SellEndDate", "DiscontinuedDate", "rowguid", "ModifiedDate"]],
    "ProductCategory": [["ProductCategoryID", "Name", "rowguid", "ModifiedDate"]],
    "ProductDescription": [["ProductDescriptionID", "Description", "rowguid", "ModifiedDate"]],
    "ProductModel": [["ProductModelID", "Name", "CatalogDescription", "rowguid", "ModifiedDate"]],
    "ProductModelProductDescription": [["ProductModelID", "ProductDescriptionID", "Culture", "rowguid", "ModifiedDate"]]
}

def list_to_csv(data: list):
    """
    Convert a list of lists to a csv string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue().strip()

def get_tables():
    """
    Get list of tables for the database.
    """
    tables = [["Address", "Customer", "CustomerAddress", "Product", "ProductCategory", "ProductDescription", "ProductModel", "ProductModelProductDescription"]]
    return list_to_csv(tables)
    
def get_columns(tables: str):
    """
    Get list of columns for the tables in the database.
    """
    print(f"Getting columns for tables: {tables}")
    tabs = tables.split(',')
    resp = ""
    for table in tabs:
        if table not in columns:
            print(f"Table {table} not found")
            tabColumns = f"Table {table} not found"
        else:
            tabColumns = f"Table {table} contains the following columns: {list_to_csv(columns[table])}"
        resp += tabColumns + "\n"
    return resp

def get_tables_for_column(columnName: str):
    """
    Get list of tables containing a column with this or similar name.
    """
    print(f"Getting tables for column: {columnName}")
    resp = ""
    for table, cols in columns.items():
        for col in cols[0]:
            if columnName.lower() in col.lower():
                resp += f"Table {table} contains column {col}\n"
    return resp

def try_query(query: str):
    """
    Try running an SQL query and return the first 10 rows of the result or an error message.
    """
    print(f"Trying query: {query}")
    results = [
        ["John", "Smith", "123 Main St", "Springfield", "IL", "62701"],
        ["Alex", "Johnson", "456 Elm St", "Chicago", "IL", "60601"],
    ]
    return f"Query is valid. Sample data.\n\n{list_to_csv([results])}"
    # return("Erroe: lastName is not a valid column name. Use lower case letters only")

# print(get_columns("Customer,Product"))
# print(try_query("select all"))