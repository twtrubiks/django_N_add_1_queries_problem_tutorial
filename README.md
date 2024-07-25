# django_N_add_1_queries_problem_tutorial

透過 django 介紹 N+1 Queries Problem

* [Youtube Tutorial - 透過 django 介紹 N+1 Queries Problem](https://youtu.be/trVzF-jBFTo)

## 環境安裝

```cmd
pip3 install -r requirements.txt
```

這裡面有使用到 [django-extensions](https://django-extensions.readthedocs.io/en/latest/), 主要是要看 raw SQL 做了什麼事情

## 介紹

[models.py](https://github.com/twtrubiks/django_N_add_1_queries_problem_tutorial/blob/main/books/models.py)

建立一些簡單的資料

Author

```sql
postgres=# SELECT * FROM public.author;
 id |   name   | country_id
----+----------+------------
  1 | author_1 |          1
  2 | author_2 |          2
  3 | author_3 |          3
(3 rows)
```

Book

```sql
postgres=# SELECT * FROM public.book;
 id |  name  | author_id
----+--------+-----------
  1 | book_1 |         1
  2 | book_2 |         2
  3 | book_3 |         3
(3 rows)
```

Country

```sql
postgres=# SELECT * FROM public.country;
 id |   name
----+-----------
  1 | country_1
  2 | country_2
  3 | country_3
(3 rows)
```

User

```sql
postgres=# SELECT * FROM public."user";
 id | name
----+-------
  1 | user1
  2 | user2
  3 | user3
(3 rows)
```

Tag

```sql
postgres=# SELECT * FROM public.tag;
 id | name  | created_by_id
----+-------+---------------
  1 | tag_1 |             1
  3 | tag_3 |             3
  2 | tag_2 |
(3 rows)
```

book_tags

(ManyToManyField 自動產出來的表, 紀錄 Book 和 Tag 的關係)

```sql
postgres=# SELECT * FROM public.book_tags;
 id | book_id | tag_id
----+---------+--------
  1 |       1 |      1
  2 |       1 |      2
  3 |       2 |      3
(3 rows)
```

先 migrate 後匯入測試資料

```cmd
python manage.py migrate
python manage.py loaddata db.json
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

看了情境一(N+1 Queries), 以及情境二 (2N+1 Queries), 肯定會造成效能的影響 :weary:

這樣在 Django ORM 上, 應該怎麼解決呢 :question:

### 情境三

也來看一下 ManyToManyField 的情境

```cmd
from books.models import Country, Author, Book, Tag
>>> books = Book.objects.all()
>>> for book in books:
...     print(book.tags.all())
...

SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
Execution time: 0.001057s [Database: default]
SELECT "tag"."id",
       "tag"."name",
       "tag"."created_by_id"
  FROM "tag"
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE "book_tags"."book_id" = 1
 LIMIT 21
Execution time: 0.001094s [Database: default]
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>
SELECT "tag"."id",
       "tag"."name",
       "tag"."created_by_id"
  FROM "tag"
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE "book_tags"."book_id" = 2
 LIMIT 21
Execution time: 0.000927s [Database: default]
<QuerySet [<Tag: tag_3>]>
SELECT "tag"."id",
       "tag"."name",
       "tag"."created_by_id"
  FROM "tag"
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE "book_tags"."book_id" = 3
 LIMIT 21
Execution time: 0.000973s [Database: default]
<QuerySet []>
```

一次 SQL 取出全部的 book,

二次 SQL 直接 JOIN book_tags, 然後透過 WHERE 的方式, 將需要的資料拿出來,

因為 book 有三筆資料, 就分別 JOIN 了 3 次 (效能不好).

## 解決方法

### 方法一

`select_related()` [https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-related](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-related)

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

`prefetch_related` [https://docs.djangoproject.com/en/5.0/ref/models/querysets/#prefetch-related](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#prefetch-related)

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

#### 情境三

ManyToManyField 的情境

```cmd
>>> from books.models import Country, Author, Book, Tag
>>> books = Book.objects.all().prefetch_related("tags")
>>> for book in books:
...     print(book.tags.all())
...

SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
Execution time: 0.001068s [Database: default]
SELECT ("book_tags"."book_id") AS "_prefetch_related_val_book_id",
       "tag"."id",
       "tag"."name",
       "tag"."created_by_id"
  FROM "tag"
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE "book_tags"."book_id" IN (1, 2, 3)
Execution time: 0.000886s [Database: default]
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>
<QuerySet [<Tag: tag_3>]>
<QuerySet []>
```

一次 SQL 取出全部的 book,

二次 SQL 直接 JOIN book_tags, 然後透過 WHERE IN 的方式, 一口氣將需要的資料拿出來,

當在 loop 的時候, 其實也都是去快取(cache) 裡面取資料而已(不會 access db).

#### 更複雜的情境

假設今天我們的 ManyToManyField tags 裡面還有一個 ForeignKey created_by,

這樣應該如何一起把它 JOIN 起來呢 ❓ 這時候就必須透過 [Prefetch](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#django.db.models.Prefetch)

以下範例是只撈出 Tag 裡面有 created_by 值得內容,

```cmd
>>> from books.models import Country, Author, Book, Tag, User
>>> from django.db.models import Prefetch
>>> queryset = Tag.objects.select_related("created_by").filter(created_by__isnull=False)
>>> books = Book.objects.prefetch_related(Prefetch("tags", queryset=queryset, to_attr="tag_has_created_by"))
>>> for book in books:
...     for tag in book.tag_has_created_by:
...         print(tag.created_by)
...

SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
Execution time: 0.001034s [Database: default]
SELECT ("book_tags"."book_id") AS "_prefetch_related_val_book_id",
       "tag"."id",
       "tag"."name",
       "tag"."created_by_id",
       "user"."id",
       "user"."name"
  FROM "tag"
 INNER JOIN "user"
    ON ("tag"."created_by_id" = "user"."id")
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE ("tag"."created_by_id" IS NOT NULL AND "book_tags"."book_id" IN (1, 2, 3))
Execution time: 0.001113s [Database: default]
user1
user3
```

你會發現 JOIN 了兩次, 一次是針對 book_tags, 另一次是針對 created_by (user).

#### prefetch_related_objects

如果今天你使用了 `model.all()`, 它不會有快取,

因為對 django 來說, 他是一份新的.

所以這時候可以透過 [prefetch_related_objects](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#prefetch-related-objects) 快取起來.

`prefetch_related_objects(model_instances, *related_lookups)`

```cmd
>>> from books.models import Country, Author, Book, Tag, User
>>> book = Book.objects.first()
SELECT "book"."id",
       "book"."name",
       "book"."author_id"
  FROM "book"
 ORDER BY "book"."id" ASC
 LIMIT 1
Execution time: 0.000815s [Database: default]
>>> book.tags.all() # query db
SELECT "tag"."id",
       "tag"."name",
       "tag"."created_by_id"
  FROM "tag"
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE "book_tags"."book_id" = 1
 LIMIT 21
Execution time: 0.001145s [Database: default]
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>
>>> book.tags.all() # query db
SELECT "tag"."id",
       "tag"."name",
       "tag"."created_by_id"
  FROM "tag"
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE "book_tags"."book_id" = 1
 LIMIT 21
Execution time: 0.001164s [Database: default]
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>

>>> from django.db.models import prefetch_related_objects
>>> prefetch_related_objects([book], "tags")
SELECT ("book_tags"."book_id") AS "_prefetch_related_val_book_id",
       "tag"."id",
       "tag"."name",
       "tag"."created_by_id"
  FROM "tag"
 INNER JOIN "book_tags"
    ON ("tag"."id" = "book_tags"."tag_id")
 WHERE "book_tags"."book_id" IN (1)
Execution time: 0.001192s [Database: default]
>>> book.tags.all() # use cache
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>
>>> book.tags.all() # use cache
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>
>>> book.tags.all() # use cache
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>
>>> book.tags.all() # use cache
<QuerySet [<Tag: tag_1>, <Tag: tag_2>]>
```

可以發現當我們使用了 prefetch_related_objects, 就會直接從快取拿資料.

## 結論

`select_related` 可以只 Query 一次, 但 JOIN 還是需要一點成本.

通常使用在 OneToOne(一對一) 或 ForeignKey(多對一), 透過 join 降低查詢次數.

```text
select_related is limited to single-valued relationships - foreign key and one-to-one.
```

`prefetch_related` Query 多次(依照你要取的 ForeignKey 數量), 但執行比較不需要成本的 Query.

通常使用在 OneToMany(一對多) 或 ManyToMany(多對多), 避免載入大量資料.

## 執行環境

* Python 3.11

## Reference

* [Django](https://www.djangoproject.com/)

* [Django and the N+1 Queries Problem](https://scoutapm.com/blog/django-and-the-n1-queries-problem)

## Donation

文章都是我自己研究內化後原創，如果有幫助到您，也想鼓勵我的話，歡迎請我喝一杯咖啡:laughing:

![alt tag](https://i.imgur.com/LRct9xa.png)

[贊助者付款](https://payment.opay.tw/Broadcaster/Donate/9E47FDEF85ABE383A0F5FC6A218606F8)

## License

MIT license