# -*- coding:utf8 -*-
"""
@author: Krzysiek Grzembski (mynthon.net)
@version: 0.0.1
@python: 2.6
@license: free for any use
@warranty: no warranty at all

--------------------------------------------------------------------------------
--- MANUAL ---------------------------------------------------------------------
--------------------------------------------------------------------------------

C data is returned as string right stripped
N data is returned as float
L data is returned as boolean
D data is returned as string

dataset[0] contains iformations about delete flag. If True item is marked as
deleted. 

First column in dataset contains info about delete flag, but it has to be
transparent to user! For user data always begins with index 0 not 1!

--------------------------------------------------------------------------------
--- EXAMPLES -------------------------------------------------------------------
--------------------------------------------------------------------------------

conn = connect('file.dbf' [,cols])
Opens database. If second argument is givent creates new empty database.
Second (optional) argument is list of columns containing name and definiton.
Currently only few types are supported.
Numeric column - list of four values: name, type, length, decimal
Character column - list of three values: name, type, length
Date column - list of three values: name, type, length
Logical column - list of three values: name, type, length

example of creating new database:

columns = (
    ('MYNUM', 'N', 8, 2),
    ('MYCHAR', 'C', 30),
    ('MYLOGICL', 'L'),
    ('MYDATE', 'D')
)

dbu = connect('mydb.dbf', columns)

cursor = conn.cursor()

cursor.description
# return tuple containing 7-items tuples. First item for every tuple is column
# name and other items are None.
# (
#   (colname1, None, None, None, None, None, None),
#   (colname2, None, None, None, None, None, None),
#   (colname3, None, None, None, None, None, None),
# )

cursor.descriptionDbf
# Returns tuple containing column names.
# (colname1, colname2, colname3 ..., colnameN)

cursor.descriptionDbf2
# returns tuple containing tuples for every column. Data in every tuple is
# column name, field length, field type and decimal places.
# (
#   (colname1, length, type, decimal),
#   (colname2, length, type, decimal),
#   (colname3, length, type, decimal),
# )

conn.commit('newfile.dbf')
# Saves file. If no name is given saves changes to current file.

LINKS:
http://code.activestate.com/recipes/362715/
http://www.whitetown.com/dbf-format/dbf.php
http://www.clicketyclick.dk/databases/xbase/format/
http://www.clicketyclick.dk/databases/xbase/format/dbf.html#DBF_STRUCT
"""

import time
import sys
import math
import struct
import re
import decimal

class DbfOnPyError(Exception):
    pass

class DbfOnPyDataError(Exception):
    pass

class DbfOnPySqlError(Exception):
    pass

def connect(f, cols=None):
    return Connection(f, cols)

