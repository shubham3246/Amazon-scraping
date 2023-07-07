from django.shortcuts import render

import requests
from bs4 import BeautifulSoup
import csv
import os
from app.models import *

# Create your views here.

HEADERS = ({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'})

def get_asin(asin_table):
    if asin_table:
        rows = asin_table.find_all('tr')
        
        for row in rows:
            th_element = row.find('th')
            
            if th_element and th_element.text.strip() == 'ASIN':
                td_element = row.find('td')
                
                if td_element:
                    asin_value = td_element.text.strip()
                    return asin_value
                    
    return None

def scrape_extra_data(url):   
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        #getting product description
        product_overview = soup.find('div', attrs={'id':'productOverview_feature_div'})
        if product_overview:
            product_overview = '\n'.join(item.get_text(separator='\n') for item in product_overview)
            product_overview = ' '.join(product_overview.split())

        #getting extra detail
        detail_bullet = soup.find('div', attrs={'id':'detailBullets_feature_div'})
        asin = ""
        
        if detail_bullet:
            detail_bullet = '\n'.join(item.get_text(separator='\n') for item in detail_bullet)
            detail_bullet = ' '.join(detail_bullet.split())

            asin = detail_bullet.find("ASIN")
            if asin:
                asin = detail_bullet[asin+9:asin+21].strip()

            
        if detail_bullet == None:
            detail_bullet = soup.find('table', attrs={'id':'productDetails_techSpec_section_1'})
            
            if detail_bullet:
                detail_bullet = '\n'.join(item.get_text(separator='\n') for item in detail_bullet)
                detail_bullet = ' '.join(detail_bullet.split())
        
            asin_table = soup.find('table', attrs={'id':'productDetails_detailBullets_sections1'})

            if asin == "":
                asin = get_asin(asin_table)
            
        
        #getting feature detail
        feature_detail = soup.find('div', attrs={'id':'feature-bullets'})

        if feature_detail:
            feature_detail = '\n'.join(item.get_text(separator='\n') for item in feature_detail)
            feature_detail = ' '.join(feature_detail.split())    

        #getting seller
        seller = soup.find('div', attrs={'id':'shipsFromSoldByInsideBuyBox_feature_div'})
        if seller:
            seller = '\n'.join(item.get_text(separator='\n') for item in seller)
            seller = ' '.join(seller.split())


        description = ""
        if(product_overview):
            description += "Description : \n" + product_overview
        if(feature_detail):
            description += "\nFeature : \n" + feature_detail
        if(detail_bullet):
            description += "\nProduct description : \n" + detail_bullet
        if(asin):
            description += "\nASIN : \n" + asin
        if(seller):
            description += "\nSeller : \n"+seller

        return [description, asin]


def scrape_page(url, pg):
    response = requests.get(url+str(pg), headers=HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        for i in range(1, 50):
            try:
                #getting element
                element = soup.find(attrs={'data-index': str(i)})

                #getting link
                data = element.find(class_='a-section')
                h2_element = data.find('h2')
                a_element = h2_element.find('a')
                href = "https://www.amazon.in"+a_element.get('href')

                

                #getting name
                name = h2_element

                #getting price
                price = data.find(class_='a-price-whole')

                #getting rating
                span_elements = data.find_all('span', attrs={'aria-label':True})
                rating = span_elements[0]
                
                #getting no. of ratings
                no_of_rating = span_elements[1]

                #getting extra data
                extra_data = scrape_extra_data(href)
                fileName = extra_data[1].strip()

                url = url.encode('ascii', errors='ignore').decode('ascii')
                name = name.text.encode('ascii', errors='ignore').decode('ascii')
                no_of_rating = no_of_rating.text.encode('ascii', errors='ignore').decode('ascii')
                price = price.text.encode('ascii', errors='ignore').decode('ascii')
                rating = rating.text.encode('ascii', errors='ignore').decode('ascii')
                extra_data = extra_data[0].encode('ascii', errors='ignore').decode('ascii')

                #saving the data
                folderName = 'csv_files/page_'+str(pg)+'/'
                if not os.path.exists(folderName):
                    os.makedirs(folderName)

                with open(folderName+fileName+'.csv', 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Url: "+url])
                    writer.writerow(["Name: "+name])
                    writer.writerow(["Price: Rs."+price])
                    writer.writerow(["Rating: "+rating[:3]])
                    writer.writerow(["Number of reviews: "+no_of_rating])
                    writer.writerow([extra_data])

            except Exception as e:
                pass

    else:
        print(f"Failed to fetch page: {url}")


def index(request):
    if request.method == "POST":
        url = 'https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_'

        for i in range(1, 25):
            scrape_page(url, i)

    return render(request, "index.html")
