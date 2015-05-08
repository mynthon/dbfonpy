# Introduction #

This module reads and writes dbf files. It is designed to looks like compatible with python db api, but only for extracting data.

# Details #

Currently only Character, Number, Logical values are supported. Date columns are treated as text.

## Basics ##

This module is designed to access dbf files in python way.

Currently it support only CHAR, NUMBER and LOGICAL types. Dates are represented as strings.

NUMBER type is represented as decimal (decimal.Decimal). Please take it into count when working
with floats.

### Connecting and retrieving data ###

Code:
```
import dbfonpy

dbf = dbfonpy.connect('my_dbf_file.dbf')
cursor = dbf.cursor()

cursor.execute() # no sql query given! this is how it works! it is not mistake!

for row in cursor:
   print row
```

The code above will return all records. First cell in every record will contain information if record **is marked** as deleted (True) or not (False).

For example if you have first and last row marked as deleted in this dbf file:

|1|Chris|13|
|:|:----|:-|
|2 |Maria|14|
|3 |Julia|33|

dbfonpy will return:

```
[True, Decimal('1'), 'Chris', Decimal('13')]
[False, Decimal('2'), 'Maria', Decimal('14')]
[True, Decimal('3'), 'Julia', Decimal('33')]
```





---

## dbfonpy methods ##

### ` Connection dbfonpy.connect(str fileName[, list columnsDefinition]) ` ###
Returns `Connection` object with connection to `fileName` dbf file. If optional `columnsDefinition` list is given new database will be created.

Opens database. If second argument is givent creates new empty database.
Second (optional) argument is list of columns containing name and definiton.
Currently only few types are supported.

  * Numeric column - list of four values: name, type, length, decimal
  * Character column - list of three values: name, type, length
  * Date column - list of three values: name, type, length
  * Logical column - list of three values: name, type, length

example of creating new database:

```
import dbfonpy

columns = (
    ('MYNUM', 'N', 8, 2),
    ('MYCHAR', 'C', 30),
    ('MYLOGICL', 'L'),
    ('MYDATE', 'D')
)

connection = dbfonpy.connect('mydb.dbf', columns)
cursor = connection.cursor()
#...
```




---

## Connection methods ##

### Cursor Connection.cursor() ###
Returns `Cursor` object.

### ` None Connection.commit([fileName]) ` ###
Saves data to current file. If optional `fileName` is given data will be saved to `fileName` file.




---

## Cursor methods ##

### ` None Cursor.execute() ` ###
Prepares data to fetch.

### ` list Cursor.fetchall() ` ###
Returns list containg all records from dbf file. Every record is list. It can return empty list if you forget to run `Cursor.execute`.

### ` list|None Cursor.fetchone() ` ###
Returns one record.

### ` Cursor.delete() ` ###
Marks current record as deleted.

### ` Cursor.undelete() ` ###
Marks current record as not deleted.

### ` Cursor.zap() ` ###
Marks all records as deleted.

### ` Cursor.pack() ` ###
Deletes permanently all records marked as deleted.

### ` Cursor.insert(data) ` ###
Inserts new record.

### ` Cursor.update(data) ` ###
Updates current record.