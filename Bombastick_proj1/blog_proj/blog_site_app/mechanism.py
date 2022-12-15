import random
import string
from datetime import datetime, timedelta

from django.core.mail import send_mail, send_mass_mail
from django.shortcuts import redirect, render

import blog_proj
from blog_proj.settings import STATIC_ROOT
from .models import *
from .validators import *


def login_operation(req):
    email = req.POST.get('email')
    ip = req.META['REMOTE_ADDR']

    # If user not sign up in blog, we create an account
    if UsersAc.objects.filter(email=email).exists() == False:
        cleanup_db_start()
        new_us = UsersAc.objects.create(email=email, password=req.POST.get('password'), last_login=datetime.datetime.utcnow())
        res = valid_user(new_us)
        if res == None:
            time = datetime.datetime.utcnow() + timedelta(days=1) # token lifetime id 1 day
            token = create_token(new_us, time, ip) # Here we check ip and token, it was made for account's security
            response = redirect('/')
            response.set_cookie('Auth_key_blog', token, expires=time)
            return response
        elif res.get('email', None) != None:
            new_us.delete()
            return redirect('/error/3/')
        elif res.get('password', None) != None:
            new_us.delete()
            return redirect('/error/4/')

    else:
        # Login
        cleanup_db_start()
        user = UsersAc.objects.get(email=email)
        out_pass = req.POST.get('password')
        if out_pass == user.password:
            time = datetime.datetime.utcnow() + timedelta(days=1)
            token = create_token(user, time, ip)
            response = redirect('/')
            response.set_cookie('Auth_key_blog', token, expires=time)
            user.pre_last_login = user.last_login
            user.last_login = datetime.datetime.utcnow()
            user.save()
            return response
        else:
            return redirect('/error/5/')


def create_token(user, time, ip):
    letters = string.ascii_letters
    rand_string = ''.join(random.choice(letters) for i in range(69))
    new_token = SessUsers.objects.create(id_user=user.id, token=rand_string, data_to_erase=time, ip=ip)
    return rand_string

def exists_token(req):
    token = req.COOKIES.get('Auth_key_blog', None)
    return SessUsers.objects.filter(token=token).exists()

# I use the method not always, but it check valid token
def in_sys(req):
    ip = req.META['REMOTE_ADDR']
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        user_line = SessUsers.objects.filter(token=token).exists()
        if user_line == True:
            user_line = SessUsers.objects.get(token=token)
            if user_line.ip != ip:
                user_line.delete()
                red = redirect('/reg/')
                red.delete_cookie('Auth_key_blog')
                return red

        else:
            red = redirect('/reg/')
            red.delete_cookie('Auth_key_blog')
            return red

# Menu for login users and guests
def menu_login(req):
    if req.COOKIES.get('Auth_key_blog', None) != None:
        if exists_token(req):
            return 'menu_login.html'
        else:
            return 'menu.html'

    else:
        return 'menu.html'


def list_subs(id_owner):
    res = Subs.objects.filter(subscription=id_owner).values()
    subscribers = list()
    for d in res:
        subscribers.append(d['subscriber'])
    return subscribers


def is_posts(id):
    exists = Post.objects.filter(author=id).exists()
    if exists:
        return Post.objects.filter(author=id).values('id', 'title', 'pic_1', 'desc')
    else:
        return False


def page_user_with_auth(req, id):
    token = req.COOKIES['Auth_key_blog']
    user_line = SessUsers.objects.get(token=token)
    user = UsersAc.objects.get(id=user_line.id_user)
    data = {}
    if is_ban(id):
        data['is_ban'] = True
        data['template_name'] = menu_login(req)
        return render(req, 'acc_user_pub.html', context=data)

    elif user.id == id: # If this page the user's
        data['full_name'] = user.full_name
        data['desc'] = user.desc
        data['number_of_sub'] = len(list_subs(user.id))
        data['template_name'] = 'menu_login.html'
        posts = is_posts(user.id)
        if posts:
            data['posts_count'] = 22
            data['coll'] = posts

        else:
            data['posts_count'] = 0


        data['img'] = user.main_pic
        return render(req, 'acc_user_pub_own.html', context=data)

    else:
        user = UsersAc.objects.get(id=id)
        res = do_freeze_user(id)
        if not res:
            data['is_freeze'] = True
        elif res == 'del':
            return redirect('/error/2/')
        else:
            data['desc'] = user.desc

        data['img'] = user.main_pic
        data['full_name'] = user.full_name
        data['number_of_sub'] = len(list_subs(user.id))
        data['template_name'] = 'menu_login.html'
        posts = is_posts(id)
        if posts == False:
            data['posts_count'] = 0

        else:
            data['coll'] = posts
            data['posts_count'] = 22

        is_sub = Subs.objects.filter(subscriber=user_line.id_user, subscription=id).exists()
        data['sub'] = is_sub

        if is_sub:
            data['path'] = f'/user/{id}/unsub'
        else:
            data['path'] = f'/user/{id}/sub'

        return render(req, 'acc_user_pub.html', context=data)

