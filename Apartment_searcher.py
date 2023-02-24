import bs4, requests, re, os
from datetime import date, datetime, timedelta

page = '' #The OLX address with the filters you want to look up

#The headers help to avoid anti bot measures
headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept-Language': 'en-US'
        }
 
res = requests.get(page, headers=headers)

soup = bs4.BeautifulSoup(res.text, 'html.parser')

listings = []

for i in range(len(soup.find_all('span', {'class': 'main-price'}))):
    
    price = int(re.sub(r'\D', '', soup.find_all('span', {'class': 'main-price'})[i].text))
    
    try:
        condominio = int(re.sub(r'\D', '', soup.find_all('span', {'class': 'second-price-label'})[i].text))
    except:
        condominio = 0 #If there's no condominio it gave an error, now it just gave 0
        
    total_price = price + condominio
    
    if total_price > 0: #maximum total price you want to look up.
        continue
    
    date_published = soup.find_all('span', {'class': 'adDate'})[i*2+1].text
      
    if date_published[:4] == 'Hoje':
        date_listing = str(date.today()) + ' ' + date_published[6:12] + ':00' #transform the date in a standard format
    elif date_published[:5] == 'Ontem':
        date_listing = str(date.today() - timedelta(days=1)) + ' ' + date_published[7:13] + ':00'
    else:
        continue    
    
    if datetime.now() - datetime.strptime(date_listing, '%Y-%m-%d %H:%M:%S') > timedelta(hours = 1, minutes = 5):
        continue #If the listing is older than 1hour and 5minutes do not include
    
    rooms = soup.find_all('span', {'aria-label': re.compile('\d quarto')})[i].text
    
    size = soup.find_all('span', {'aria-label': re.compile('\d+ metros')})[i].text
    
    link = soup.find_all('a', {'class': 'sc-eKZiaR YfujD'})[i].get('href')
    
    try:
        neighbor = re.findall(r'Rio de Janeiro, (\w+( \w+)?)',soup.find_all('span', {'aria-label': re.compile('localiza')})[i].text)[0][0]
    except:
        neighbor = ''
        
    listing = {
        "Date": date_listing,
        "Price": price,
        "Condominio": condominio,
        "Total price": total_price,
        "Size": size,
        "Rooms": rooms,
        "Neighbor": neighbor,
        "Link": link
        }
    
    listings.append(listing)

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

listings_file = open('listings_file_' + str(now) + '.txt', 'w')

for item in listings:
    
    listings_file.write("%s \n" % item)
        
listings_file.close()
