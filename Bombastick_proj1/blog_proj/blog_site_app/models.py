import datetime
import os

from django.db import models

from blog_proj.settings import BASE_DIR


class UsersAc(models.Model):
    email = models.CharField(max_length=30, null=False, unique=True)
    password = models.CharField(max_length=30, null=False)
    full_name = models.CharField(max_length=40, default='Кто-то и как-то')
    gender = models.CharField(max_length=11, default='Жаба', null=True)
    desc = models.CharField(max_length=900, default='Пока, нечего рассказать', null=True)
    main_pic = models.CharField(max_length=200, default='/static/assets/images/1605206596114447571-816x577.png')
    true_email = models.BooleanField(default=False)
    status_admin = models.BooleanField(default=False)
    is_freeze = models.BooleanField(default=False)
    count_email = models.IntegerField(default=0, null=True)
    time_zone = models.CharField(max_length=4, null=False, default=0)
    last_login = models.DateTimeField(null=True)
    pre_last_login = models.DateTimeField(null=True)





class SessUsers(models.Model):
    id_user = models.IntegerField(null=False)
    token = models.CharField(unique=True, max_length=100)
    data_to_erase = models.DateTimeField()
    ip = models.CharField(max_length=20, null=False)



class Subs(models.Model):
    subscriber = models.IntegerField(null=False)
    subscription = models.IntegerField(null=False)

class Post(models.Model):
    author = models.IntegerField(null=False)
    title = models.CharField(max_length=65, null=False)
    desc = models.CharField(max_length=225, null=False)
    text = models.CharField(max_length=6300, null=False)
    is_adult = models.BooleanField(null=False, default=True)
    tags = models.CharField(max_length=100, null=False, default='')
    pic_1 = models.CharField(max_length=100, null=True)
    pic_2 = models.CharField(max_length=100, null=True)
    pic_3 = models.CharField(max_length=100, null=True)
    data_of_create = models.DateTimeField(null=False, default=datetime.datetime.utcnow())
    good_num = models.IntegerField(default=0)
    bad_num = models.IntegerField(default=0)


class Comments(models.Model):
    author_com = models.IntegerField(null=False)
    text = models.CharField(max_length=225, null=False)
    post_id = models.IntegerField(null=False)

class Likes(models.Model):
    user = models.IntegerField(null=False)
    is_like = models.BooleanField(null=False)
    post_id = models.IntegerField(null=False)

class DisLikes(models.Model):
    user = models.IntegerField(null=False)
    is_dislike = models.BooleanField(null=False)
    post_id = models.IntegerField(null=False)


class ErrorPage(models.Model):
    error_title = models.CharField(max_length=65, null=False)
    error_desc = models.CharField(max_length=300, null=False)
    url_red = models.CharField(max_length=200, null=False)


class PasswUrl(models.Model):
    id_user = models.IntegerField(null=False)
    url = models.CharField(null=False, max_length=70)
    new_password = models.CharField(max_length=30, null=False)
    data_to_erase = models.DateTimeField(default=datetime.datetime.utcnow()+datetime.timedelta(days=1))

class WindowCens(models.Model):
    title = models.CharField(max_length=50)
    desc = models.CharField(max_length=150)
    url = models.CharField(max_length=150)

class Reports(models.Model):
    path_page = models.CharField(max_length=65)
    id_user = models.IntegerField(null=False)
    comment = models.IntegerField(default=None, null=True)
    text = models.CharField(max_length=50, null=True)


class Notification(models.Model):
    id_user = models.IntegerField(null=False)
    status = models.CharField(max_length=40, null=False)  # new_post email_notf new_comm new_like new_sub new_report new_report_ad
    url = models.CharField(max_length=50, null=False)
    until_date = models.DateTimeField(default=datetime.datetime.utcnow()+datetime.timedelta(days=3))
    text = models.CharField(max_length=200, null=True)

class ReportsListAll(models.Model):
    id_user = models.IntegerField(null=False)
    data_of_rep = models.DateTimeField(null=False, default=str(datetime.datetime.utcnow()))

class BanList(models.Model):
    id_user = models.IntegerField(null=False)

class Cleanup(models.Model):
    data = models.DateField(null=False, unique=True)
    count_done = models.IntegerField(default=0)