class Cursor():
    def __init__(self, parent):
        self._parent = parent
        self._cnt = 0
        self._dataset = parent._dataset
        self._recordset = parent._recordset
        self.description = None
        self.descriptionDbf = None
        self.descriptionDbf2 = None
        self._description()
        self.rowcount = len(self._dataset)
    
    def _description(self):
        set = [] # py db api
        set2 = [] # colnames only
        set3 = [] # column full info (name, len, type, decimal)
        set.append(('MARKED_FOR_DELETE',None,None,None,None,None,None))
        set2.append('MARKED_FOR_DELETE')
        set3.append(('MARKED_FOR_DELETE', 1, '', 0))
        for record in self._recordset:
            set.append((record['name'],None,None,None,None,None,None))
            set2.append(record['name'])
            set3.append((
                record['name'],
                record['length'],
                record['type'],
                record['decimal']
            ))
        self.description = tuple(set)
        self.descriptionDbf = tuple(set2)
        self.descriptionDbf2 = tuple(set3)
    
    def __analyzeSqlQuery(self, query):
        """\
        Method analyzes sql query and overwrites selecting methods.
        Methods: fetchone(), fetchall(), next() are overwritten at runtime.
        It allows to spped up selecting of data.
        """
        sqlQuery = query.lower().strip().rstrip(';').rstrip()
        sqlQuery = re.sub('\s+', ' ', sqlQuery)
        
        if sqlQuery == 'delete from dbf':
            self.zap()
            
        elif sqlQuery == 'commit':
            self.self.commit()
            
        elif sqlQuery == 'select * from dbf' or sqlQuery == '':
            # fetch all records (default)
            def next():
                if self._cnt >= len(self._dataset):
                    self._cnt = 0
                    raise StopIteration
                else:
                    self._cnt += 1
                    return self._dataset[self._cnt - 1]
            self.next = next
            
            def fetchall():
                return self._dataset
            self.fetchall = fetchall
            
            def fetchone():
                if self._cnt >= len(self._dataset):
                    return None
                else:
                    self._cnt += 1
                    return self._dataset[self._cnt - 1]
            self.fetchone = fetchone
            
        elif sqlQuery == 'select * from dbf where delete_flag = true':
            # fetch all deleted rows
            def next():
                while 1:
                    if self._cnt >= len(self._dataset):
                        self._cnt = 0
                        raise StopIteration
                    else:
                        self._cnt += 1
                        if self._dataset[self._cnt - 1][0] == True:
                            return self._dataset[self._cnt - 1]
            self.next = next
            
            def fetchall():
                return [row for row in self._dataset if row[0] == True]
            self.fetchall = fetchall
            
            def fetchone():
                while 1:
                    if self._cnt >= len(self._dataset):
                        return None
                    else:
                        self._cnt += 1
                        if self._dataset[self._cnt - 1][0] == True:
                            return self._dataset[self._cnt - 1]
            self.fetchone = fetchone
            
        elif sqlQuery == 'select * from dbf where delete_flag = false':
            # fetch all not deleted rows
            def next():
                while 1:
                    if self._cnt >= len(self._dataset):
                        self._cnt = 0
                        raise StopIteration
                    else:
                        self._cnt += 1
                        if self._dataset[self._cnt - 1][0] == False:
                            return self._dataset[self._cnt - 1]
            self.next = next
            
            def fetchall():
                return [row for row in self._dataset if row[0] == False]
            self.fetchall = fetchall
            
            def fetchone():
                while 1:
                    if self._cnt >= len(self._dataset):
                        return None
                    else:
                        self._cnt += 1
                        if self._dataset[self._cnt - 1][0] == False:
                            return self._dataset[self._cnt - 1]
            self.fetchone = fetchone
            
        else:
            raise DbfOnPySqlError(
                '\nWrong query:\n'\
                '%s\n'\
                'Allowed are:\n'\
                'EMPTY STRING\n'\
                'select * from dbf\n'\
                'select * from dbf where delete_flag = true\n'\
                'select * from dbf where delete_flag = false\n' % sqlQuery
            )
    
    def fetchone(self):
        return None
    
    def fetchall(self):
        return []
    
    def rowcount(self):
        return len(self._dataset)
    
    def execute(self, sql='', data=None):
        self.__analyzeSqlQuery(sql)
        return True
    
    def __iter__(self):
        return self
    
    def next(self):
        raise StopIteration
    
    # *********************
    # dbf specific options
    # *********************
    def delete(self):
        """ Mark current record as deleted """
        self._dataset[self._cnt - 1][0] = True
    
    def undelete(self):
        """ Mark current record as not deleted """
        self._dataset[self._cnt - 1][0] = False
    
    def zap(self):
        """ Marks all records as deleted """
        for i in xrange(len(self._dataset)):
            self._dataset[i][0] = True
    
    def pack(self):
        """ Remove all records marked as deleted. """
        # go from end to begin to avoid reindexing issues
        i = len(self._dataset) - 1
        while i >= 0:
            if self._dataset[i][0]:
                del self._dataset[i]
            i -= 1
    
    def toTxt(self, filename, delimiter=',', lineEnd='\r\n', header=False):
        """Exports current selection to text file."""
        fp = open(filename, 'wb')
        
        headerTxt = ''
        if header:
            headerData = []
            for record in self._recordset:
                headerData.append(record['name'])
            headerTxt = delimiter.join(headerData) + lineEnd
        fp.write(headerTxt)
        
        lineFormat = delimiter.join(
            ['%s'] * len(self._recordset)
            ) + lineEnd
        
        for line in self:
            fp.write(lineFormat % tuple(line[1:]))
        
        fp.close()
    
    def toSqlite3(self, filename):
        pass
    
    def insert(self, data):
        """
        None insert(data)
        inserts new data. data length has to be equal to number of columns
        (delete flag not included - it is always False for new records)
        and must have right order. File is not saved automatically!  
        """
        if len(data) == len(self._recordset):
            i = 0
            
            # prepare record to insert
            while i < len(self._recordset):
                if self._recordset[i]['type'] == 'C':
                    data[i] = self._parent._format_C_put_(data[i], self._recordset[i]['length'])
                elif self._recordset[i]['type'] == 'N':
                    data[i] = self.__fmt_N_upd(data[i], self._recordset[i]['length'], self._recordset[i]['decimal'])
                elif self._recordset[i]['type'] == 'L':
                    data[i] = self.__fmt_L_upd(data[i])
                else:
                    #domyslnie traktuj jak string
                    data[i] = self._parent._format_C_put_(data[i], self._recordset[i]['length'])
                i += 1
            
            # add delete flag to record
            data.insert(0, False)
            # add record
            self._dataset.append(data)
    ### /insert
    
    def update(self, data):
        """ modify current record """
        if len(data) == len(self._recordset):
            i = 0
            while i < len(self._recordset):
                if self._recordset[i]['type'] == 'C':
                    self._dataset[self._cnt - 1][i+1] = self._parent._format_C_put_(data[i], self._recordset[i]['length'])
                elif self._recordset[i]['type'] == 'N':
                    self._dataset[self._cnt - 1][i+1] = self.__fmt_N_upd(data[i], self._recordset[i]['length'], self._recordset[i]['decimal'])
                elif self._recordset[i]['type'] == 'L':
                    self._dataset[self._cnt - 1][i+1] = self.__fmt_L_upd(data[i])
                else:
                    #domyslnie traktuj jak string
                    self._dataset[self._cnt - 1] = self._parent._format_C_put_(data[i], self._recordset[i]['length'])
                i += 1
    ### /update
    
    #########################################################
    # section: datachecking
    # check data for insert and update operations
    #########################################################
    def __fmt_L_upd(self, da):
        if type(da) is bool or da == ' ':
            return da
        raise DbfOnPyDataError('Invalid value for BOOL column: "%s"' % da)
    
    def __fmt_N_upd(self, num, numLen, decPlaces):
        """Returns number if is allowed."""
        
        """
        In dbf length of numeric field is total length with decimal separator
        and minus sign so number -174.976 has length 8.
        
        In field of length 5 and 2 decimal places you can put numbers from
        -9.99 to 99.99.
        
        My idea to check if number fits field is to multiple number by
        10 to power "decimalPlaces". Eg. (length=6, decimal=2) number 853.8776
        become 85387.76. Now i round it to get 85388.
        
        This number cannot be bigger than 10^fieldLength if there is no decimal
        separator and 10^(fieldLength-1) if there is decimal separator (thats
        because decimal separator takes one slot from total length).
        
        I my example length=6 and there is decimal separator (decimalPlaces>0) so
        biggest number is 10^(6-1)=100000. 85388 is smaller than 100000 so it is ok.
        
        For the same field number 999.99998 is not ok because:
        999.99998 * 10^decimalPlaces = 99999.998
        after rounding i get 100000. 100000 == 10000 so number doesnt fit.
        
        For the same field number 1111.5 is not ok because:
        1111.5 * 10^decimalPlaces = 111150
        after rounding i get 111150. 111150 > 10000 so number doesnt fit.
        """
        
        point = 1 - 0 ** decPlaces
        
        number = decimal.Decimal(str(num))
        if number.is_zero():
            return decimal.Decimal('0')
        
        number2 = (number * 10 ** (decPlaces)).quantize(decimal.Decimal('1')) 
        #print number, number2, (10 ** (numLen - 1)), point
        
        if ((10 ** (numLen - point)) > number2 > (10 ** (numLen - point - 1) * (-1))):
            return number
        else:
            raise DbfOnPyDataError('After rounding number %s does not fit to cell of lenght %s with %s decimal places.' % (num, numLen, decPlaces))
            return None


