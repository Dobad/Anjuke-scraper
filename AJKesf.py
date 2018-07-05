from bs4 import BeautifulSoup
import requests, csv, time, re, sys, os, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print('''This program is to scrape ErShouFang data from Anjuke.com. 

Please...
Turn off Lantern or other VPN-like application for optimum speed.(it's not fast anyway...) 
Do not open the generated file before the program is finished.
Make sure the result.html file is in the same directory of this file.
Also be aware that there is a maximum of 3000 items in ErShouFang section with no more than 60 items each page, which means there're only 50 pages at most. 
''')

text = input('Please input the Pinyin of the city OR paste the url of the first page: ')

if text.startswith('http') and '.anjuke.com/sale/' in text:
    city = re.search('(?<=://)\w+', text).group(0)
    url = text
elif '.anjuke.com/sale/' in text:
    city = re.search('\w+',text).group(0)
    url = 'https://' + text
elif text.isalpha():
    city = text
    url = 'https://'+ city +'.anjuke.com/sale/p1/'
else:
    print('There\'s something wrong with your input. Please check again.')

temp = 'AJKesf_' + city + '(temp).csv'

header = {'user-agent': 'Mozilla/5.0'}

print(f'Checking if {city} exists in the database...')

res = requests.get(url, headers=header)
if url != res.url:
    print(f'Either \'{city}\' doesn\'t exists in Anjuke\'s ErShouFang database or the url {url} is invalid. Program terminated.')
    sys.exit()

print(f'Program started. Scraping data from https://'+ city +'.anjuke.com/sale/. \nPlease wait. To terminate the program, press ctrl+C.')

soup = BeautifulSoup(res.text, 'lxml')
city_zh = soup.find(class_='city').text

print('')

