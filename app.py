from flask import Flask, render_template,request
from bs4 import BeautifulSoup as bs
from flask_cors import CORS, cross_origin
import requests
from urllib.request import urlopen as uReq
import logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import re
import csv
import pandas as pd

app = Flask(__name__)

@app.route("/")
@cross_origin()
def home():
    return render_template("index.html")

@app.route("/scrap",methods=['POST'])
@cross_origin()
def scrape():
    if request.method == 'POST':
        try: 
        	#driver setup
            chrome_service = ChromeService(executable_path=ChromeDriverManager().install())
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
           # getting page source
            youtube_url = request.form['content'].replace(" ","")
            driver.get(youtube_url)
            driver.implicitly_wait(10)
            youtube_source = driver.page_source
            youtube_html = bs(youtube_source, "html.parser")

           ## extract video urls (first 5)
            youtube_a_tags = youtube_html.find_all('a',class_="ytd-thumbnail")
            youtube_a_tags = youtube_a_tags[1:6]
            youtube_extract_urls = []
            for i in youtube_a_tags:
               youtube_extract_urls.append("https://www.youtube.com/"+i.get('href'))
               
		  ## extract thumbnail url
            youtube_extract_thumbnails = []
            for i in youtube_extract_urls:
                driver.get(i)
                video_page_source = bs(driver.page_source,"html.parser")
                find = video_page_source.find('link',itemprop="thumbnailUrl")
                youtube_extract_thumbnails.append(find['href'])
		   ###extract video title
            youtube_heading_tags = youtube_html.find_all('h3',class_="style-scope ytd-rich-grid-media")
            youtube_heading_tags = youtube_heading_tags[:5]
            youtube_extract_titles = []
            for i in youtube_heading_tags:
                youtube_extract_titles.append(i.text)
			
			
			#no of views
            youtube_span_tags = youtube_html.find_all('span',class_="inline-metadata-item style-scope ytd-video-meta-block")
            views_pattern = re.compile("\d+.*views")
            views_spans = []
            for span in youtube_span_tags:
                if views_pattern.search(span.text):
                      views_spans.append(span)
            youtube_extract_views=[]
            views_spans = views_spans[:5]
            for span in views_spans:
                youtube_extract_views.append(span.text)
           

			#	 time of upload

            views_pattern = re.compile("\d+.*ago")
            views_spans = []
            for span in youtube_span_tags:
                if views_pattern.search(span.text):
                      views_spans.append(span)
            views_spans = views_spans[:5]
            youtube_extract_upload_time = []
            for span in views_spans:
                youtube_extract_upload_time.append(span.text)

            driver.close()

            # save data to csv
            data = { 'Youtube Urls': youtube_extract_urls,
                        'Thumbnails':youtube_extract_thumbnails,
                        'Titles':youtube_extract_titles,
                        'Views': youtube_extract_views,
                        'Upload Time':youtube_extract_upload_time
                    }
            df = pd.DataFrame(data)

            df.to_csv('data.csv', index=False)


            #return 'working' 
            return render_template('results.html',data=data)

        except Exception as e:
           print(e)
           return 'Something Went Wrong! '
    else:
        render_template('index.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1',port=8000, debug=True)