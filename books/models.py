from django.db import models

# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=20)
    created_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tag'

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        db_table = 'country'

    def __str__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=20)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        db_table = 'author'

    def __str__(self):
        return self.name

class Book(models.Model):
    name = models.CharField(max_length=20)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    class Meta:
        db_table = 'book'

    def __str__(self):
        return self.name