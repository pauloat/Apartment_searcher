import bs4, requests, re, os
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

page = '' #OLX page with filters

#The headers help to avoid anti bot measures
headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept-Language': 'en-US'
        }
 
res = requests.get(page, headers=headers)

soup = bs4.BeautifulSoup(res.text, 'html.parser')

listings = []

horas = #Max hours looking up

max_price = #Max price (price + condominio)

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
    
    if datetime.now() - datetime.strptime(date_listing, '%Y-%m-%d %H:%M:%S') > timedelta(hours = horas, minutes = 5):
        continue #If the listing is older than 1hour and 5minutes do not include
    
    rooms = soup.find_all('span', {'aria-label': re.compile('\d quarto')})[i].text
    
    size = soup.find_all('span', {'aria-label': re.compile('\d+ metros')})[i].text
    
    link = soup.find_all('a', {'class': 'sc-eKZiaR YfujD'})[i].get('href')
    
    try:
        neighbor = re.findall(r'Rio de Janeiro, (\w+( \w+)?)',soup.find_all('span', {'aria-label': re.compile('localiza')})[i].text)[0][0]
    except:
        neighbor = ''
    
    res_listing = requests.get(link, headers = headers)
    
    soup_listing = bs4.BeautifulSoup(res_listing.text, 'html.parser')
    
    comments = soup_listing.find('span', {'class': 'ad__sc-1sj3nln-1 fMgwdS sc-ifAKCX cmFKIN'}).text
    
    diaria = re.findall(r'(?i)di[aá]ria', comments) #Look the comments for diarias
    
    if len(diaria) > 0: #Don't use the listing if is a diaria
        continue
    
    listing = {
        "Date": date_listing,
        "Price": price,
        "Condominio": condominio,
        "Total price": total_price,
        "Size": size,
        "Rooms": rooms,
        "Neighbor": neighbor,
        "Comments": comments,
        "Link": link
        }
    
    listings.append(listing)
    



if len(listings) != 0:  
    message = ''
    separator = ', '

    keys = list(listings[0].keys())

    for d in listings:
      for key in keys:
        message += key + ': ' + str(d[key]) + separator

      message = message[:-len(separator)] + '\n\n\n'

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)

    smtp_server.starttls()
    smtp_server.login('', '')
                       #your email, your google application password
    msg = MIMEMultipart()
    msg['From'] = '' #your email
    msg['To'] = '' #clients email
    msg['Subject'] = 'Apartment Searcher ' + str(now) 
    body = message
    msg.attach(MIMEText(body, 'plain'))

    smtp_server.sendmail('', '', msg.as_string())
    #                     my email, recipient email
    smtp_server.quit()


#code next is for the testing enviroment
'''
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

listings_file = open('listings_file_' + str(now) + '.txt', 'w')

for item in listings:
    
    listings_file.write("%s \n" % item)
        
listings_file.close()
'''