class Connection:
    #########################################################
    # section: basic methods
    #########################################################
    
    def __init__(self, fname, cols):
        
        # jesli jest cols to znaczy ze masz stworzyc nowa pusta baze danych
        if cols != None:
            self.__createEmptyDB(fname, cols)
        
        # te zmienne sluza do porownan, zeby nie tworzyc obiektow
        # w kazdym IF...ELSE czy RETURN
        self.DATA_DBF_L_TRUE = 'T'
        self.DATA_DBF_L_FALSE = 'F'
        self.DATA_DBF_L_EMPTY = ' '
        
        self.DATA_DBF_DELFLAG_TRUE = '\x2a' # '*'
        self.DATA_DBF_DELFLAG_FALSE = '\x20' # ' '
        
        # inne
        self.currentFileName = ''
        self.header = {}
        self._recordset = []
        self._dataset = []
        self.idx = [{}] # indexes
        
        self.currentFileName = fname;
        
        f = open(fname, 'rb')
        
        '''# header
        self.header = {
            'fileType' : f.read(1),
            'lastUpdate' : f.read(3), # YMD
            'numberOfRecords' : self._byteToInt_(f.read(4)),
            'positionFirstData' : f.read(2), # where first data starts (bytes)
            'lengthOfData' : self._byteToInt_(f.read(2)), # length of one data record with del flag
            'reserved1' : f.read(16),
            'tableFlag' : f.read(1),
            'codePage' : f.read(1),
            'reserved2' : f.read(2)
        } ''' 
        
        (
        self.header['fileType'],
        self.header['lastUpdate'], # YMD
        self.header['numberOfRecords'],
        self.header['positionFirstData'], # where first data starts (bytes)
        self.header['lengthOfData'],# length of one data record with del flag
        self.header['reserved1'],
        self.header['tableFlag'],
        self.header['codePage'],
        self.header['reserved2']
        ) = struct.unpack('<c3sIHH16scc2s', f.read(32))
        
        # record set
        while 1:
            if f.read(1) == '\x0d':
                f.seek(-1,1) # after checking for delimiter go back 1 char
                break
            else:
                f.seek(-1,1) # after checking for delimiter go back 1 char
                self._recordset.append(
                    {
                        'name' : self._format_COLNAME_get_(f.read(10)),
                        'break' : f.read(1),
                        'type' : f.read(1),
                        'displacement' : f.read(4),
                        'length' : self._byteToInt_(f.read(1)),
                        'decimal' : self._byteToInt_(f.read(1)),
                        'flag' : f.read(4),
                        'autoincrement' : f.read(1),
                        'step' : f.read(1),
                        'reserved' : f.read(8)
                    }
                )
        
        # skip terminator 0x0d and database container 0x00
        f.read(1)
        while 1:
            if f.read(1) != '\x00':
                f.seek(-1,1)
                break
        
        # data
        
        ##### PREKOMPILACJA #######
        
        # tutaj przygotowujemy i prekompilujemy funkcje, dzieki czemu
        # przy duzych plikach przyspieszamy wczytywanie do 50%!
        dataAppendConf = []
        i = 1 # @ 0 is delete flag
        
        for j in self._recordset:
            le = j['length']
            if j['type'] == 'C':
                dataAppendConf.append('strline[%s:%s].rstrip()' % (i, i+le))
            elif j['type'] == 'N':
                dataAppendConf.append('self._format_N_get_(strline[%s:%s])' % (i, i+le))
            elif j['type'] == 'L':
                dataAppendConf.append('self._format_L_get_(strline[%s:%s])' % (i, i+le))
            else:
                dataAppendConf.append('strline[%s:%s]' % (i, i+le))
            i += le
        
        compilestr  = ''\
            '\ndef appendfuncdynamic(self, strline):'\
            '\n    temp = False;'\
            '\n    if strline[0] == self.DATA_DBF_DELFLAG_TRUE: temp = True;'\
            '\n    self._dataset.append([temp, %s])' % ','.join(dataAppendConf)
        
        exec(compilestr)
        
        while 1:
            dbfLine = f.read(self.header['lengthOfData'])
            if len(dbfLine) != self.header['lengthOfData'] or dbfLine[0] == '\x1a':
                break
            else:
                appendfuncdynamic(self, dbfLine)
        f.close()
        
    ### /__init__()
    
    def __createEmptyDB(self, fname, cols):
        """ Create empty database """
        
        # ustaw dane do naglowka
        self.header = {
            'fileType' : '\x03',
            'lastUpdate' : self._lastUpdate_(time.strftime("%y%m%d")), # YMD
            'numberOfRecords' : 0,
            'positionFirstData' : 0, # where first data starts (bytes)
            'lengthOfData' : 0, # length of one data record with del flag
            'reserved1' : '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
            'tableFlag' : '\x00',
            'codePage' : '\x00',
            'reserved2' : '\x00\x00'
        }
        
        # clear current recordset info (columns definitions)...
        self._recordset = []
        
        # ... and add new one.
        for row in cols:
            # ('name', 'type', length, decimal)
            ctypes = ('L','N','C','D')
            cname = '%s%s' % (row[0].upper(), (10 - len(row[0])) * '\x00')
            clen = 1
            cdec = 0
            ctype = row[1].upper()
            
            if ctype not in ctypes:
                ctype = 'C'
            
            try:
                if ctype == 'N':
                    cdec = row[3]
            except:
                pass
            
            try:
                if ctype == 'C' or ctype == 'N':
                    clen = row[2]
                elif ctype == 'D':
                    clen = 8
                elif ctype == 'L':
                    clen = 1
            except:
                pass
            
            self._recordset.append(
                {
                    'name' : cname,
                    'break' : '\x00',
                    'type' : ctype,
                    'displacement' : '\xb8\x60\x0d\x00',
                    'length' : clen,
                    'decimal' : cdec,
                    'flag' : '\xec\x75\x02\x65',
                    'autoincrement' : '\xaa',
                    'step' : '\x21',
                    'reserved' : '\x72\x4f\x0d\x00\xec\x75\x12\x65'
                }
            )
        # wyczysc stare dane
        self._dataset = [] 
        self.commit(fname)
    ### /__createEmptyDB
    
    def commit(self,f=''):
        if f == '':
            f = self.currentFileName
        dbf = open(f, "wb")
        
        # recordset
        dataFieldLength = 1 #delete flag
        _recordset = b''
        for i in xrange(len(self._recordset)):
            _recordset += self._format_COLNAME_put_(self._recordset[i]['name'])
            _recordset += self._recordset[i]['break']
            _recordset += self._recordset[i]['type']
            _recordset += self._recordset[i]['displacement']
            _recordset += self._intToByte_(self._recordset[i]['length'], 1)
            _recordset += self._intToByte_(self._recordset[i]['decimal'], 1)
            _recordset += self._recordset[i]['flag']
            _recordset += self._recordset[i]['autoincrement']
            _recordset += self._recordset[i]['step']
            _recordset += self._recordset[i]['reserved']
            dataFieldLength += self._recordset[i]['length']
        
        # terminator and db container
        _TerminatorAndDBContainer = b'\x0d\x00'
        
        # header
        '''
        _header = ''
        _header += self.header['fileType']
        _header += self._lastUpdate_(time.strftime("%y%m%d"))# last update
        _header += self._intToByte_(len(self._dataset),4) # num of records
        _header += self._intToByte_(32 + len(_TerminatorAndDBContainer) + len(_recordset), 2) # 
        _header += self._intToByte_(dataFieldLength,2) # length of data record
        _header += self.header['reserved1']
        _header += self.header['tableFlag']
        _header += self.header['codePage']
        _header += self.header['reserved2']
        '''
        
        _header = struct.pack('<c3sIHH16scc2s', 
            self.header['fileType'],
            self._lastUpdate_(time.strftime("%y%m%d")),
            len(self._dataset),
            32 + len(_TerminatorAndDBContainer) + len(_recordset),
            dataFieldLength,
            self.header['reserved1'],
            self.header['tableFlag'],
            self.header['codePage'],
            self.header['reserved2']
        )
        
        # save header
        dbf.write(_header + _recordset + _TerminatorAndDBContainer)
        
        # save data        
        for rowdata in self._dataset:
            _data = ''
            columnNo = 0
            for field in rowdata:
                if columnNo == 0:
                    _data += self.__format_DELETEFLAG_put(field)
                else:
                    if self._recordset[columnNo-1]['type'] == 'N':
                        _data += self._format_N_put_(
                            field,
                            self._recordset[columnNo-1]['length'],
                            self._recordset[columnNo-1]['decimal']
                        )
                    elif self._recordset[columnNo-1]['type'] == 'L':
                        _data += self._format_L_put_(field)
                    else:
                        _data += self._format_C_put_(
                            field,
                            self._recordset[columnNo-1]['length']
                        )
                columnNo += 1
            dbf.write(_data)
        #end of file     
        
        dbf.write('\x1a')
        dbf.close()
    ### /commit()
    
    #########################################################
    # section: cursor
    #########################################################
    
    def cursor(self):
        """ create cursor which contains all rows """
        return Cursor(self)
    
    #########################################################
    # section: data formatting methods
    # _put_ methods translates data from column format to file
    # _get_ methods translates data from file to column format
    #########################################################
    
    def _format_C_put_(self, dataString, dataLength):
        if len(dataString) > dataLength:
            raise DbfOnPyError, 'String is too long: ' + \
                str(len(dataString)) + \
                " (max: " + str(dataLength) +" expected)"
        dataString = ("% -" + str(dataLength) + "s") % dataString
        return dataString
    
    def _format_C_get_(self, dataString):
        return dataString.rstrip()
    
    def _format_N_put_(self, dataString, dataLength, decimalPlaces):
        return ("% " + str(dataLength) + "s") % (("%.0" + str(decimalPlaces) + "f") % decimal.Decimal((dataString)))
    
    def _format_N_get_(self, dataString):
        try:
            return decimal.Decimal(dataString)
        except:
            return 0
    
    def _format_L_put_(self, dataString):
        if dataString == True:
            return self.DATA_DBF_L_TRUE
        elif dataString == False:
            return self.DATA_DBF_L_FALSE
        else:
            return self.DATA_DBF_L_EMPTY
    
    def _format_L_get_(self, dataString):
        if dataString == self.DATA_DBF_L_FALSE:
            return False
        elif dataString == self.DATA_DBF_L_TRUE:
            return True
        else:
            return dataString
        
    def _format_D_put_(self):
        pass
    
    def _format_D_get_(self):
        pass
    
    def _format_COLNAME_get_(self, colname):
        return colname[0:colname.find('\x00')]

    def _format_COLNAME_put_(self, dataString):
        if len(dataString) > 10:
            return dataString[0:10]
        else:
            return dataString + ((10 - len(dataString)) * '\x00')

    def __format_DELETEFLAG_get(self, dataString):
        return (dataString == self.DATA_DBF_DELFLAG_TRUE and True) or False
    
    def __format_DELETEFLAG_put(self, flag):
        return (flag and self.DATA_DBF_DELFLAG_TRUE) or self.DATA_DBF_DELFLAG_FALSE
    
    #########################################################
    # section: helper methods
    #########################################################
    
    def _intToByte_(self, n, l):
        """ Converts integer to bytes. If length aftrer conversion
        is smaller than given as param returned value is right-filled
        with 0x00 bytes. Use Little-endian  byte order."""
        return b''.join([
            chr((n >> ((l - i - 1) * 8)) % 256) for i in xrange(l)
        ][::-1])
    
    def _byteToInt_(self, bytes):
        """ Converts byte string to integer.
        struct.unpack is too much platform dependent.
        Use Little-endian  byte order."""
        return sum([
            ord(b) << (8 * i) for i, b in enumerate(bytes)
        ])
    
    def _lastUpdate_(self, dateYMD = None):
        """
        _lastUpdate_([str data_YYMMDD]) -> void
        aktualizuje informacje o dacie ostatniej modyfikacji jesli ten parametr
        zostal podany, w przeciwnym wypadku wyswietla date ostatniej modyfikacji.
        """
        if dateYMD == None:
            out = "%02d" % ord(self.header["lastUpdate"][0])
            out += "%02d" % ord(self.header["lastUpdate"][1])
            out += "%02d" % ord(self.header["lastUpdate"][2])
            return out
        else:
            out  = chr(int(dateYMD[0:2]))
            out += chr(int(dateYMD[2:4]))
            out += chr(int(dateYMD[4:6]))
            return out
    
    def _numberOfRecords_(self, records = -1):
        """
        _numberOfRecords_([int ile_rekordow]) -> void
        aktualizuje informacje o ilosci rekordow jesli parametr zostal podany,
        w przeciwnym wypadku przesyla do konsoli informacje o aktualnej ilosci rekordow.
        """
        if records < 0:
            print self._byteToInt_(self.header['numberOfRecords'])
        else:
            self.header["numberOfRecords"] = self._intToByte_(records,4)
    
    def _lengthOfData_(self, length = -1):
        if length < 0:
            print self._byteToInt_(self.header['lengthOfData'])
        else:
            self.header["lengthOfData"] = self._intToByte_(length,2)
    
    def _positionFirstData_(self, position = -1):
        if position < 0:
            print self._byteToInt_(self.header['positionFirstData'])
        else:
            self.header["positionFirstData"] = self._intToByte_(position,2)   
