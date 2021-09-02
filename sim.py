import csv
import os
import random
from sqlutil import sqlDo, dld
import io
import sys
import datetime
from sqlutil import dld, switchToDB
from getproduct import getProduct
import googlemaps
import json
from newpacker import Packer, Bin, Item

runconf = json.load(open("runconfig.json"))
if len(sys.argv) < 3:
    print("Include locker.json and orderdata.txt")
    exit(1)
lockerLayout = sys.argv[1]
orderData = sys.argv[2] 
f = open(lockerLayout, "r")
la = json.loads(f.read())
f.close()
truck = la[0]['truck']

def calcBins(bins):
    for x in bins:
            binsUsed[int(x)-1] += 1

def lockerAvailability(since = None, daysAheadLo = 2, daysAheadHi = 10):
    return dld({
          "lockers": '''
SELECT trip.truck, departs,lockerMap.num locker, lockerMap.height totalh, u.id AS occupied,kind,w,d,h
  FROM trip JOIN lockerMap ON trip.truck =  lockerMap.truck AND gone = 0
       LEFT JOIN (
        SELECT tripTruck,tripDeparts,lmTruck,lmNum,delivery.id
          FROM alloc JOIN delivery on delivery=id AND status >= 20
         GROUP BY tripTruck,tripDeparts,lmTruck,lmNum,delivery.id
         ) AS u ON trip.departs=u.tripDeparts
                  AND trip.truck=u.lmTruck
                  AND lockerMap.num = u.lmNum
             JOIN lockerKind ON kind = lockerKind.id
 ORDER BY departs,trip.truck,locker
          '''
          }, {"today":since or datetime.datetime.today().isoformat()[:10]})

def makeItSo(oordernum,truck,address,bins,name,email,mobile,coworker='not-set'):
    itemSQL = []
    for b in bins:
        for i in b.items:
            [x,y,z] = [int(x) for x in i.position]
            [w,h,d] = [int(x) for x in i.get_dimension()]
            itemSQL.append(f'''
            INSERT INTO alloc(lmTruck,lmNum,delivery,art,w,h,d,x,y,z,weight)
            VALUES ({truck},{b.name},@delivery,'{i.name.split('_',1)[1]}',{w},{h},{d},{x},{y},{z},{i.weight})''')
    sqlList = f'''
    INSERT INTO delivery(oordernum,tripTruck,tripDeparts,address,name,email,phone,mru_who,mru_whn)
      VALUES(%(oordernum)s,{truck},'2022-01-01 17:00:00',%(address)s,%(name)s,%(email)s,%(phone)s,%(coworker)s,CURRENT_TIMESTAMP);
    SET @delivery = @@IDENTITY;
    {';'.join(itemSQL)}
    '''.split(';\n')
    sqlDo(sqlList, {
        "oordernum": oordernum,
        "address": address,
        "name":name,
        "email":email,
        "phone":mobile,
        "coworker":coworker
    })
    return {"success":True,"truck":truck}

def canFitOptimise(items,lockerList):
    lockerList = sorted(lockerList, key = lambda l: l[1]*l[2]*l[3])
    items = list(reversed(sorted(items, key = lambda l: l[1]*l[2]*l[3])))
    cf = canFit(items,lockerList)
    if not cf["success"]:
        return cf
    if len(cf["bins"]) == 1:
        return cf
    binsUsed = (x.name for x in cf["bins"])
    calcBins(binsUsed)
    lockerList2 = [x for x in lockerList if x[0] in binsUsed]
    lockerList2.reverse()
    cf2 = canFit(items,lockerList2)
    if cf2["success"]:
        print("Applied reverse lockers used")
        return cf2
    return cf

def canFit(items,lockerList):
    packer = Packer()
    for i in items:
        packer.add_item(Item(*i))
    for b in lockerList:
        packer.add_bin(Bin(b[0],b[1],b[2],b[3],b[4],b[5]))
    packer.pack(distribute_items = True, bigger_first=False)
    unfitted = [{"id":i.name.split('_')[1],
        "w":float(i.width),
        "h":float(i.height),
        "d":float(i.depth),
        "weight":float(i.weight),
        } for i in (packer.bins[-1].unfitted_items if len(packer.bins)>0 else packer.items)]
    used_bins = [b for b in packer.bins if len(b.items) > 0]
    return {"success":len(packer.bins) > 0 and len(packer.bins[-1].unfitted_items) == 0,
            "bins":used_bins,
            "bin_names": [b.name for b in used_bins],
            "unfitted":unfitted}

