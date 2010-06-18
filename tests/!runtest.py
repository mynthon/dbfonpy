import imp
import decimal
dbfonpy = imp.load_source('dbfonpy', '../dbfonpy.py')

def compareFiles(f1, f2):
    fp1 = open(f1,'rb')
    fp2 = open(f2,'rb')
    
    fd1 = fp1.read()
    fd2 = fp2.read()
    
    if len(fd1) != len(fd2):
        print 'Loaded and saved files have different lengths!'
    
    # skip modify date
    if fd1[4:] != fd2[4:]:
        print 'Loaded and saved files are different!'
        
    fp1.close()
    fp2.close()


########## START TESTS ############

################################################################################
if 1:
    print ''
    print 'Testing struct module...'
    import struct
    if 32 != struct.calcsize('<c3sIHH16scc2s'):
        print 'Dbf header format is incorrest for this machine.'
        print 'USING DBFONPY ON THIS MACHINE WILL CORRUPT FILES!'
    print 'Test end.'

################################################################################
if 1:
    print ''
    print 'Testing reading from file...'
    
    conn = dbfonpy.connect('test1exp.dbf')
    c = conn.cursor()
    c.execute()
    
    i = 0
    testdata = (
        ('This is FIRST RECORD',1234567890,decimal.Decimal('1234.5678'),True,'19310912'),
        ('This is record number 2',12,decimal.Decimal('5.0'),' ','19791231'),
        ('This is third record',1,decimal.Decimal('12.6'),False,'19990130')
    )
    for row in c:
        for j in xrange(len(testdata[i])):
            if row[j+1] != testdata[i][j]:
                print 'Row %s, column %s error.' % (i+1,j+1)
                print 'test: %s' % testdata[i][j]
                print 'row:  %s' % row[j+1]
        i += 1
    if i == 0:
        print 'No results found!'
    
    print 'Test end.'


################################################################################
if 1:
    print ''
    print 'Testing reading and saving file...'
    
    conn = dbfonpy.connect('test1exp.dbf')
    c = conn.cursor()
    conn.commit('test1sv.dbf')
    
    compareFiles('test1sv.dbf', 'test1exp.dbf')
    
    conn = dbfonpy.connect('test1sv.dbf')
    c = conn.cursor()
    c.execute()
    
    i = 0
    testdata = (
        ('This is FIRST RECORD',1234567890,decimal.Decimal('1234.5678'),True,'19310912'),
        ('This is record number 2',12,decimal.Decimal('5.0'),' ','19791231'),
        ('This is third record',1,decimal.Decimal('12.6'),False,'19990130')
    )
    for row in c:
        for j in xrange(len(testdata[i])):
            if row[j+1] != testdata[i][j]:
                print 'Row %s, column %s error.' % (i+1,j+1)
                print 'test: %s' % testdata[i][j]
                print 'row:  %s' % row[j+1]
        i += 1
    if i == 0:
        print 'No results found!'
    
    print 'Test end.'


################################################################################
if 1:
    print ''
    print 'Testing creating and saving file...'
    
    columns = (
        ('FIELDCHAR', 'C', 50),
        ('FIELDNUM', 'N', 10),
        ('FIELDFLT', 'N', 9, 4),
        ('FIELDBOOL', 'L'),
        ('FIELDDATE', 'D')
    )
    conn = dbfonpy.connect('test1cn.dbf', columns)
    c = conn.cursor()
    c.insert(['This is FIRST RECORD',1234567890,decimal.Decimal('1234.5678'),True,'19310912'])
    c.insert(['This is record number 2',12,decimal.Decimal('5.0'),' ','19791231'])
    c.insert(['This is third record',1,decimal.Decimal('12.6'),False,'19990130'])
    conn.commit()

    compareFiles('test1cn.dbf', 'test1exp.dbf')
    
    conn = dbfonpy.connect('test1cn.dbf')
    c = conn.cursor()
    c.execute()
    
    i = 0
    testdata = (
        ('This is FIRST RECORD',1234567890,decimal.Decimal('1234.5678'),True,'19310912'),
        ('This is record number 2',12,decimal.Decimal('5.0'),' ','19791231'),
        ('This is third record',1,decimal.Decimal('12.6'),False,'19990130')
    )
    for row in c:
        for j in xrange(len(testdata[i])):
            if row[j+1] != testdata[i][j]:
                print 'Row %s column %s error.' % (i+1,j+1)
                print '[%s:%s] TEST DATA IS: %s' % (i+1,j+1,testdata[i][j])
                print '[%s:%s] DATA IN FILE: %s' % (i+1,j+1,row[j+1])
        i += 1
    if i == 0:
        print 'No results found!'
    
    print 'Test end.'