def page_user_without_auth(req, id):
    data = {}
    if is_ban(id):
        data['is_ban'] = True
        data['template_name'] = menu_login(req)
        return render(req, 'acc_user_pub.html', context=data)

    user = UsersAc.objects.get(id=id)
    res = do_freeze_user(id)
    if not res:
        data['is_freeze'] = True
    elif res == 'del':
        return redirect('/error/2/')
    else:
        data['desc'] = user.desc

    data['full_name'] = user.full_name
    data['number_of_sub'] = len(list_subs(user.id))
    data['template_name'] = 'menu.html'
    posts = is_posts(id)
    if posts == False:
        data['posts_count'] = 0

    else:
        data['posts_count'] = 2
        data['coll'] = posts[:2]
        cens = WindowCens.objects.get(id=2)
        data['not_auth'] = True
        data['w_title'] = cens.title
        data['w_desc'] = cens.desc
        data['w_url'] = cens.url

    data['sub'] = False
    data['path'] = '/reg/'
    data['img'] = user.main_pic
    return render(req, 'acc_user_pub.html', context=data)

# Saving users pictures
def pic_saver(file):
    img_path = f'{BASE_DIR}/blog_site_app/static/assets/images/'
    new_name = ''.join(random.choice(string.ascii_letters) for i in range(25)) # I make new name for files, for uniqueness
    suff = str(file)
    ind = suff.rfind('.')
    suff = suff[ind:]
    b_file = bytes(file.read())
    if len(b_file) < 1048576:
        destination = open(f'{img_path}{new_name}{suff}', 'wb')
        destination.write(b_file)
        return f'/static/assets/images/{new_name}{suff}'
    else:
        return redirect('/error/7/')

# If user had a default name, in comments will use an email
def nick_name(id):
    if UsersAc.objects.filter(id=id).exists():
        user = UsersAc.objects.get(id=id)
        if user.full_name != 'Кто-то и как-то':
            author = user.full_name
        else:
            author = user.email
    else:
        author = 'Пользователь удален'
    return author


def strip_time_for_tz(post_data: datetime.datetime, tz: str):
    print(tz[0])
    num = int(tz[1:])
    if tz[0] == '-':
        post_data -= timedelta(hours=num)
    else:
        post_data += timedelta(hours=num)
    return post_data

def send_notf_new_post(author_id, post_id):
    subs = Subs.objects.filter(subscription=author_id).values('subscriber')
    for sub in subs:
        new_notf = Notification.objects.create(id_user=int(sub['subscriber']), status='new_post', url=f'/posts/{post_id}/')

def send_notf_new_comment(post_id, author_id):
    new_notf = Notification.objects.create(id_user=author_id, status='new_comm', url=f'/posts/{post_id}/')

def send_notf_new_like(post_id, author_id):
    new_notf = Notification.objects.create(id_user=author_id, status='new_like', url=f'/posts/{post_id}/')

def send_notf_new_sub(user_id, author_id):
    new_notf = Notification.objects.create(id_user=author_id, status='new_sub', url=f'/user/{user_id}/')

def send_notf_new_rep(user_id, post_page_id):
    new_notf = Notification.objects.create(id_user=user_id, status='new_report', url=f'/posts/{post_page_id}/')

def send_notf_new_rep_from_admin(user_id, text):
    new_notf = Notification.objects.create(id_user=user_id, status='new_report_ad', url=f'/rules/', text=text)

def search_proc(tags_str, req):
    data = {}
    data['template_name'] = menu_login(req)
    if tags_str:
        tags_str = tags_str.replace(',', '').replace('.', '').replace(';', '')
        tags_list = tags_str.split()
        posts_cards = []
        for tag in tags_list:
            res_title = Post.objects.filter(title__icontains=tag).values('id', 'title', 'desc', 'pic_1')
            res_text = Post.objects.filter(text__icontains=tag).values('id', 'title', 'desc', 'pic_1')
            for el in res_title:
                posts_cards.append(el)
            for el in res_text:
                posts_cards.append(el)

        if data['template_name'] == 'menu.html':
            posts_cards = posts_cards[:5]
            cens = WindowCens.objects.get(id=2)
            data['w_title'] = cens.title
            data['w_desc'] = cens.desc
            data['w_url'] = cens.url

        if posts_cards:
            data['list_posts'] = posts_cards

    return render(req, 'searchpage.html', context=data)

