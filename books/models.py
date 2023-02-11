from django.db import models

# Create your models here.

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

    class Meta:
        db_table = 'book'

    def __str__(self):
        return self.name