import time
import unittest

import pymysql
from py2neo import Graph, Node, Relationship

from website.crawl.build_neo4j import *

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
USERNAME = "root"
PASSWORD = "123456"
DATABASE = "cnkidemo"

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379


class MyTestCase(unittest.TestCase):
    def test_setCONSTRAINT(self):
        try:
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            g.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:article) REQUIRE n.url IS UNIQUE")
            g.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:author) REQUIRE n.url IS UNIQUE")
            g.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:source) REQUIRE n.url IS UNIQUE")
            g.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:organization) REQUIRE n.url IS UNIQUE")
        except:
            self.assertTrue(False, '储存文章作者关系-创建约束异常')

    def test_setStatus(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD, db=DATABASE, port=MYSQL_PORT,
                                 charset='utf8')
            setStatus(db, 'article', 'dbcode=CAPJ&dbname=CAPJDAY&filename=JEXK20210511001', 0)
        except:
            self.assertTrue(False, '设置状态位异常')

    def test_setstatus_target(self):
        """状态位设置"""
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            setstatus_target(db, 'article', 0)
            setstatus_target(db, 'author', 0)
            db.close()
        except:
            self.assertTrue(False, '将状态位置异常')

    def test_setstatusRE_target(self):
        """状态位关系设置"""
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            setStatusRE_target(db, 're_article_author', 'url_article', 'url_author', 0)
            db.close()
        except:
            self.assertTrue(False, '将状态位置异常')

    def test_saveArticle(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_article(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储文章节点neo4j异常')

    def test_saveAuthor(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_author(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储作者节点neo4j异常')

    def test_saveSource(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_source(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储文献来源节点neo4j异常')

    def test_saveOrganization(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_organization(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储组织节点neo4j异常')

    def test_saveREAA(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_re_article_author(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储文章-作者关系neo4j异常')

    def test_saveREAS(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_re_article_source(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储文章-来源关系neo4j异常')

    def test_saveREAO(self):
        """测试作者-组织"""
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_re_author_organization(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储作者组织关系neo4j异常')

    def test_saveRETS(self):
        try:
            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            save_re_teacher_student(db, g)
            db.close()
        except:
            self.assertTrue(False, '存储师生关系neo4j异常')

    def test_main(self):
        try:
            start = time.time()

            db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD,
                                 db=DATABASE, port=MYSQL_PORT, charset='utf8')
            g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
            main(db, g)
            # save_article(db, g)
            # save_author(db, g)
            # save_source(db, g)
            # save_organization(db, g)
            # save_re_article_author(db, g)
            # save_re_article_source(db, g)
            # save_re_author_organization(db, g)
            # save_re_teacher_student(db, g)
            db.close()

            end = time.time()
            t = end - start
            m, s = divmod(t, 60)
            h, m = divmod(m, 60)
            print("程序耗时 {:.0f}时 {:.0f}分 {:.0f}秒".format(h, m, s))
        except:
            self.assertTrue(False, '存储作者节点neo4j异常')


if __name__ == '__main__':
    unittest.main()
