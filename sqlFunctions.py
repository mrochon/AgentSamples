import csv
import io

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
    tabs = tables.split(',')
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
    resp = ""
    for table in tabs:
        tabColumns = f"Table {table} contains the following columns: {list_to_csv(columns[table])}"
        resp += tabColumns + "\n"
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
    return list_to_csv([results])

# print(get_columns("Customer,Product"))
# print(try_query("select all"))