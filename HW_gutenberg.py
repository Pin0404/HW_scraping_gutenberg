# ------------------------------------------------------
# 載入套件：靜態 HTML 用 requests + BeautifulSoup 即可爬取
# ------------------------------------------------------
import os
import re
import json
import random
from time import sleep
from pprint import pprint
import requests as req
from bs4 import BeautifulSoup as bs

# ------------------------------------------------------
# STEP1：由參考網站爬取"中文與標點"的正規表達式
# ------------------------------------------------------
regex_url = 'https://blog.typeart.cc/%E6%AD%A3%E5%89%87%E8%A1%A8%E9%81%94%E5%BC%8F-%E5%85%A8%E5%9E%8B%E8%8B%B1%E6%95%B8%E4%B8%AD%E6%96%87%E5%AD%97%E3%80%81%E5%B8%B8%E7%94%A8%E7%AC%A6%E8%99%9Funicode%E5%B0%8D%E7%85%A7%E8%A1%A8/#google_vignette'
res = req.get(regex_url)  # 發送 HTTP 請求取得文章內容
res.encoding = 'utf-8'  # 避免亂碼
soup = bs(res.text, "lxml")

regex_elements = soup.select('code')  # 將所有 <code> 標籤內的內容取出來
rg1 = '\\u4E00-\\u9FFF'  # 所有中文字
rg2_pattern = re.compile(r'\\u[A-Za-z0-9]{4}$')  # \ 是跳脫符號，若字串裡表示一個反斜線 \，要打兩個：\\

filtered_rg2 = []
for cd in regex_elements:
    rg2 = cd.get_text()
    if rg2_pattern.search(rg2): 
        filtered_rg2.append(rg2)

regex_str = "[" + rg1 + ''.join(filtered_rg2) + "]"
zh_pattern = re.compile(regex_str)

# ------------------------------------------------------
# STEP2：爬取古騰堡中文書籍目錄
# ------------------------------------------------------
link_url = "https://www.gutenberg.org/browse/languages/zh"
res = req.get(link_url)
res.encoding = 'utf-8'
soup = bs(res.text, "lxml")

zh_book_list = []
for a in soup.select('li.pgdbetext a[href]'):
    text = a.get_text(strip=True)
    link = a['href']
    zh_book = re.match(r'[\u4E00-\u9FFF]+', text)  #判斷 text 字串 是否是以一串中文字開頭
    link_match = re.match(r'^/ebooks/(\d+)$', link)
    # 若同時符合條件，就把資訊存起來
    if zh_book and link_match:
        book_name = zh_book.group(0)
        book_id = link_match.group(1)  # 取得每本書 id
        content_url = f'https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}-images.html'

        zh_book_list.append({
            'book_name': book_name,
            'book_id': book_id,
            'link': content_url
        })

# ------------------------------------------------------
# STEP3：由 content_url 逐本爬取中文內容，並儲存至資料夾
# ------------------------------------------------------

# 建立資料夾
os.makedirs("project_gutenberg", exist_ok=True)
print("=====已建立 project_gutenberg 資料夾=====")

# 從 zh_book_list 逐筆取出資料放入 book 變數
for i, book in enumerate(zh_book_list):
    try:  # 嘗試執行這段程式碼(可能報錯)
        # 如果 txt 檔案數量超過 books_count 就停止
        books_count = 210
        existing_files = [f for f in os.listdir("project_gutenberg") if f.endswith(".txt")]
        if len(existing_files) >= books_count:
            print(f"=====已超過{books_count}本書，停止爬取=====")
            break

        sleep(random.uniform(1, 3))   # 1~3 秒之間的隨機等待
        res = req.get(book['link'], timeout=10) # 設定最多等待 10 秒的逾時時間
        res.encoding = 'utf-8'
        soup = bs(res.text, "lxml")

        book_content = ""
        # select() CSS 選擇器無法吃 re.compile()
        for p in soup.find_all('p', id=re.compile(r'^id\d{5}$')):  # 選擇 id 名稱"idXXXXX"
            text = p.get_text(strip=True)
            zh_content = zh_pattern.findall(text)  # 只爬取中文
            if zh_content:
                book_content += ''.join(zh_content) + '\n'

        file_path = os.path.join("project_gutenberg", f"{book['book_name']}.txt")
        if book_content.strip():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(book_content)
            print(f"已儲存：{file_path}")
        else:
            print(f"無中文內容：{book['book_name']}")

    except Exception as e:  # 若上方程式出現錯誤，會進入這裡處理，印出錯誤訊息
        print(f"失敗：{book['book_name']} - {e}")
        continue




