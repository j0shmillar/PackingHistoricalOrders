import mysql.connector
import json
import datetime

conf = json.load(open("config.json"))

def switchToDB(name):
    global conf
    conf['mysql-db'] = name


def uq(s):
    return s.replace("'","''")

def q(s):
    return f"'{uq(s)}'"

def sqlDo(sqlList, params = {}):
    global conf
    cnx = mysql.connector.connect(
            user    =conf['mysql-user'],
            password=conf['mysql-pass'],
            database=conf['mysql-db'],
            auth_plugin='mysql_native_password'
            )
    cursor = cnx.cursor()
    try:
        for sql in sqlList:
            if sql.strip() != '':
                cursor.execute(sql, params)
    finally:
        cnx.commit()
        cursor.close()
        cnx.close()

def dld(sqld, params = {},debug = False):
    global conf
    cnx = mysql.connector.connect(
            user    =conf['mysql-user'],
            password=conf['mysql-pass'],
            database=conf['mysql-db'],
            auth_plugin='mysql_native_password'
            )
    cursor = cnx.cursor()
    ret = {}
    if isinstance(sqld,str):
        sqld = {"result":sqld}
    for (k,v) in sqld.items():
        #print(k,v)
        cursor.execute(v,params)
        ret[k] = []
        for r in cursor:
            rw = {}
            for (i,c) in enumerate(cursor.description):
                if isinstance(r[i],datetime.datetime):
                    rw[c[0]] = r[i].isoformat()
                else:
                    rw[c[0]] = r[i]
            ret[k].append(rw)
    cnx.commit()
    cursor.close()
    cnx.close()
    return ret
