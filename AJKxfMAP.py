import requests, csv, os, json, math, sys
import pandas as pd
from datetime import date

print('WARNING: You are about to scrape data of new properties of 34 major cities throughout China.')
y = input('Type \'y\' to continue: ')
if y == 'y':
    print('Scraping started.')
else:
    sys.exit()

city_id = pd.read_csv('cityIDtask.csv', header=0)
today = date.today().strftime("%Y%m%d")

for i in range(len(city_id)):
    city = city_id['city'][i]
    print(f'{i+1}: {city}')
    cityID = city_id['ID'][i]
    path = f'Database/{city}/xf'
    if os.path.exists(path) is False:
        os.mkdir(path)
    opf = f'{path}/AJKxfMAP_{city}_{today}.csv'
    url = f'https://api.fang.anjuke.com/web/loupan/mapNewlist/?city_id={cityID}&status_sale=3,4,6&page_size=100&page=1'
    # r = requests.get(url)
    # data = json.loads(r.text)
    data = requests.get(url).json()
    total = data['result']['total']
    pages = math.ceil(total/100)
    line_count = 0
    dump = 0

    print(f'{total} communities found in {city}. Scraping started...')

    with open(opf, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['小区','count','lng','lat','上线时间','建筑类型','价格类型','显示价格','户型数量','区','地段','地址','ID']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for j in range(pages):
            url = f'https://api.fang.anjuke.com/web/loupan/mapNewlist/?city_id={cityID}&status_sale=3,4,6&page_size=100&page={j+1}'
            r = requests.get(url)
            data = json.loads(r.text)
            lines = len(data['result']['rows'])
            for k in range(lines):
                p = data['result']['rows'][k]
                if p['new_price'] == '0' or p['new_price'] == 0 or p['new_price'] == 1 or p['new_price'] == '1':
                    dump += 1
                    continue
                line_count += 1
                print(f'Writing {line_count}/{total}... ', flush=True, end='\r')
                name = p['loupan_name']
                count = p['house_type_count']
                if p['new_price_desc'] == '均价':
                    price = p['new_price']
                if p['new_price_desc'] == '总价':
                    if len(p['house_types']) != 0:
                        li = []
                        for h in range(len(p['house_types'])):
                            li.append(float(p['house_types'][h]['area']))
                        if sorted(li)[0] == sorted(li)[-1] == 0:
                            continue
                        else:
                            if sorted(li)[0] != 0:
                                area = sorted(li)[0]
                            elif sorted(li)[1] != 0:
                                area = sorted(li)[1]
                            else:
                                area = sorted(li)[-1]
                            price = int(int(p['new_price'])*10000/area)
                lng = p['baidu_lng']
                lat = p['baidu_lat']
                date = p['kaipan_new_date']
                buildingType = p['build_type'].replace(',','，')
                priceType = p['new_price_desc']
                region = p['region_title']
                sub_region = p['sub_region_title']
                address = p['address'].replace(',','，')
                commID = p['loupan_id']
                writer.writerow({
                    '小区': name,
                    'count': price,
                    'lng': lng,
                    'lat': lat,
                    '上线时间': date,
                    '建筑类型': buildingType,
                    '价格类型': priceType,
                    '显示价格': p['new_price_desc'],
                    '户型数量': count,
                    '区': region,
                    '地段': sub_region,
                    '地址': address,
                    'ID': commID
                })
    print(f'\nFinished. {line_count}/{total} scraped. {dump} lines dumped.')
    df = pd.read_csv(opf,header=0)
    len1 = len(df)
    df.drop_duplicates(subset=['lng','lat'], inplace=True, keep=False)
    len2 = len(df)
    df.to_csv(opf, encoding='utf-8', index=False)
    print(f'{len1-len2} lines removed from {len1} lines, {len2} remained.\n')
        
print('All done.')
os.system('pause')