################################################################################
if 1:
    print ''
    print 'pseudo SQL'

    conn = dbfonpy.connect('TEST1sql1.dbf')
    c = conn.cursor()

    c.execute()
    if len(c.fetchall()) == 4:
        print 'ALL RECORDS OK'
    else:
        print 'ALL RECORDS FAIL'
    
    c.execute('select * from dbf')
    if len(c.fetchall()) == 4:
        print 'ALL RECORDS OK'
    else:
        print 'ALL RECORDS FAIL'
    
    c.execute('select * from dbf where delete_flag = true')
    result = c.fetchall()
    if len(result) == 2 and\
        result[0][1] == '2 deleted record' and\
        result[1][1] == '3 deleted record':
        print 'NOT DELETED RECORDS OK'
    else:
        print 'NOT DELETED RECORDS FAIL'
    
    c.execute('select * from dbf where delete_flag = false')
    result = c.fetchall()
    if len(result) == 2 and\
        result[0][1] == '1 not deleted record' and\
        result[1][1] == '4 not deleted record':
        print 'DELETED RECORDS OK'
    else:
        print 'DELETED RECORDS FAIL'
    
    try:
        c.execute('select * fere deleted = true')
        print 'WRONG SQL FAIL'
    except(dbfonpy.DbfOnPySqlError):
        print 'WRONG SQL OK'
        
    print ('\nPRINT ROWS (4 expected):')
    i = 0
    c.execute('select * from dbf')
    for row in c.fetchall():
        print row
        i += 1
    if i == 4:
        print '4 of 4 OK'
    else:
        print '%s of 4 - FAIL' % i
    
    print 'Test end.'


################################################################################
if 0:
    print ''
    print 'Testing large file...'
    
    import time
    debugTime = time.time()
    conn = dbfonpy.connect('cart.dbf')
    print 'Data load time: %s' % (time.time() - debugTime)
    c = conn.cursor()
    print '%d rows loaded' % c.rowcount
    print 'Test end.'











raise SystemExit





# print __debug__
#dbu = connect('KARTY.DBF')

cols = (
    ('col1', 'N', 8, 2),
    ('col2', 'C', 20),
    ('col3', 'L')
)

dbu = connect('test3.dbf', cols)
c = dbu.cursor()

c.insert([20.46, 'column1', True])
c.insert([189.89, 'column2', True])
c.insert([1223.7, 'column3', False])

dbu.commit()
raise SystemExit

#dbu = connect('INTERNET.DBF')
dbu = connect('test.DBF')

print dbu.recordset[0]
print dbu.recordset[1]
print dbu.recordset[2]
print dbu.recordset[3]

#raise SystemExit
curs = dbu.cursor()
print '-----------------'
for row in curs:
    print row
print '-----------------'

print 'description:'
print curs.description
print 'description dbf:'
print curs.descriptionDbf
print 'description dbf2:'
print curs.descriptionDbf2
print 'insert'
curs.insert(['a', 1, True, '20080901', 'b', 23])
curs.insert(['rekord', 12346.7898, False, '20080901', 'xxpp', 3])
curs.insert(['rekordx', 12345.7897, ' ', '20080901', 'xxpp', 3])
curs.insert(['rekordy', -1234.7897, ' ', '20080901', 'xxiiii', 3])
print 'rowcount'
print curs.rowcount
print 'num of records (heder)'
print dbu.header['numberOfRecords']
print 'commit'
dbu.commit('test2.dbf')
raise SystemExit

tWork = time.time()
print "loop start: " + str(tWork)

for i in curs:
    print i

tWork = time.time() - tWork
print "loop end: " + str(tWork)

curs.pack()