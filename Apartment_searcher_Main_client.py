#Libraries
import bs4, requests, re, logging, locale
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Apartment_searcher_Main_function import market_searcher

locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')


#Variables
client_name = ''
page = '' #Page with filters
frequency = 12 #In hours
max_price = 5000 #Max price (price + condominio)
min_size = 0
server_email = ''
server_password = ''
client_email = ''
Market_analyser = False

### logging ###

logging.basicConfig(filename=f'Apartment_searcher_{client_name}.log', level=logging.INFO)

logging.info(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script starting')

listings = market_searcher(client_name, page, frequency, max_price, min_size, Market_analyser)

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

listings_file = open(f'listings_test_file_{str(now)}.txt', 'w')

for item in listings:
    
    listings_file.write(f'{item} \n')
        
listings_file.close()

###

logging.info(' ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + ' Script finished correctly')