def do_freeze_user(id):
    user = UsersAc.objects.get(id=id)
    if datetime.datetime.now(user.last_login.tzinfo) - datetime.timedelta(weeks=20) > user.last_login and user.is_freeze:
        return None
    elif datetime.datetime.now(user.last_login.tzinfo) - datetime.timedelta(weeks=20) > user.last_login:
        user.gender = None
        user.desc = None
        if user.main_pic != '/static/assets/images/1605206596114447571-816x577.png':
            os.remove(os.path.join(BASE_DIR, 'blog_site_app') + user.main_pic)
        user.main_pic = '/static/assets/images/1605206596114447571-816x577.png'
        user.is_freeze = True
        user.save()
    elif datetime.datetime.now(user.last_login.tzinfo) - datetime.timedelta(days=365) > user.last_login:
        erase_user(user)
        return 'del'
    else:
        return True

def is_ban(id):
    is_b = BanList.objects.filter(id_user=id).exists()
    return is_b

def erase_user(user):
    subs = Subs.objects.filter(subscriber=user.id).values()
    for sub in subs:
        s = Subs.objects.get(id=sub['id'])
        s.delete()

    subscription = Subs.objects.filter(subscription=user.id).values()
    for sub in subs:
        s = Subs.objects.get(id=sub['id'])
        s.delete()

    likes = Likes.objects.filter(user=user.id)
    for l in likes:
        l.delete()

    dislikes = DisLikes.objects.filter(user=user.id)
    for l in dislikes:
        l.delete()

    reps = ReportsListAll.objects.filter(id_user=user.id)
    for r in reps:
        r.delete()

    if user.main_pic != '/static/assets/images/1605206596114447571-816x577.png' and user.main_pic != '/static/assets/images/1605206596114447571-1016x719.png':
        os.remove(os.path.join(BASE_DIR, 'blog_site_app') + user.main_pic)

# Erasing user's data if he was ban
def erase_dirty_user(user):
    erase_user(user)
    posts = Post.objects.filter(author=user.id)
    for post in posts:
        post.delete()

    comms = Comments.objects.filter(author_com=user.id)
    for com in comms:
        com.delete()

def erase_fakes():
    users_list = list(UsersAc.objects.filter(pre_last_login=None).values('id'))
    users_list += list(UsersAc.objects.filter(true_email=False).values('id'))
    for us in users_list:
        user = UsersAc.objects.get(id=us['id'])
        points = 0  # Than more points the more activity
        time_res = user.last_login > datetime.datetime.now(tz=user.last_login.tzinfo) - datetime.timedelta(weeks=6)
        if user.main_pic != '/static/assets/images/1605206596114447571-816x577.png':
            points += 1
        if len(Likes.objects.filter(user=user.id).values('id')) + len(DisLikes.objects.filter(user=user.id).values('id')) > 2:
            points += 1
        if user.true_email:
            points += 2
        if user.desc != 'Пока, нечего рассказать':
            points += 1
        if user.full_name != 'Кто-то и как-то':
            points += 1
        if not (points >= 2 and time_res) or not points >= 4:
            erase_user(user)



def cleanup_db():
    # Clean sessions
    sess = SessUsers.objects.values('id', 'data_to_erase')
    user = UsersAc.objects.get(id=1)
    tz = user.last_login.tzinfo
    now = datetime.datetime.now(tz=tz)
    for ses in sess:
        ses_obj = SessUsers.objects.get(id=ses['id'])
        if now > ses_obj.data_to_erase:
            ses_obj.delete()

    # Not used url for changing password
    urls = PasswUrl.objects.values('id', 'data_to_erase')
    for url in urls:
        url_obj = PasswUrl.objects.get(id=url['id'])
        if now > url_obj.data_to_erase:
            url_obj.delete()

    # Old notifications
    notfs = Notification.objects.filter(until_date__lte=now).values('id')
    for n in notfs:
        n_obj = Notification.objects.get(id=n['id'])
        n_obj.delete()

    # Check dead or unused accounts
    erase_fakes()


# Twice per day database is tidied up. But, I start it in login_operation()
def cleanup_db_start():
    data = datetime.datetime.utcnow().date()
    if blog_proj.settings.cleanup_count_today >= 2:
        # If already new day
        if Cleanup.objects.filter(data=data).exists() == False:
            blog_proj.settings.cleanup_count_today = 0
            Cleanup.objects.create(data=data, count_done=0)
            cleanup_db_start()

    else: # cleanup < 2
        if Cleanup.objects.filter(data=data).exists() == False: # If hasn't notes about today
            blog_proj.settings.cleanup_count_today = 0
            note = Cleanup.objects.create(data=data, count_done=0)
            cleanup_db()
            blog_proj.settings.cleanup_count_today += 1
            note.count_done += 1
            note.save()
        else: # If had note today
            note = Cleanup.objects.get(data=data)
            count = note.count_done
            blog_proj.settings.cleanup_count_today = count
            if count < 2:
                cleanup_db()
                blog_proj.settings.cleanup_count_today += 1
                note.count_done += 1
                note.save()
