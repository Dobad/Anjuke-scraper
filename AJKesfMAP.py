import requests, csv, os, sys
import pandas as pd
from datetime import date

print('WARNING: Start?')
y = input('Type \'y\' to continue: ')
if y == 'y':
    print('Scraping started.')
else:
    sys.exit()

today = date.today().strftime("%Y%m%d")
header = {'user-agent': 'Mozilla/5.0'}

dic = {
    'shanghai': [120.70,121.64],
    'guangzhou': [113.16,113.44],
    'shenzhen': [113.90,114.24],
    'beijing': [116.20,116.66],
    'chengdu': [103.80,104.20],
    'nanjing': [118.70,118.90],
    'tianjin': [117.10,117.50],
    'hangzhou': [120.06,120.30],
    'suzhou': [120.56,120.7],
    'chongqing': [106.40,106.70],
    'dalian': [121.621333],
    'wuhan': [114.20,114.40],
    'foshan': [113.10,113.16],
    'zhengzhou': [113.60,113.70],
    'changsha': [112.98,113.02],
    'qingdao': [120.22,120.46],
    'xian': [108.90,109.00],
    'ningbo': [121.555065],
    'dongguan': [113.758187],
    'fuzhou': [119.30,119.40],
    'guiyang': [106.718174],
    'taiyuan': [112.54,112.60],
    'shenyang': [123.40,123.50],
    'kunshan': [120.987441],
    'nanchang': [115.92],
    'zhuhai': [113.583215],
    'jiaxing': [120.762075],
    'xiamen': [118.10,118.20],
    'haerbin': [126.63904],
    'changchun': [125.331262],
    'sanya': [109.518266],
    'huizhou': [114.421928],
    'wulumuqi': [87.594941],
    'mudanjiang': [129.631534]
}

first = True
last = False
index = 0

for city,cityRange in dic.items():
    print(f'{index} {city}...')
    index += 1
    path = f'Database/{city}/esf'
    if os.path.exists(path) is False:
        os.mkdir(path)
    opf = f'{path}/AJKesfMAP_{city}_{today}.csv'

    finished = False
    totalLines = 0

    with open(opf, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['小区','房屋数量','count','均价变动','lng','lat','地址','ID']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        while not finished:
            if first == True:
                m = 76
                n = cityRange[0]
                first = False
                if n == cityRange[-1]:
                    last = True
            elif last == True:
                m = cityRange[-1]
                n = 135
                first = True
                last = False
                finished = True
            else:
                m = n
                n = round(n + 0.02, 2)
                if n == cityRange[-1]:
                    last = True
            
            print(f'{m}_{n}\t', end='\a')
            url = f'https://{city}.anjuke.com/v3/ajax/map/sale/facet/?zoom=17&lat=16_54&lng={m}_{n}'
            data= requests.get(url, headers=header).json()
            lines = len(data['val']['comms'])

            error = True
            while error:
                if lines == 0:
                    print("Error. Retrying... ", end='\a')
                    data= requests.get(url, headers=header).json()
                    lines = len(data['val']['comms'])
                else:
                    error = False
            # if lines == 0:
            #     print(f'error on {city} {m}_{n}')
            #     continue
            totalLines += lines
            print(f'found {lines} lines.')

            for j in range(lines):
                p = data['val']['comms'][j]
                midP = p['mid_price']
                if midP == 0 or midP == "" or midP == '0' or midP == '1' or midP == 1:
                    continue
                name = p['truncate_name']
                count = p['prop_num']
                PChange = p['mid_change']
                lng = p['lng']
                lat = p['lat']
                address = p['address'].replace(',','，')
                commID = p['id']
                writer.writerow({
                    '小区': name,
                    '房屋数量': count,
                    'count': midP,
                    '均价变动': PChange,
                    'lng': lng,
                    'lat': lat,
                    '地址': address,
                    'ID': commID
                })

    df = pd.read_csv(opf,header=0)
    len1 = len(df)
    print(f'Successfully scraped {len1} lines.\nRemoving duplicated coordinates...')
    df.drop_duplicates(subset=['lng','lat'], inplace=True, keep=False)
    len2 = len(df)
    df.to_csv(opf, encoding='utf-8', index=False, float_format='%.6f')
    print(f'{len1} - {len1-len2} = {len2}\n')

print('All done.')
os.system('pause')
