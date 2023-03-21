#Libraries
import bs4, requests, re, logging, locale
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')


#Variables
page = '' #Page with filters
frequency = 12 #In hours
max_price = 5000 #Max price (price + condominio)
min_size = 0
server_email = ''
server_password = ''
client_email = ''
Market_analyser = False

### logging ###

logging.basicConfig(filename='Apartment_searcher_Main.log', level=logging.INFO)

logging.info(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script starting')


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


logging.info(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' BeatifulSoup found ' + str(len(soup.find_all('span', {'class': 'main-price'}))) + ' total listings')

for i in range(len(soup.find_all('span', {'class': 'main-price'}))):
    
    while True:
        try:
            link = soup.select(f'li.sc-1mburcf-1:nth-child({i+1}) > a:nth-child(1)')[0].get('href')
            break
        except:
            i += 1
            if i > 100:
                break

    res_listing = requests.get(link, headers = headers)
    soup_listing = bs4.BeautifulSoup(res_listing.text, 'html.parser')
    
    codigo = soup_listing.select('.ad__sc-16iz3i7-0')[0].text
    codigo = int(re.sub(r'\D', '', codigo))

    price = soup_listing.select('h2.ad__sc-12l420o-1:nth-child(2)')[0].text
    price = int(re.sub(r'\D', '', price))
    
    try:
        condominio = soup_listing.select('div.gqoVfS:nth-child(1) > div:nth-child(3) > div:nth-child(3) > div:nth-child(1) > dd:nth-child(2)')[0].text
        condominio = int(re.sub(r'\D', '', condominio))
    except:
        condominio = 0 #If there's no condominio it gave an error, now it just gave 0
        
    total_price = price + condominio
    if total_price > max_price:
        continue
    
    date_text = soup_listing.select('.fpFNoN > span:nth-child(1)')[0].text
    date_numbers = re.sub(r'\D', '', date_text)
    datetime_obj = datetime.strptime(date_numbers, '%d%m%H%M')
    datetime_obj = datetime_obj.replace(year=date.today().year)
    date_listing = datetime_obj.strftime("%A, %d de %B de %Y - %H:%M:%S")

    if datetime.now() - datetime_obj > timedelta(hours = frequency, minutes = 10):
        continue #If the listing is older than frequency and 10 minutes do not include
    
    rooms = soup_listing.select('div.ad__duvuxf-0:nth-child(6) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1)')[0].text
     
    size = soup_listing.select('div.ad__duvuxf-0:nth-child(5) > div:nth-child(1) > dd:nth-child(2)')[0].text
    size = int(re.sub(r'\D', '', size))
    if size < min_size:
        continue
    
    price_x_mt2 = round(total_price / size)
    
    neighbor = soup_listing.select('div.ad__sc-1aze3je-1:nth-child(9) > a:nth-child(1)')[0].text
    neighbor = neighbor.strip() 
    
    try:
        comments = soup_listing.select('.ad__sc-1sj3nln-1')[0].text
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


logging.info(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script found ' + str(len(listings)) + ' valid listings')



#Production mode
"""###

if len(listings) != 0:  
    message = '\n\n\n'.join(listings)

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
    
    try:
        smtp_server.sendmail(server_email, client_email, msg.as_string())
        #                     your email, recipient email
        logging.info(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Email send correctly')
    except:
        logging.error(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Error trying to send email')


    smtp_server.quit()


"""###

#Testing mode


###


now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

listings_file = open('listings_test_file_' + str(now) + '.txt', 'w')

for item in listings:
    
    listings_file.write("%s \n" % item)
        
listings_file.close()

###

logging.info(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script finished correctly')
