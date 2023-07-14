import gzip
import json

with gzip.open("C:/Users/Tejinder Soomal/Downloads/Books.json.gz", "r") as f:
   data = f.read()
   j = json.loads (data.decode('utf-8'))
   print (type(j))