import pymysql
from website.crawl.cnki_spiders import KeyList, main

# 连接数据库
db = pymysql.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="123456",
    db="cnkidemo",
    charset='utf8'
)

if __name__ == "__main__":
    try:
        # 方式1：按关键词爬取
        crawler = KeyList()
        crawler.crawl("你想搜索的关键词")
        
        # 或者方式2：运行主爬虫程序
        # main(db)
        
    except Exception as e:
        print(f"爬虫运行出错: {str(e)}")
    finally:
        db.close() 