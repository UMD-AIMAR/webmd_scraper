#!/usr/bin/env python
# coding: utf-8
import requests
import json
from tqdm import tqdm
from bs4 import BeautifulSoup
from requests_html import HTMLSession

WEBMD = "https://symptomchecker.webmd.com/"
AZ = 'symptoms-a-z/'


def get_page_links(soup):
    page_links = []
#     print(soup.select('ul.list_page_links'))
    pagination = soup.select('ul.list_page_links')
    if len(pagination) == 0:
        return page_links
    for li in pagination[0].select('li'):
        if li.get('class') is None:
            link = li.find('a').get('href')
            if link != "":
                page_links.append(link)
    return page_links


def associated_conditions(tup):
    symptoms_str, link = tup
    conditions = []
    soup_multiple_symptom_page_n = BeautifulSoup(requests.get(WEBMD + link).text)
    for x in soup_multiple_symptom_page_n.select('.results_list .bg a'):
        conditions.append((x.text, set(symptoms_str.split(',')), x.get('href')))
    return conditions


# We start by scraping all the single symptoms on the WebMD Symptoms A-Z page.
def scrape_single_symptoms():
    soup_az = BeautifulSoup(requests.get(WEBMD + AZ).text)
    single_symptoms = []
    for x in soup_az.select('#list_az .bg'):
        single_symptoms.append((x.find('a').text, x.find('a').get('href')))
    return single_symptoms

# Each of these has multiple associated pages, so we scrape the URLs of those.
# single_symptoms should be a list of (name, href) tuples.
def scrape_single_symptoms_pagination(single_symptoms):
    page_links = []
    for name, link in tqdm(single_symptoms):
        soup_single_symptom = BeautifulSoup(requests.get(WEBMD + link).text)
        page_links += [link] + get_page_links(soup_single_symptom)
    return page_links


# On each one of these pages, possible groups of symptoms are listed together as single links.
def scrape_multiple_symptoms(page_links):
    multiple_symptoms = []
    for page_link in tqdm(page_links):
        soup_single_symptom_page_n = BeautifulSoup(requests.get(WEBMD + page_link).text)
        for x in soup_single_symptom_page_n.select('.results_table td a'):
            multiple_symptoms.append((x.text, x.get('href')))
    multiple_symptoms = list(set(multiple_symptoms))


# In each of these, we find conditions that correspond to the listed symptoms.
# This one takes a while so we'll save to a file once we finish.
def scrape_conditions(multiple_symptoms):
    conditions_dict = {}
    for symptoms_str, link in tqdm(multiple_symptoms):
        soup_multiple_symptom_page_n = BeautifulSoup(requests.get(WEBMD + link).text)
        for x in soup_multiple_symptom_page_n.select('.results_list .bg a'):
            conditions_dict[x.text] = {
                'symptoms': symptoms_str.split(', '),
                'link': x.get('href')
            }

    with open('conditions.json', 'w') as f:
        json.dump(conditions_dict, f)
    
    return conditions_dict

# single_symptoms = scrape_single_symptoms()
# page_links = scrape_single_symptoms_pagination(single_symptoms)
# multiple_symptoms = scrape_multiple_symptoms(page_links)
# conditions = scrape_conditions(multiple_symptoms)

with open('conditions.json') as f:
    conditions_dict = json.load(f)

failed = []
cdir = 'condition_pages'
for condition_name, data_dict in tqdm(conditions_dict.items()):
    session = HTMLSession()
    resp = session.get(data_dict['link'])
    resp.html.render()
    condition_page = BeautifulSoup(resp.html.html, features="lxml")
    for section in condition_page.select('.article-section'):
        section_name = section.find('h3').text
        section_content = section.find('p')
        if section_content is not None:
            read_more = section_content.find('a', class_='read-more')
            if read_more is not None:
                read_more.decompose()
            conditions_dict[condition_name][section_name] = section_content.text
    try:
        resp.close()
        session.close()
    except:
        print("Failed to close session for", condition_name)
        failed.append(condition_name)
print(failed)

with open('conditions_clean.json', 'w') as f:
    json.dump(conditions_dict, f)
