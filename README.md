# django_N_add_1_queries_problem_tutorial

透過 django 介紹 N+1 Queries Problem

* [Youtube Tutorial - 透過 django 介紹 N+1 Queries Problem](https://youtu.be/trVzF-jBFTo)

## 環境安裝

```cmd
pip3 install -r requirements.txt
```

這裡面有使用到 [django-extensions](https://django-extensions.readthedocs.io/en/latest/), 主要是要看 raw SQL 做了什麼事情

## 介紹

[models.py](https://github.com/twtrubiks/django_N_add_1_queries_problem_tutorial/blob/main/books/models.py),

建立一些簡單的資料

Author

```text
id	name	country_id
1	author_1	1
2	author_2	2
3	author_3	3
```

Book

```text
id	name	author_id
1	book_1	    1
2	book_2	    2
3	book_3	    3
```

Country

```text
id	name
1	country_1
2	country_2
3	country_3
```

也可以從後台建立(觀看),

```cmd
python3 manage.py runserver
```

進入 [http://0.0.0.0:8000/admin/](http://0.0.0.0:8000/admin/)

```text
帳號/密碼: admin/admin
```

進入 shell_plus 操作資料,

```cmd
python3 manage.py shell_plus --print-sql
```

讓我們來看一個例子,

### 情境一

N+1 Queries

```cmd
>>> from books.models import Country, Author, Book
>>> books = Book.objects.all() # QuerySets are lazy # Doesn't hit the database.
>>> for book in books:
...     print(book.name, "by", book.author.name)
...
SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
Execution time: 0.000184s [Database: default]
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" = 1
 LIMIT 21
Execution time: 0.000178s [Database: default]
book_1 by author_1
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" = 2
 LIMIT 21
Execution time: 0.000191s [Database: default]
book_2 by author_2
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" = 3
 LIMIT 21
Execution time: 0.000202s [Database: default]
book_3 by author_3
```

book table 只有3筆資料, 但總共執行了 4 (N+1) 次 SQL,

1次是撈出全部的book, 剩下的3次, 是透過 author id 去撈作者的 name.

### 情境二

2N+1 Queries

假如今天我們 access 更多的 foreign key

```cmd
>>> from books.models import Country, Author, Book
>>> books = Book.objects.all() # QuerySets are lazy # Doesn't hit the database.
>>> for book in books:
...     print(book.name, "by", book.author.name, "from", book.author.country.name)
...
SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
Execution time: 0.000313s [Database: default]
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" = 1
 LIMIT 21
Execution time: 0.000086s [Database: default]
SELECT "country"."id",
       "country"."name"
  FROM "country"
 WHERE "country"."id" = 1
 LIMIT 21
Execution time: 0.000128s [Database: default]
book_1 by author_1 from country_1
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" = 2
 LIMIT 21
Execution time: 0.000112s [Database: default]
SELECT "country"."id",
       "country"."name"
  FROM "country"
 WHERE "country"."id" = 2
 LIMIT 21
Execution time: 0.000108s [Database: default]
book_2 by author_2 from country_2
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" = 3
 LIMIT 21
Execution time: 0.000254s [Database: default]
SELECT "country"."id",
       "country"."name"
  FROM "country"
 WHERE "country"."id" = 3
 LIMIT 21
Execution time: 0.000117s [Database: default]
book_3 by author_3 from country_3
```

book table 只有3筆資料, 但總共執行了 7 (2N+1) 次 SQL,

1次是撈出全部的book,

(1次是透過 author id 去撈作者的 name, 1次是透過 country id 去撈居住地點的 name.) * 2 次.

看了情境一(N+1 Queries), 以及情境二 (2N+1 Queries), 肯定會造成效能的影響:weary:

這樣在 Django ORM 上, 應該怎麼解決呢:question:

## 解決方法

### 方法一

`select_related()` [https://docs.djangoproject.com/en/4.1/ref/models/querysets/#select-related](https://docs.djangoproject.com/en/4.1/ref/models/querysets/#select-related)

官網說明如下,

```text
Returns a QuerySet that will “follow” foreign-key relationships, selecting additional related-object data when it executes its query. This is a performance booster which results in a single more complex query but means later use of foreign-key relationships won’t require database queries.
```

#### 情境一

N+1 Queries

```cmd
>>> from books.models import Country, Author, Book
>>> books = Book.objects.all().select_related("author") # QuerySets are lazy # Doesn't hit the database.
>>> for book in books:
...     print(book.name, "by", book.author.name)
...
SELECT "book"."id",
       "book"."name",
       "book"."author_id",
       "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "book"
 INNER JOIN "author"
    ON ("book"."author_id" = "author"."id")
Execution time: 0.000651s [Database: default]
book_1 by author_1
book_2 by author_2
book_3 by author_3
```

只使用了一次的 Query, 使用 Join 的方式解決了這個問題.

#### 情境二

2N+1 Queries

```cmd
>>> from books.models import Country, Author, Book
>>> books = Book.objects.all().select_related("author", "author__country") # QuerySets are lazy # Doesn't hit the database.
>>> for book in books:
...     print(book.name, "by", book.author.name, "from", book.author.country.name)
...
SELECT "book"."id",
       "book"."name",
       "book"."author_id",
       "author"."id",
       "author"."name",
       "author"."country_id",
       "country"."id",
       "country"."name"
  FROM "book"
 INNER JOIN "author"
    ON ("book"."author_id" = "author"."id")
 INNER JOIN "country"
    ON ("author"."country_id" = "country"."id")
Execution time: 0.000541s [Database: default]
book_1 by author_1 from country_1
book_2 by author_2 from country_2
book_3 by author_3 from country_3
```

只使用了一次的 Query, 使用 Join 兩個 table 的方式解決了這個問題.

### 方法二

`prefetch_related` [https://docs.djangoproject.com/en/4.1/ref/models/querysets/#prefetch-related](https://docs.djangoproject.com/en/4.1/ref/models/querysets/#prefetch-related)

官網說明如下,

```text
Returns a QuerySet that will automatically retrieve, in a single batch, related objects for each of the specified lookups.

This has a similar purpose to select_related, in that both are designed to stop the deluge of database queries that is caused by accessing related objects, but the strategy is quite different.

select_related works by creating an SQL join and including the fields of the related object in the SELECT statement. For this reason, select_related gets the related objects in the same database query. However, to avoid the much larger result set that would result from joining across a ‘many’ relationship, select_related is limited to single-valued relationships - foreign key and one-to-one.

prefetch_related, on the other hand, does a separate lookup for each relationship, and does the ‘joining’ in Python. This allows it to prefetch many-to-many and many-to-one objects, which cannot be done using select_related, in addition to the foreign key and one-to-one relationships that are supported by select_related. It also supports prefetching of GenericRelation and GenericForeignKey, however, it must be restricted to a homogeneous set of results. For example, prefetching objects referenced by a GenericForeignKey is only supported if the query is restricted to one ContentType.
```

#### 情境一

N+1 Queries

```cmd
>>> from books.models import Country, Author, Book
>>> books = Book.objects.all().prefetch_related("author") # QuerySets are lazy # Doesn't hit the database.
>>> for book in books:
...     print(book.name, "by", book.author.name)
...
SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
Execution time: 0.000486s [Database: default]
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" IN (1, 2, 3)
Execution time: 0.000735s [Database: default]
book_1 by author_1
book_2 by author_2
book_3 by author_3
```

和 `select_related` 不同的是, 使用了兩次的 Query,

一次找全部的 book,

第二次透過作者 id (ids) 一次找到全部的名稱.

#### 情境二

2N+1 Queries

```cmd
>>> from books.models import Country, Author, Book
>>> books = Book.objects.all().prefetch_related("author", "author__country") # QuerySets are lazy # Doesn't hit the database.
>>> for book in books:
...     print(book.name, "by", book.author.name, "from", book.author.country.name)
...
SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
Execution time: 0.000108s [Database: default]
SELECT "author"."id",
       "author"."name",
       "author"."country_id"
  FROM "author"
 WHERE "author"."id" IN (1, 2, 3)
Execution time: 0.000112s [Database: default]
SELECT "country"."id",
       "country"."name"
  FROM "country"
WHERE "country"."id" IN (1, 2, 3)
```

和 `select_related` 不同的是, 使用了三次的 Query,

一次找全部的 book,

第二次透過作者 id (ids) 一次找到全部的名稱.

第三次透過居住地 id (ids) 一次找到全部的名稱.

## 結論

至於要使用 `select_related` 還是 `prefetch_related` 我認為應該看使用情境,

`select_related` 可以只 Query 一次, 但 JOIN 還是需要一點成本.

```text
select_related is limited to single-valued relationships - foreign key and one-to-one.
```

`prefetch_related` Query 多次(依照你要取的 ForeignKey 數量), 但執行比較不需要成本的 Query.

```text
prefetch_related can work many-to-many and many-to-one objects
```

## 執行環境

* Python 3.9

## Reference

* [Django](https://www.djangoproject.com/)

* [Django and the N+1 Queries Problem](https://scoutapm.com/blog/django-and-the-n1-queries-problem)

## Donation

文章都是我自己研究內化後原創，如果有幫助到您，也想鼓勵我的話，歡迎請我喝一杯咖啡:laughing:

![alt tag](https://i.imgur.com/LRct9xa.png)

[贊助者付款](https://payment.opay.tw/Broadcaster/Donate/9E47FDEF85ABE383A0F5FC6A218606F8)

## License

MIT license