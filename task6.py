import os
import re
import glob
import requests
from dbfread import DBF
from pyproj import CRS
from pyproj import Transformer


print("Getting the list of files to donwload...")
download_page = "https://apps.planning.maryland.gov/Secure/REST/SharepointService1.svc/GetOpenData" # API that returns url to all data
attachments = requests.get(download_page).json()
links = []
for attachment in attachments: # Only get MPV data. MPV data are smaller in size.
    if attachment["FILENAME"].endswith("MPV15"):
        links.append((attachment["FILELINK"], attachment["FILENAME"]))

print("Downloading the files...")
for link, filename in links:
    print(f"downloading {filename}")
    os.system(f"wget -nc {link}?dl=1 -O {filename}.zip") # Might not work without wget. This can probably be done with requests too.

print("Unzipping the files...")
os.system("unzip \*.zip") # Unzip the files. This also relies on the unix command unzip (which I'm not sure is presnet in Windows).

print("Getting the list of the database files...")
data_files = glob.glob("*/ATDATA/DATABASE/*2015.dbf") # dbf file with all the relevant data

print("Setting up the crs to convert database coordinates to lon, lat...")
# Setup transformer. CRS.from_epsg(102285) does not work
crs_102285 = CRS.from_proj4("+proj=lcc +lat_1=38.3 +lat_2=39.45 +lat_0=37.66666666666666 +lon_0=-77 +x_0=400000 +y_0=0 +ellps=GRS80 +units=m no_defs")
# This is obtained from http://epsg.io/102285
crs_4326 = CRS.from_epsg(4326)
transformer = Transformer.from_crs(crs_102285, crs_4326)

output = open("locations.csv", "w")
errors = open("erros.csv", "w")
output.write(",JURSCODE,ACCTID,story,material,Latitude,Longitude\n")

row_num = 1
for data_file in data_files:
  print(f"Processing {data_file}")
  dbf = DBF(data_file, encoding='iso-8859-1') # 
  for row in dbf:
    jurs, acctid = row["JURSCODE"], row["ACCTID"]
    x, y = row["DIGXCORD"], row["DIGYCORD"]
    lat, long = transformer.transform(x, y)
    material = row["DESCCNST"]
    if len(material) < 2:
      errors.write(f"Empty material at {row['SDATWEBADR']}\n")
    material = material.replace("CNST ", "")
    story = row["DESCSTYL"]
    if len(story) < 1:
      errors.write(f"Empty story at {row['SDATWEBADR']}\n")
    if story.startswith("STRY"):
      if "Story" in story:
        story = re.findall(r'(\d.*) Story', story)[0].replace(" 1/2", ".5")
      elif "Split Foyer" in story:
        story = "2"
      else:
        print(f"UNKNOWN STORY: {story}")
    output.write(f"{row_num},{jurs},{acctid},{story},{material},{lat},{long}\n")
    row_num += 1
  output.flush()

output.close()
errors.close()