with open(temp, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['标题','小区','房型','面积','均价','总价','层位','建筑年份','所在区','地段','地址']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

count = 1

while True:
    print('Now on page', count, end='\r', flush=True)
    count += 1
    res = requests.get(url, headers=header)
    soup = BeautifulSoup(res.text, 'lxml')

    for i in range(len(soup.find_all('li','list-item'))):
        o = soup.find_all('li','list-item')[i].find('div','pro-price').find_all('span')
        p = soup.find_all('li','list-item')[i].find('div','house-details').find_all('div','details-item')[0].find_all('span')

        title = soup.find_all('li','list-item')[i].find('div','house-details').find_all('div','house-title')[0].text.strip().replace(',',' ').replace('\n安选验真','')
        if len(soup.find_all('li','list-item')[i].find('div','house-details').find_all('div','details-item')) == 2:
            q = re.match(r"(\S+)(\s+)(\w+)-(\w+)-(.+)", soup.find_all('li','list-item')[i].find('div','house-details').find_all('div','details-item')[1].text.strip())
            commName = q[1]
            district = q[3]
            plate = q[4]
            address = q[5].replace(',',' ')
        else:
            commName = ''
            district = ''
            plate = ''
            address = ''
        roomtype = p[0].text
        size = p[1].text.strip('m²')
        unitprice = o[1].text.strip('元/m²')
        totalprice = o[0].text
        
        try:
            floor = p[2].text
        except:
            floor = ''
        
        if len(soup.find_all('li','list-item')[i].find('div','house-details').find_all('div','details-item')[0].find_all('span')) == 5:
            yearOfBuilt = soup.find_all('li','list-item')[i].find('div','house-details').find_all('div','details-item')[0].find_all('span')[3].text.strip('年建造')
            floor = p[2].text
        elif len(soup.find_all('li','list-item')[i].find('div','house-details').find_all('div','details-item')[0].find_all('span')) == 4:
            yearOfBuilt = ''
            floor = p[2].text
        else:
            yearOfBuilt = ''
            floor = ''
        
        with open(temp, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['标题','小区','房型','面积','均价','总价','层位','建筑年份','所在区','地段','地址']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow({
                '标题': title,
                '小区': commName,
                '房型': roomtype,
                '面积': size,
                '均价': unitprice,
                '总价': totalprice,
                '层位': floor,
                '建筑年份': yearOfBuilt,
                '所在区': district,
                '地段': plate,
                '地址': address
            })

    if soup.find(class_='aNxt') is not None:
        url = soup.find(class_='aNxt')['href']
    else:
        break

print('\nScraping complete!\nRemoving duplicates...')

df = pd.read_csv(temp)
df.drop_duplicates(subset=None, inplace=True)
fl = f'AJKesf_{city}.csv'
df.to_csv(fl, encoding='utf-8', index=False)


old_lines = sum(1 for line in open(temp, encoding="utf-8"))
new_lines = sum(1 for line in open(fl, encoding="utf-8"))

os.remove(temp)

print(f'Removed {old_lines-new_lines} duplicated lines. {new_lines} lines remained. Temporary file deleted.')

print('Analysis started...')

nf = f'analysis_{city}.csv'

df = pd.read_csv(fl, header=0)
lines = len(df)
s1 = set()
# s2 = set()
# s3 = set()

for i in range(lines):
    s1.add(df['小区'][i])
# for j in range(lines):
#     s2.add(df['地段'][j])
# for k in range(lines):
#     s3.add(df['所在区'][k])
t1 = {x for x in s1 if x == x}
# t2 = {x for x in s2 if x == x}
# t3 = {x for x in s3 if x == x}

with open(nf, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['小区','count','lng','lat']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

count_comm = 1
commWithCoord = 1
totalComm = len(t1)

print('Calculating average prices and obtaining coordinates of each community from api.map.baidu.com...')

for m in t1:
    print(f'now on community {count_comm}/{totalComm}', end='\r', flush=True)
    li = []
    for n in range(lines):
        if df['小区'][n] == m:
            li.append(df['均价'][n])
    avg = int(sum(li)/len(li))
    
    geocoder_url = f'http://api.map.baidu.com/geocoder/v2/?address={city_zh}市{m}&output=json&ak=7x7kT5Qo9qBK5ucW6eqGF16qsToonADj'
    resp = requests.get(geocoder_url)
    data = json.loads(resp.text)

    if data['status'] == 1:
        lng = ''
        lat = ''
    elif data['result']['level'] == '地产小区':
        lng = data['result']['location']['lng']
        lat = data['result']['location']['lat']
        commWithCoord += 1
    else:
        lng = ''
        lat = ''

    with open(nf, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['小区','count','lng','lat']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow({
            '小区': m,
            'count': avg,
            'lng': lng,
            'lat': lat
        })

    count_comm += 1

print(f'Successfully obtained {commWithCoord} coordinates in {len(t1)} communities.')

''' 
print('Generating bar charts for data of plates and districts...')

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height, int(height), ha='center', va='bottom')

li_plate_name = []
li_plate_value = []
for p in t2:
    li = []
    for q in range(lines):
        if df['地段'][q] == p:
            li.append(df['均价'][q])
    avg = int(sum(li)/len(li))
    li_plate_name.append(p)
    li_plate_value.append(avg)

if max(li_plate_value) < 15000:
    interval = 1000
elif max(li_plate_value) >= 15000 and max(li_plate_value) < 50000:
    interval = 5000
elif max(li_plate_value) >= 50000 and max(li_plate_value) < 100000:
    interval = 10000
else:
    interval = 20000

width = 0.35
ind = np.arange(len(li_plate_name))
fig, ax = plt.subplots()
bar_plate = ax.bar(ind, li_plate_value, width)
ax.set_ylabel('Price(Yuan/m²)')
ax.set_title(f'Average price per square meter by plate in {city}')
ax.set_xticks(ind)
plt.yticks(np.arange(0,max(li_plate_value)*1.2,interval))
ax.set_xticklabels(li_plate_name)
autolabel(bar_plate)
plt.show()

li_district_name = []
li_district_value = []
for x in t3:
    li = []
    for y in range(lines):
        if df['所在区'][y] == x:
            li.append(df['均价'][y])
    avg = int(sum(li)/len(li))
    # print(x, avg)
    li_district_name.append(x)
    li_district_value.append(avg)

if max(li_district_value) < 15000:
    interval = 1000
elif max(li_district_value) >= 15000 and max(li_district_value) < 50000:
    interval = 5000
elif max(li_district_value) >= 50000 and max(li_district_value) < 100000:
    interval = 10000
else:
    interval = 20000

width = 0.4
ind = np.arange(len(li_district_name))
fig, ax = plt.subplots()
bar_district = ax.bar(ind, li_district_value, width)
ax.set_ylabel('Price(Yuan/m²)')
ax.set_title(f'Average price per square meter by district in {city}')
ax.set_xticks(ind)
plt.yticks(np.arange(0,max(li_district_value)*1.2,interval))
ax.set_xticklabels(li_district_name)
autolabel(bar_district)
plt.show()

print('Analysis complete. Opening browser for visual output. \nDO NOT close this window before closing the browser.')
os.system(f'cd {os.getcwd()} | python -m http.server | python -m webbrowser -t "http://localhost:8000/result.html"')
 '''

print('Finished.')

os.system('pause')
