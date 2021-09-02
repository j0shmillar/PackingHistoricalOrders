from requests import get
import json
import sys
import os

#Examples 00263850 - Billy bookcase, single package
#         50403589 - Malm chest of drawers, two packages
#         49009947 - Malm bed, three packages in two child items 20250050 and 70278725

headers = {
  "x-client-id":"534ee22a-1e41-4f3c-a593-10dae2d07bf9",  # From David Hagland
  "authority":"api.ingka.ikea.com"
  }

def getProduct(item, lang='dk'):
  fle = f"ingka-cache/{item}"
  j = None
  if os.path.isfile(fle):
      j = json.load(open(fle))
  else:
      url = f'https://api.ingka.ikea.com/salesitem/communications/ru/{lang}?expand=1&itemNos={item}'
      a = get(url,headers=headers)
      j = json.loads(a.text)
      f = open(fle,'w');
      f.write(a.text);
  if not 'data' in j:
    return "No data"
  b = j['data'][0]
  #print(f"{b=}")
  pl = []
  ret = {
    "item": item,
    "productName": b["localisedCommunications"][0]["productName"],
    "productDesc": b["localisedCommunications"][0]["productType"]['name'],
    "packageList": []
  }
  if "media" in b["localisedCommunications"][0]:
    ret["mediaName"] = b["localisedCommunications"][0]["media"][0]["name"]
    for m in b["localisedCommunications"][0]["media"][0]["variants"]:
      if m["quality"] == "S2":
        ret["image"] = m["href"]
  def packages(b):
      #packNo gives the index (1 based)
      #DINERA
      #Espresso cup and saucer
      #Article no:
      #604.240.15
      #This product has multiple packages.
      #Length: 2 cm
      #Weight: 0.09 kg
      #Diameter: 10 cm
      #
      #Width: 7 cm
      #Height: 6 cm
      #Length: 8 cm
      #Weight: 0.13 kg
      #
      #[{'type':x['type'],'packNo':x['packNo'],'valueMetric':x['valueMetric']} for x in c if x['type'] in ['WIDTH','LENGTH','HEIGHT','DIAMETER','WEIGHT']]
      #[{'type': 'DIAMETER', 'packNo': 1, 'valueMetric': '10'}, {'type': 'LENGTH', 'packNo': 1, 'valueMetric': '2'}, {'type': 'WEIGHT', 'packNo': 1, 'valueMetric': '0.09'},
      #{'type': 'HEIGHT', 'packNo': 2, 'valueMetric': '6'}, {'type': 'LENGTH', 'packNo': 2, 'valueMetric': '8'}, {'type': 'WEIGHT', 'packNo': 2, 'valueMetric': '0.13'}, {'type': 'WIDTH', 'packNo': 2, '-1e41-4f3c-a593-10dae2d07bf9valueMetric': '7'}]
      c = b["localisedCommunications"][0]["packageMeasurements"]
      interestingTypes = {'LENGTH','WIDTH','HEIGHT','WEIGHT','DIAMETER'}
      d = [[{'key':j['type'],'value':j['valueMetric']}
          for j in c if j['packNo']==i+1 and j['type'] in interestingTypes] for i in range(b['numberOfPackages'])]
      e = [dict([[a['key'].lower(),float(a['value']) if a['key'] == 'WEIGHT' else 10*int(a['value'])] for a in x])
              for x in d]
      #substitute diameter for any missing dimension
      def subst(p):
          if 'diameter' in p:
              for d in ['length','width','height']:
                  if not d in p:
                      p[d] = p['diameter']
          return p
      return [subst(x) for x in e]
  if 'childItems' in b:
     for c in b['childItems']:
         for _ in range(c['quantity']):
             ret["packageList"].extend(packages(c))
  else:
      ret["packageList"].extend(packages(b))
  return ret

