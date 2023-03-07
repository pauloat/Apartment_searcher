#Libraries
import bs4, requests, re, logging
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#Variables
page = '' #Page with filters
frequency = 12 #In hours
max_price = 5000 #Max price (price + condominio)
server_email = ''
server_password = ''
client_email = ''
Market_analyser = False

### logging ###

logging.basicConfig(filename='Apartment_searcher_Main.log', level=logging.INFO)

logging.info('INFO: ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script starting')


### code ###

if Market_analyser:
    import pandas as pd

    data = pd.read_csv('listings.txt')
    data.columns = ['Codigo', 'Date', 'Price', 'Condominio', 'Total price', 'Size', 'Price / mt2', 'Neighbor']
    market_mean = round(data['Price / mt2'].mean(), 2)
    data_by_neighbor = data.groupby('Neighbor')
    mean_by_neighbor = data_by_neighbor.mean()
    mean_pricexmt2_by_neighbor = mean_by_neighbor['Price / mt2']

#The headers help to avoid anti bot measures
headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept-Language': 'en-US'
        }
 
res = requests.get(page, headers=headers)

soup = bs4.BeautifulSoup(res.text, 'html.parser')

listings = []


logging.info('INFO: ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' BeatifulSoup found ' + str(len(soup.find_all('span', {'class': 'main-price'}))) + ' total listings')

for i in range(len(soup.find_all('span', {'class': 'main-price'}))):
    
    price = int(re.sub(r'\D', '', soup.find_all('span', {'class': 'main-price'})[i].text))
    
    try:
        condominio = int(re.sub(r'\D', '', soup.find_all('span', {'class': 'second-price-label'})[i].text))
    except:
        condominio = 0 #If there's no condominio it gave an error, now it just gave 0
        
    total_price = price + condominio
    
    if total_price > max_price:
        continue
    
    date_published = soup.find_all('span', {'class': 'adDate'})[i*2+1].text
      
    if date_published[:4] == 'Hoje':
        date_listing = str(date.today()) + ' ' + date_published[6:12] + ':00' #transform the date in a standard format
    elif date_published[:5] == 'Ontem':
        date_listing = str(date.today() - timedelta(days=1)) + ' ' + date_published[7:13] + ':00'
    else:
        continue    
    
    if datetime.now() - datetime.strptime(date_listing, '%Y-%m-%d %H:%M:%S') > timedelta(hours = frequency, minutes = 10):
        continue #If the listing is older than 1hour and 5minutes do not include
    
    rooms = soup.find_all('span', {'aria-label': re.compile(r'\d quarto')})[i].text
    
    size = soup.find_all('span', {'aria-label': re.compile(r'\d+ metros')})[i].text
    
    price_x_mt2 = round(total_price / int(re.sub(r'\D', '', size)), 2)
    
    link = soup.find_all('a', {'data-ds-component' : 'DS-AdCardHorizontal'})[i].get('href')
    
    try:
        neighbor = re.findall(r'Rio de Janeiro, (\w+( \w+)?)',soup.find_all('span', {'aria-label': re.compile('localiza')})[i].text)[0][0]
    except:
        neighbor = ''
    
    res_listing = requests.get(link, headers = headers)
    
    soup_listing = bs4.BeautifulSoup(res_listing.text, 'html.parser')
    
    try:
        comments = soup_listing.find('span', {'class': 'ad__sc-1sj3nln-1 fMgwdS sc-ifAKCX cmFKIN'}).text
    except:
        comments = ''
        
    diaria = re.findall(r'(?i)di[aá]ria', comments) #Look the comments for diarias
    temporada = re.findall(r'(?i)temporada', comments) 
    
    if (len(diaria) + len(temporada)) > 0: #Don't use the listing if is a diaria
        continue
    
    if Market_analyser and neighbor != '':
        neighbor_mean = mean_pricexmt2_by_neighbor[neighbor:].iloc[0]
        
        if price_x_mt2 < market_mean:
            market_mean_text = str(round(market_mean - price_x_mt2, 2)) + " R$/mt2 mais BARATO do que a media na Zona Sul"
        elif price_x_mt2 > market_mean:
            market_mean_text = str(round(price_x_mt2 - market_mean, 2)) + " R$/mt2 mais CARO do que a media na Zona Sul"    
        else:
            market_mean_text = "Este apartamento esta igual do que a media da Zona Sul"
            
        if price_x_mt2 < neighbor_mean:
            neighbor_mean_text = str(round(neighbor_mean - price_x_mt2, 2)) + " R$/mt2 mais BARATO do que a media em " +  neighbor
        elif price_x_mt2 > neighbor_mean:
            neighbor_mean_text = str(round(price_x_mt2 - neighbor_mean, 2)) + " R$/mt2 mais CARO do que a media em " + neighbor    
        else:
            neighbor_mean_text = "Este apartamento esta igual do que a media em " + neighbor
    else:
        market_mean_text = ''
        neighbor_mean_text = ''
    
    
    listing = {
        "Date": date_listing,
        "Price": price,
        "Condominio": condominio,
        "Total price": total_price,
        "Price / mt2" : price_x_mt2,
        "Market mean": market_mean_text,
        "Neighbor mean": neighbor_mean_text,
        "Size": size,
        "Rooms": rooms,
        "Neighbor": neighbor,
        "Comments": comments,
        "Link": link
        }
    
    listing_formatted = f'''

Price: {listing['Price']}
Condominio: {listing['Condominio']}
Total price: {listing['Total price']}
Size: {listing['Size']}
Price/mt2: {listing['Price / mt2']}
{listing['Market mean']}
{listing['Neighbor mean']}
Rooms: {listing['Rooms']}
Neighbor: {listing['Neighbor']}

Comments:
{listing['Comments']}

Link: {listing['Link']}
Date: {listing['Date']}

---------------------------------------
'''
                
    
    listings.append(listing_formatted)


logging.info('INFO: ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script found ' + str(len(listings)) + ' valid listings')



#Production mode


if len(listings) != 0:  
    message = '\n\n\n'.join(listings)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)

    smtp_server.starttls()
    smtp_server.login(server_email, server_password)
                       #your email, your google application password
    msg = MIMEMultipart()
    msg['From'] = server_email #your email
    msg['To'] = client_email #clients email
    msg['Subject'] = f'Encontrei {len(listings)} apartamentos para voce!'
    body = message
    msg.attach(MIMEText(body, 'plain'))

    smtp_server.sendmail(server_email, client_email, msg.as_string())
    #                     your email, recipient email
    smtp_server.quit()




#Testing mode
'''

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

listings_file = open('listings_test_file_' + str(now) + '.txt', 'w')

for item in listings:
    
    listings_file.write("%s \n" % item)
        
listings_file.close()
'''

logging.info('INFO: ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script finished correctly')

