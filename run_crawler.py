import pymysql
import schedule
import time
import argparse
from website.crawl.cnki_spiders import KeyList, main

# 连接数据库
def get_db_connection():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="123456",
        db="cnkidemo",
        charset='utf8'
    )

def crawl_with_keyword(keyword):
    db = get_db_connection()
    try:
        # 创建爬虫实例
        crawler = KeyList()
        # 使用传入的关键词进行爬取与关键词有关的文章链接
        crawler.crawl(keyword)
        # 通过链接爬取具体数据
        main(db)
        
    except Exception as e:
        print(f"爬虫运行出错: {str(e)}")
    finally:
        db.close()

def schedule_crawler(keyword, frequency, frequency_unit):
    # 清除所有已有的定时任务
    schedule.clear()
    
    # 根据不同的时间单位设置定时任务
    if frequency_unit == 'minutes':
        schedule.every(frequency).minutes.do(crawl_with_keyword, keyword=keyword)
    elif frequency_unit == 'hours':
        schedule.every(frequency).hours.do(crawl_with_keyword, keyword=keyword)
    elif frequency_unit == 'days':
        schedule.every(frequency).days.do(crawl_with_keyword, keyword=keyword)
    else:
        print(f"Unsupported frequency unit: {frequency_unit}")
        return
    
    print(f"已设置定时任务，每 {frequency} {frequency_unit} 爬取一次关键词 '{keyword}'")
    
    # 运行定时任务
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run the CNKI crawler with specified keyword and frequency.")
    # parser.add_argument('--keyword', type=str, required=True, help='The keyword to search for.')
    # parser.add_argument('--frequency', type=int, required=True, help='The frequency of the crawler.')
    # parser.add_argument('--frequency_unit', type=str, default='minutes', choices=['minutes', 'hours', 'days'], help='The unit of frequency (default: minutes).')
    #
    # args = parser.parse_args()
    #
    # schedule_crawler(args.keyword, args.frequency, args.frequency_unit)
    crawl_with_keyword("人")