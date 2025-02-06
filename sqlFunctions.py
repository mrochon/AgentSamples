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

def get_tables(dbName: str):
    """
    Get list of tables for the database.
    """
    tables = [["Address", "Customer", "CustomerAddress", "Product", "ProductCategory", "ProductDescription", "ProductModel", "ProductModelProductDescription"]]
    return list_to_csv(tables)
    
def get_columns(tables_csv: str):
    """
    Get list of columns for the tables in the database.
    """
    tables = tables_csv.split(',')
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
    selected_columns = {table: columns[table] for table in tables if table in columns}
    return list_to_csv(selected_columns[tables[0]])

def try_query(query: str):
    """
    Try running an SQL query and return the first 10 rows of the result or an error message.
    """
    results = [
        ["John", "Smith", "123 Main St", "Springfield", "IL", "62701"],
        ["Alex", "Johnson", "456 Elm St", "Chicago", "IL", "60601"],
    ]
    return list_to_csv([results])

# print(get_columns(["Customer", "Product"]))
# print(try_query("select all"))