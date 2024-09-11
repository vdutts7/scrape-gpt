import os
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Type

import pandas as pd
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, create_model
import html2text
import tiktoken

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from openai import OpenAI

load_dotenv()

# Set up the Chrome WebDriver options

def setup_selenium():
    options = Options()

    # adding arguments
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Randomize user-agent to mimic different users
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # Specify the path to the ChromeDriver
    service = Service(r"./chromedriver-win64/chromedriver.exe")  

    # Initialize the WebDriver
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def fetch_html_selenium(url):
    driver = setup_selenium()
    try:
        driver.get(url)
        
        # Add random delays to mimic human behavior
        time.sleep(5)  # Adjust this to simulate time for user to read or interact
        
        # Add more realistic actions like scrolling
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Simulate time taken to scroll and read
        
        html = driver.page_source
        return html
    finally:
        driver.quit()

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove headers and footers based on common HTML tags or classes
    for element in soup.find_all(['header', 'footer']):
        element.decompose()  # Remove these tags and their content

    return str(soup)


def html_to_markdown_with_readability(html_content):

    
    cleaned_html = clean_html(html_content)  
    
    # Convert to markdown
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False
    markdown_content = markdown_converter.handle(cleaned_html)
    
    return markdown_content



if __name__ == "__main__":
    url = 'https://news.ycombinator.com/'
    fields=['Title', 'Number of Points', 'Creator', 'Time Posted', 'Number of Comments']

    try:
        # # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Scrape data
        raw_html = fetch_html_selenium(url)
    
        markdown = html_to_markdown_with_readability(raw_html)
        
        # Save raw data
        save_raw_data(markdown, timestamp)

        # Create the dynamic listing model
        DynamicListingModel = create_dynamic_listing_model(fields)

        # Create the container model that holds a list of the dynamic listing models
        DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
        
        # Format data
        formatted_data = format_data(markdown, DynamicListingsContainer)  # Use markdown, not raw_html
        
        # Save formatted data
        save_formatted_data(formatted_data, timestamp)

        # Convert formatted_data back to text for token counting
        formatted_data_text = json.dumps(formatted_data.dict()) 
        
        
        # Automatically calculate the token usage and cost for all input and output
        input_tokens, output_tokens, total_cost = calculate_price(markdown, formatted_data_text, model=model_used)
        print(f"Input token count: {input_tokens}")
        print(f"Output token count: {output_tokens}")
        print(f"Estimated total cost: ${total_cost:.4f}")

    except Exception as e:
        print(f"An error occurred: {e}")
        