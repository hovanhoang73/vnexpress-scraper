# ***Cài đặt thư viện***:
# Cài BeautifulSoup4 và Schedule
#pip install beautifulsoup4
#pip install schedule

# ***Import thư viện***
from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from urllib.parse import urljoin
import schedule
import time

# Website tin tức
website = "https://vnexpress.net/"

# Thêm User-Agent để tránh bị chặn
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
}

# ***MỤC 1: Truy cập vào trang chủ***
try:
    response = requests.get(website)
    if response.status_code == 200:
        print("Truy cập thành công!")
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Tiêu đề trang:", soup.title.text)
    else:
        print("Truy cập thất bại! Mã trạng thái:", response.status_code)
except requests.exceptions.RequestException as e:
    print("Truy cập thất bại! Lỗi:", e)

# ***MỤC 2: Click chọn một mục tin tức***
try:
    response = requests.get(website)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.find('a', href='/khoa-hoc-cong-nghe')
        if link:
            news_url = website.rstrip('/') + link['href']
            news_response = requests.get(news_url)
            if news_response.status_code == 200:
                print("Truy cập Khoa học công nghệ thành công!")
                print(f"URL: {news_url}")
            else:
                print("Truy cập Khoa học công nghệ thất bại! Mã trạng thái:", news_response.status_code)
        else:
            print("Không tìm thấy mục 'Khoa học công nghệ'!")
    else:
        print("Truy cập thất bại! Mã trạng thái:", response.status_code)
except requests.exceptions.RequestException as e:
    print("Truy cập thất bại! Lỗi:", e)

# ***MỤC 3: Tìm kiếm nội dung***
content = input("Nhập nội dung cần tìm kiếm: ")

try:
    response = requests.get(website)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        search_form = soup.find('form', id='formSearchHeader')
        if search_form:
            search_url = search_form['action']
            search_params = {'q': content}
            search_response = requests.get(search_url, params=search_params)
            if search_response.status_code == 200:
                print("Gửi yêu cầu tìm kiếm thành công!")
                print(f"URL tìm kiếm: {search_response.url}")
            else:
                print("Gửi yêu cầu tìm kiếm thất bại! Mã trạng thái:", search_response.status_code)
        else:
            print("Không tìm thấy nút tìm kiếm trên trang!")
    else:
        print("Truy cập thất bại! Mã trạng thái:", response.status_code)
except requests.exceptions.RequestException as e:
    print("Truy cập thất bại! Lỗi:", e)

# ***MỤC 4: Lấy tất cả dữ liệu hiển thị ở bài viết***
def scrape_vnexpress_khcn_all_pages():
    base_url = "https://vnexpress.net"
    category_url = base_url + "/khoa-hoc-cong-nghe"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/58.0.3029.110'}
    articles = []
    seen_urls = set()

    def scrape_page(url, session):
        try:
            response = session.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Truy cập {url} thất bại! Mã trạng thái: {response.status_code}")
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all(['h3', 'h4'], class_='title-news')

            for item in news_items:
                article = {'Title': '', 'Description': '', 'Image': '', 'Content': '', 'URL': ''}
                title_tag = item.find('a')
                if title_tag:
                    article['Title'] = title_tag.text.strip()
                    article['URL'] = urljoin(base_url, title_tag.get('href', ''))
                parent_container = item.find_parent('article') or item.find_parent('div', class_=re.compile('item|news'))
                if parent_container:
                    description_tag = parent_container.find('p', class_='description')
                    article['Description'] = description_tag.text.strip() if description_tag else ''
                thumb_tag = parent_container.find('div', class_='thumb-art') if parent_container else None
                img_tag = thumb_tag.find('img') if thumb_tag else None
                article['Image'] = img_tag.get('src', '') if img_tag else ''

                if article['Title'] and article['URL'] and article['URL'] not in seen_urls:
                    seen_urls.add(article['URL'])
                    articles.append(article)

            next_page = soup.find('a', class_='next-page')
            return urljoin(base_url, next_page.get('href', '')) if next_page else None

        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi truy cập {url}: {e}")
            return None

    def scrape_article_content(url, session):
        try:
            response = session.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Truy cập bài viết {url} thất bại! Mã trạng thái: {response.status_code}")
                return ''
            soup = BeautifulSoup(response.text, 'html.parser')
            content_container = soup.find(['article', 'div'], class_='fck_detail')
            if content_container:
                paragraphs = content_container.find_all('p')
                return ' '.join(p.text.strip() for p in paragraphs if p.text.strip())
            print(f"Không tìm thấy nội dung tại {url} (thiếu thẻ fck_detail)")
            return ''
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi truy cập bài viết {url}: {e}")
            return ''

    with requests.Session() as session:
        current_url = category_url
        while current_url:
            print(f"Đang thu thập dữ liệu từ: {current_url}")
            next_page = scrape_page(current_url, session)
            current_url = next_page

        for article in articles:
            print(f"Đang lấy nội dung từ: {article['URL']}")
            article['Content'] = scrape_article_content(article['URL'], session)

    csv_file = 'VnExpress_KHCN.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Title', 'Description', 'Image', 'Content']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            article.pop('URL', None)
            writer.writerow(article)

    print(f"Dữ liệu đã được lưu vào {csv_file}. Tổng số bài viết: {len(articles)}")

