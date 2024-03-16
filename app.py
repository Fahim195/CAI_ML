from flask import Flask, request, render_template, redirect, jsonify
import os
import requests
from bs4 import BeautifulSoup
import re
from google.cloud import vision
import psycopg2

app = Flask(__name__)

# google image server credential
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'quixotic-market-402116-2387e32a1e73.json'
client = vision.ImageAnnotatorClient()



db_params = {
    "database": "CIMLA_DB",
    'user': "postgres",
    "password": "Y(q%Gz53dM!6MIjg",
    "host": "lms.cegmhknb2qgj.us-east-2.rds.amazonaws.com",
    "port": "5432"
}

@app.route('/')
def index():
    return render_template("index.html")
@app.route('/apitest')
def home():
    return render_template("apitest.html")

@app.route('/knowledge')
def knowledge():
    return render_template("knowledge.html")



def find_image_urls(htmlContent, keyword):
    soup = BeautifulSoup(htmlContent,"html.parser")
    i = 0
    data = {}
    keys = ["keyword", "urls"]
    values = []
    for link in soup.findAll('img', attrs={'src': re.compile("^https://")}):
        i = i + 1
        if i <= 20:
            values.extend([link.get('src')])
        else:
            break
    data[keys[0]] = keyword
    data[keys[1]] = values
    return data


def fetch_keyword_based_image(keyword):
    base_url_being = 'https://www.bing.com/images/search?q='
    api_url = base_url_being + keyword
    response = requests.get(api_url)
    return find_image_urls(response.text, keyword)


@app.route('/search', methods=['post'])
def search():
    val = request.form['query']
    data2 = fetch_keyword_based_image(val)
    # print('data2', data2)
    return render_template("apitest.html", data1=data2)


def create_image_table():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS cimla_searchhistory( cimla_id int, id serial PRIMARY KEY, label text, url text, labels text[], clicking_images text, unique_label text, created_at timestamp without time zone default now());CREATE TABLE IF NOT EXISTS cimla_keyword_search(cimla_id serial PRIMARY KEY,user_IP text,search_keyword text,created_at timestamp without time zone default now())""")

    conn.commit()
    cur.close()
    conn.close()


create_image_table()


def insert_search_log(results, clicking_images,unique_elements,user_ip,keyword):
    #print(user_ip,keyword)
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cimla_keyword_search (user_IP,search_keyword) VALUES (%s, %s)",(user_ip,keyword))
    # cimla_keyword_search_ID = cur.fetchall()
    conn.commit()
    cur.close()

    cur1 = conn.cursor()
    cur1.execute("Select MAX(cimla_id) as cimla_id from cimla_keyword_search")
    cur1Data=cur1.fetchall()
    print('cur1Data', cur1Data)
    cimla_keyword_search_ID=0
    for row in cur1Data:
        cimla_keyword_search_ID=row[0]

    print('cimla_keyword_search_ID', cimla_keyword_search_ID)
    #print('Without Reg ',cimla_keyword_search_ID)

    #cimla_keyword_search_ID=re.search (r'\d+', cimla_keyword_search_ID)
    #print('After Reg ',cimla_keyword_search_ID)
    cur1.close()

    cur2 = conn.cursor()
    for result in results:
        cur2.execute("INSERT INTO cimla_searchhistory (cimla_id,label, url, labels, clicking_images, unique_label) VALUES (%s, %s, %s, %s,%s,%s)",
                    (cimla_keyword_search_ID, result['label'], result['url'], result['labels'], clicking_images, unique_elements))
    cur2.close()
    conn.commit()
    conn.close()

def detect_labels_uri(uri):
    image = vision.Image()
    image.source.image_uri = uri

    response = client.label_detection(image=image)
    labels = response.label_annotations

    detected_labels = [label.description for label in labels]
    return detected_labels


@app.route('/predict', methods=['post'])
def process_selected_images():
    user_ip = request.remote_addr
    post_request_body = request.get_json()
    print('post_request_body', post_request_body)
    results = []
    all_labels = []
    print('Indexing Initiated')
    for index, url in enumerate(post_request_body[3], start=1):
        print('url', url)
        # if url != '':
        try:
            labels = detect_labels_uri(url)
            result = {
                'label': f'image_{index}',
                'url': url,
                'labels': labels
            }
            results.append(result)
        except Exception as e:
            result = {
                'label': f'image_{index}',
                'error': str(e)
            }
            results.append(result)
    for res in results:
        label = res['labels']
        all_labels.append(label)
    #print("all labels are", all_labels)

    flattened_data = [item for inner_list in all_labels for item in inner_list]
    unique_elements = list(set(flattened_data))
    # print(unique_elements)

    insert_search_log(results, post_request_body[3], unique_elements, user_ip, post_request_body[1])
    # print("save on Database")

    return jsonify(results, unique_elements)


def viewFromImageTable():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("SELECT * FROM ciml_searchhistory")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.route('/pass_result', methods=['get'])
def past_logs():
    past_info = viewFromImageTable()
    for data in past_info:
        print(data[1])
        print(data[2])
        print(data[3])
        print(data[4])
        break
    return render_template("check.html", past_info = past_info)


@app.route('/serach_history', methods=['get'])
def _search_hostiry():
 src_history_items=get_ser_history_DB()
 return jsonify(src_history_items)

def get_ser_history_DB():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("Select cimla_id,search_keyword,created_at::DATE AS date,created_at  from cimla_keyword_search created_at order by created_at desc limit 10;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.route('/serach_history_details', methods=['post'])
def _search_hostiry_details():
    request_body = request.get_json()
    print('request_body',request_body)
    src_ID=request_body[1]
    print('src_ID', src_ID)
    src_history_details = get_ser_history_details_DB(src_ID)
    return jsonify(src_history_details)

def get_ser_history_details_DB(cimla_id):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    tempVAR="array(Select labels from cimla_searchhistory where cimla_id="+str(cimla_id)+")"
    get_ser_history_details_DB_query="Select cimla_keyword_search.cimla_id,cimla_keyword_search.search_keyword,cimla_searchhistory.clicking_images,"+tempVAR+",cimla_searchhistory.unique_label from cimla_keyword_search left join cimla_searchhistory on cimla_keyword_search.cimla_id=cimla_searchhistory.cimla_id where cimla_keyword_search.cimla_id="+str(cimla_id)+"limit 1";
    print(get_ser_history_details_DB_query)
    cur.execute(get_ser_history_details_DB_query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows




if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=False)