def tryFit(d):
    global count
    m = json.loads(d)
    r = m['_embedded']['Articles']
    artLst = []
    dimensions = {}
    for a in r:
        pp = getProduct(a['itemId'])
        dimensions[a['itemId']] = pp['packageList']
        for k,d in enumerate(pp['packageList']):
            for i in range(a['quantity']):
                artLst.append([
                    f"{i}-{k}_{a['itemId']}",
                    d['height'],
                    d['length'],
                    d['width'],
                    d['weight']
                    ])
    f = open(lockerLayout, "r")
    la = json.loads(f.read())
    f.close()
    candidates = groupBy(la, lambda a: (a['truck'],a['departs']))
    tripsWithCapacity = []
    err = []
    for k, v in candidates.items():
        lockers = [[f"{x['locker']}",x['w'],x['h'],x['d'],x['totalh'],5555] for x in v if x['occupied'] == None]
        cf = canFitOptimise(artLst, lockers)
        if cf['success']:
            tripsWithCapacity.append(k)
#           new from here
            la = lockerAvailability()['lockers']
            packer = Packer()
            lockerList = [(f"{x['locker']}",x['w'],x['h'],x['d'],x['totalh'],5555) for x in la 
                if x['truck'] == truck and x['occupied'] == None]
            lockerList.sort(key = lambda x: x[0]*x[1]*x[2])
            ret = canFitOptimise(artLst,lockerList)
            if ret['success']:
                makeItSo(1,truck,"xx",ret["bins"],"xx","xx","xx") 
                count+=1
            else:
                ordersFitted.append(count)
                clearTruck(truck);
                makeItSo(1,truck,"xx",ret["bins"],"xx","xx","xx")
                count = 1
    if tripsWithCapacity:
        successfulOrders.append(m['_embedded']['orderNo'])
        return 1
    else:
        failedOrders.append(m['_embedded']['orderNo'])
        return 0

def clearTruck(truck):
    sqlDo('''
DELETE FROM alloc;
DELETE FROM delivery WHERE tripTruck = %(truck)s AND tripDeparts = '2022-01-01 17:00:00';
            '''.split(";\n"), {"truck":truck})
    
def groupBy(lst, f):
    ret = {}
    for x in lst:
        k = f(x)
        if not k in ret:
            ret[k] = []
        ret[k].append(x)
    return ret

def sim(filename):
    f = open(f"./testorders/{orderData}/{filename}", "r")
    r = f.read()
    result = tryFit(r)
    return result

def mkorders():
    fn = orderData
    badOrders = []
    for f in [fn]:
        a = [s[:-1].split('\t') for s in io.open(f,encoding='ISO-8859-1')][1:]
        o = {}
        for l,i in enumerate(a):
            if float(i[6])>250:
                continue
            if i[4] == 'CPU':
                continue
            if i[10] != 'PRIVATE':
                continue
            if i[7] == 'SAC levering til hoveddør':
                continue
            if i[7] == 'SAC levering til kantsten uden indbæring (LCD Zone S)':
               continue
            if i[7] == 'Onlineordre planlagt levering med ind/opbæring':
                continue
            if i[7] == 'Planlagt levering med indbæring':
                continue
            if i[16] == 'METER':
                badOrders.append(i[0])
                continue
            if not i[0] in o:
                o[i[0]] = {'_embedded':{'Articles':[],'orderNo':i[0]}}
            art = ('00000000'+i[11])[-8:]
            if i[16] == 'PIECES':
                o[i[0]]['_embedded']['Articles'].append({'itemId':art,'quantity':int(i[15])})
            else:
                pass
        for i in o:
            if not i in badOrders:
                f = open(f'testorders/{orderData}/{i}.json','w')
                f.write(json.dumps(o[i]))

switchToDB(runconf.get("dbName",'caddev'))
totalFit = 0
totalProcessed = 0
successfulOrders = []
failedOrders = []
binsUsed = []
count = 0
ordersFitted = []
for x in open(lockerLayout,"r"):
    binsUsed.append(0)
if not os.path.isdir('testorders'):
    os.mkdir('testorders')
if not os.path.isdir(f"testorders/{orderData}"):
    os.mkdir(f"testorders/{orderData}")
    mkorders()
x = os.listdir(f"testorders/{orderData}")
x.sort()
for filename in x[:100]:
    totalFit += sim(filename)    
    if totalProcessed % 50 == 0:
        print(f"Processing {totalProcessed}")
    totalProcessed+=1
print(f"Processing {totalProcessed}")
clearTruck(truck);
percentage = round((totalFit/(totalProcessed))*100,2)
with open(f'good_orders_truck{truck}.csv', 'w', newline='') as myfile:
     wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
     wr.writerow(successfulOrders)
with open(f'bad_orders_truck{truck}.csv', 'w', newline='') as myfile:
     wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
     wr.writerow(failedOrders)
print("Results:")
print("Total Orders Simulated = "+str(totalProcessed))
print("Total Fit = "+str(totalFit)+"/"+str(totalProcessed)+" = "+str(percentage)+"%")
for x in range(len(binsUsed)):
    print(f"Bin {x+1} usage = {round(((binsUsed[x-1]/totalProcessed)*100),2)}%")
average = sum(ordersFitted) / len(ordersFitted)
print("Average orders fitted per trip = "+str(round(average,2)))
