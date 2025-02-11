Run the following in SQL Studio and export results in to a json file

```
SELECT TABLE_SCHEMA ,
       TABLE_NAME ,
       COLUMN_NAME ,
       DATA_TYPE 
FROM   INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='SalesLT';
```