# ***MỤC 5: Chạy ngay lập tức***
app = Flask(__name__)

@app.route('/')
def show_articles():
    base_url = "https://vnexpress.net"
    category_url = base_url + "/khoa-hoc-cong-nghe"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/58.0.3029.110'}
    articles = []
    seen_urls = set()

    def scrape_page(url, session):
        try:
            response = session.get(url, headers=headers)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all(['h3', 'h4'], class_='title-news')

            for item in news_items:
                article = {'Title': '', 'Description': '', 'Image': '', 'URL': ''}
                title_tag = item.find('a')
                if title_tag:
                    article['Title'] = title_tag.text.strip()
                    article['URL'] = title_tag.get('href', '')
                parent = item.find_parent('article') or item.find_parent('div', class_=re.compile('item|news'))
                if parent:
                    desc_tag = parent.find('p', class_='description')
                    article['Description'] = desc_tag.text.strip() if desc_tag else ''
                thumb_tag = parent.find('div', class_='thumb-art') if parent else None
                img_tag = thumb_tag.find('img') if thumb_tag else None
                article['Image'] = img_tag.get('src', '') if img_tag else ''

                if article['Title'] and article['URL'] and article['URL'] not in seen_urls:
                    seen_urls.add(article['URL'])
                    articles.append(article)
            return None
        except requests.exceptions.RequestException:
            return None

    with requests.Session() as session:
        scrape_page(category_url, session)

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>VnExpress Khoa Học Công Nghệ</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .article { margin-bottom: 30px; }
            img { max-width: 400px; height: auto; display: block; }
        </style>
    </head>
    <body>
        <h1>Tin Khoa Học Công Nghệ từ VnExpress</h1>
        {% for article in articles %}
            <div class="article">
                <h2><a href="{{ article.URL }}" target="_blank">{{ article.Title }}</a></h2>
                <p>{{ article.Description }}</p>
                {% if article.Image %}
                    <img src="{{ article.Image }}">
                {% endif %}
            </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html_template, articles=articles)

if __name__ == '__main__':
    app.run(debug=True)

# ***MỤC 6: Đặt lịch chạy hàng ngày vào lúc 6h sáng***
#def job():
#   print("Bắt đầu thu thập dữ liệu lúc 6h sáng...")
#  scrape_vnexpress_khcn_all_pages()

# Đặt lịch chạy vào 6h sáng hằng ngày
#schedule.every().day.at("06:00").do(job)

#print("Đã đặt lịch chạy vào 6h sáng hằng ngày. Đang chờ...")
#while True:
#   schedule.run_pending()
#    time.sleep(60)  # Kiểm tra lịch mỗi phút