from django.db import connection
from django.shortcuts import render
from django.conf.urls.static import static
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from .mechanism import *


def index(req):
    data = {'template_name': menu_login(req)}
    return render(req, 'index.html', context=data)


@api_view(['GET', 'POST'])
def registration(req, pk=None):
    in_sys(req)

    # If we already log in, then redirect to our acc
    if req.COOKIES.get('Auth_key_blog', None) and exists_token(req):
        return redirect('/account/')

    elif req.method == 'GET':
        data = {'template_name': menu_login(req)}
        return render(req, 'login.html', context=data)

    else:
        # if method = POST, there a registration or log in operation
        return login_operation(req)


def rules(req):
    data = {'template_name': menu_login(req)}
    return render(req, 'rules.html', context=data)


@api_view(['GET', 'POST'])
def owner_acc(req):
    in_sys(req)

    # If dont log
    if exists_token(req) == False or req.COOKIES.get('Auth_key_blog', None) == None:
        red = redirect('/reg/')
        red.delete_cookie('Auth_key_blog')
        return red

    # render our account settings and datas
    elif req.method == 'GET':
        user_line = SessUsers.objects.get(token=req.COOKIES['Auth_key_blog'])
        user = UsersAc.objects.get(id=user_line.id_user)
        data = {}
        data['email'] = user.email
        data['full_name'] = user.full_name
        data['gender'] = user.gender
        data['desc'] = user.desc
        data['template_name'] = menu_login(req)
        data['true_email'] = user.true_email
        data['url'] = f'/user/{user.id}'
        return render(req, 'owner.html', context=data)

    # Changing our datas
    elif req.method == 'POST':
        token = req.COOKIES['Auth_key_blog']
        user_line = SessUsers.objects.get(token=token)
        full_name = req.POST.get('full_name', None)
        gender = req.POST.get('gender', None)
        desc = req.POST.get('desc', None)
        email = req.POST.get('email', None)
        user = UsersAc.objects.get(id=user_line.id_user)
        ava = req.FILES.get('ava', None)

        # Change user's avatar/main picture
        if ava:
            old_pic = user.main_pic
            user.main_pic = pic_saver(ava)
            res = valid_user(user)
            if res and res.get('pic', None):
                os.remove(os.path.join(BASE_DIR, 'blog_site_app') + user.main_pic)
                user.main_pic = old_pic
                redirect('/error/6/')
            try:
                os.remove(os.path.join(BASE_DIR, 'blog_site_app') + old_pic)
            except:
                pass

        if full_name:
            user.full_name = full_name
        if gender:
            user.gender = gender
        if desc:
            user.desc = desc
        if email:
            user.email = email
            user.true_email = False

        user.save()
        return redirect('/account/')


# Then we opening /user/.../
def page_user(req, id):
    in_sys(req)
    if UsersAc.objects.filter(id=id).exists():
        if req.COOKIES.get('Auth_key_blog', None) != None:
            if exists_token(req):
                return page_user_with_auth(req, id)
            else:
                # Without log in we can't subscribe and see all user's posts
                return page_user_without_auth(req, id)
        else:
            return page_user_without_auth(req, id)
    else:
        # If user doesn't exists
        return redirect('/error/2/')


@api_view(['GET'])
def delete_page(req):
    in_sys(req)
    data = {'template_name': menu_login(req)}
    return render(req, 'delete.html', context=data)


# If user want to delete his account
def delete_acc(req):
    in_sys(req)
    token = req.COOKIES['Auth_key_blog']
    user_line = SessUsers.objects.get(token=token)
    user = UsersAc.objects.get(id=user_line.id_user)
    # Erase user's datas
    erase_user(user)
    user.delete()
    user_line.delete()
    red = redirect('/reg/')
    red.delete_cookie('Auth_key_blog')
    return red


# pattern page for differents errors. All errors taken from DB
def error_page(req, id=None):
    data = {'template_name': menu_login(req)}
    if id != None:
        if ErrorPage.objects.filter(id=id).exists():
            er = ErrorPage.objects.get(id=id)
            data['error_title'] = er.error_title
            data['error_desc'] = er.error_desc
            data['url_red'] = er.url_red
            return render(req, 'error.html', context=data)

    return redirect('/')


def logout(req):
    in_sys(req)
    token = req.COOKIES['Auth_key_blog']
    user_line = SessUsers.objects.get(token=token)
    user_line.delete()
    red = redirect('/')
    red.delete_cookie('Auth_key_blog')
    return red


def unsub(req, id):
    in_sys(req)
    token = req.COOKIES['Auth_key_blog']
    user_line = SessUsers.objects.get(token=token)
    if user_line.id_user != id and Subs.objects.filter(subscriber=user_line.id_user, subscription=id).exists():
        sub_line = Subs.objects.get(subscriber=user_line.id_user, subscription=id)
        sub_line.delete()
    return redirect(f'/user/{id}/')


def plus_sub(req, id):
    in_sys(req)
    token = req.COOKIES['Auth_key_blog']
    user_line = SessUsers.objects.get(token=token)
    if user_line.id_user != id and Subs.objects.filter(subscriber=user_line.id_user, subscription=id).exists() != True:
        Subs.objects.create(subscriber=user_line.id_user, subscription=id)
        send_notf_new_sub(user_line.id_user, id)
    return redirect(f'/user/{id}/')


def apply_email(req):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            user.true_email = True
            user.save()
            return redirect('/account/')
        else:
            return redirect('/error/1/')
    else:
        return redirect('/error/1/')


# Checking and changing password
def is_change_pass(req, url):
    if PasswUrl.objects.filter(url=url).exists():
        line = PasswUrl.objects.get(url=url)
        user = UsersAc.objects.get(id=line.id_user)
        user.password = line.new_password
        user.save()
        line.delete()
        return redirect('/reg/')
    else:
        return redirect('/error/2/')


def change_pass(req):
    if req.method == 'GET':
        data = {'template_name': menu_login(req)}
        return render(req, 'change_pass.html', context=data)

    # Create new password and sending email message
    elif req.method == 'POST':
        email = req.POST.get('email', None)
        password = req.POST.get('password', None)
        letters = string.ascii_letters
        dig = string.digits
        rand_string = ''.join(random.choice(letters) for i in range(30)) + ''.join(
            random.choice(dig) for i in range(30))
        url = f'{rand_string}'
        user = UsersAc.objects.filter(email=email).exists()
        if user:
            user = UsersAc.objects.get(email=email)
            PasswUrl.objects.create(id_user=user.id, url=url, new_password=password)
            msg = render_to_string('password_email_page.html', context={'url': f'https://bombast.ru/{url}/'})
            send_mail(
                subject='Бомбастик: Подтвердите смену пароля',
                from_email="bombast@internet.ru",
                message='',
                html_message=msg,
                recipient_list=[email],
                fail_silently=True,
            )
        return redirect('/reg/')


def create_post(req):
    if req.method == 'POST':
        token = req.COOKIES.get('Auth_key_blog', None)
        if token != None:
            if exists_token(req):
                line = SessUsers.objects.get(token=token)
                user = UsersAc.objects.get(id=line.id_user)
                if user.true_email or Post.objects.filter(author=user.id).exists() != True:
                    author = user.id
                    title = req.POST.get('title')
                    post_text = req.POST.get('post_text')
                    is_adult = req.POST.get('is_adult', None)
                    if not is_adult:
                        return redirect()
                    tags = req.POST.get('tags')
                    pic_1 = req.FILES.get('pic_1', None)
                    pic_2 = req.FILES.get('pic_2', None)
                    pic_3 = req.FILES.get('pic_3', None)
                    agree = req.POST.get('agree')
                    desc = post_text[:220]
                    desc = f'{desc}...'
                    post = Post.objects.create(author=author, title=title, desc=desc, text=post_text, is_adult=is_adult,
                                               tags=tags, pic_1=None, pic_2=None, pic_3=None, data_of_create=datetime.datetime.utcnow())
                    # Saving pictures which user loaded
                    if agree:
                        if pic_1:
                            res = pic_saver(pic_1)
                            if type(res) != type(''):
                                return res
                            else:
                                post.pic_1 = res
                                print(post.pic_1)

                        if pic_2:
                            res = pic_saver(pic_2)
                            if type(res) != type(''):
                                return res
                            else:
                                post.pic_2 = res

                        if pic_3:
                            res = pic_saver(pic_3)
                            if type(res) != type(''):
                                return res
                            else:
                                post.pic_3 = res

                    post.save()
                    # Send user's subs about new post
                    send_notf_new_post(user.id, post.id)
                    return redirect('/posts/')
                else:
                    return redirect('/error/8/')
            else:
                return redirect('/reg/')

        else:
            return redirect('/reg/')

    # render form for create article
    if req.method == 'GET':
        token = req.COOKIES.get('Auth_key_blog', None)
        if token != None:
            if exists_token(req):
                data = {'template_name': menu_login(req)}
                return render(req, 'create_post.html', context=data)
            else:
                return redirect('/reg/')
        else:
            return redirect('/reg/')


def page_post(req, id):
    token = req.COOKIES.get('Auth_key_blog', None)

    if Post.objects.filter(id=id).exists():
        if req.method == 'GET':
            post = Post.objects.get(id=id)
            new_time = post.data_of_create
            if token != None:
                if exists_token(req):
                    line = SessUsers.objects.get(token=token)
                    user_vis = UsersAc.objects.get(id=line.id_user)
                    time = user_vis.time_zone
                    new_time = strip_time_for_tz(post.data_of_create, time)

            if UsersAc.objects.filter(id=post.author).exists():
                author = UsersAc.objects.get(id=post.author)
                if author.full_name != 'Кто-то и как-то':
                    author = author.full_name
                else:
                    author = author.email
            else:  # If user was deleted we use 'User was deleted' without nickname, if user wasn't ban
                author = 'Пользователь удален'


            data = {'template_name': menu_login(req), 'is_adult': post.is_adult, 'title': post.title, 'text': post.text,
                    'pic_1': post.pic_1, 'pic_2': post.pic_2, 'pic_3': post.pic_3,
                    'data_of_create': new_time,
                    'author': author, 'id_user': post.author, 'tags': post.tags, 'good_num': post.good_num,
                    'bad_num': post.bad_num, 'good_src': f'/posts/{id}/like', 'bad_src': f'/posts/{id}/dis'}

            author = UsersAc.objects.get(id=post.author)
            if token != None:
                if exists_token(req):
                    data[
                        'login'] = True  # If user log in, he can send comment, if not, on the page will show block with message
                    if author.id == user_vis.id:
                        data[
                            'is_author'] = True  # If user is author he can delete or update his post, if he is not he can report a violation
                    else:
                        data['is_author'] = False
                else:
                    data['login'] = False
            else:
                data['login'] = False

            win = WindowCens.objects.get(
                id=1)  # Message about need to log in, how and error's pages, all text taken from DB
            data['w_title'] = win.title
            data['w_desc'] = win.desc
            data['w_url'] = win.url
            res_com = Comments.objects.filter(post_id=id).exists()
            if res_com:
                comments = list(Comments.objects.filter(post_id=id).values())
                for el in comments:
                    el['id_user'] = el['author_com']
                    el['author_com'] = nick_name(el['id_user'])
                data['comments'] = comments
            else:
                data['comments'] = None

            return render(req, 'full_post.html', context=data)

        # Saving comment
        elif req.method == 'POST':
            if token != None:
                if exists_token(req):
                    comment = req.POST.get('comment', None)
                    if comment:
                        line = SessUsers.objects.get(token=token)
                        user = UsersAc.objects.get(id=line.id_user)
                        count_comm = len(Comments.objects.filter(author_com=user.id).values())
                        if user.true_email or count_comm < 3:
                            new_com = Comments.objects.create(author_com=line.id_user, text=comment, post_id=id)
                            new_com.save()
                            post = Post.objects.get(id=id)
                            author = post.author
                            send_notf_new_comment(id, author)
                        else:
                            return redirect(
                                '/error/8/')  # if user doesn't agree his email he cannot send more than 3 comments (and can't text more than 1 post)

                    return redirect(f'/posts/{id}/')
                return redirect('/error/2/')
            return redirect('/error/2/')
    else:
        return redirect('/error/2/')


def delete_post(req, id):
    if req.method == 'GET':
        token = req.COOKIES.get('Auth_key_blog', None)
        if token != None:
            if exists_token(req):
                post = Post.objects.get(id=id)
                author = UsersAc.objects.get(id=post.author)
                line = SessUsers.objects.get(token=token)
                user_vis = UsersAc.objects.get(id=line.id_user)
                if author.id == user_vis.id:  # Only author can delete post
                    return render(req, 'del_post.html', context={'template_name': menu_login(req)})

        return redirect(f'/posts/{id}/')

    elif req.method == 'POST':
        token = req.COOKIES.get('Auth_key_blog', None)
        if token != None:
            if exists_token(req):
                post = Post.objects.get(id=id)
                author = UsersAc.objects.get(id=post.author)
                line = SessUsers.objects.get(token=token)
                user_vis = UsersAc.objects.get(id=line.id_user)
                if author.id == user_vis.id:
                    post = Post.objects.get(id=id)
                    post.delete()
                    coms = Comments.objects.filter(post_id=id).values('id')  # Also deleting post's comments
                    for val in coms:
                        comm = Comments.objects.get(id=val['id'])
                        comm.delete()

                    likes = Likes.objects.filter(post_id=id).values(
                        'id')  # Also deleting post's likes and bottom - dislikes
                    for val in likes:
                        l = Likes.objects.get(id=val['id'])
                        l.delete()

                    dlikes = DisLikes.objects.filter(post_id=id).values('id')
                    for val in dlikes:
                        dl = DisLikes.objects.get(id=val['id'])
                        dl.delete()
                    return redirect('/posts/')

        return redirect(f'/posts/{id}/')


def update_post(req, id):
    token = req.COOKIES.get('Auth_key_blog', None)
    data = {}
    if token != None:
        if exists_token(req):
            post = Post.objects.get(id=id)
            author = UsersAc.objects.get(id=post.author)
            line = SessUsers.objects.get(token=token)
            user_vis = UsersAc.objects.get(id=line.id_user)
            post = Post.objects.get(id=id)
            if author.id == user_vis.id:
                if req.method == 'GET':
                    data['title'] = post.title
                    data['text'] = post.text
                    data['tags'] = post.tags
                    data['template_name'] = menu_login(req)
                    return render(req, 'update_post.html', context=data)
                elif req.method == 'POST':
                    post.title = req.POST.get('title')
                    text = req.POST.get('post_text')
                    post.text = text
                    post.is_adult = req.POST.get('is_adult')
                    post.tags = req.POST.get('tags')
                    desc = text[:220]
                    post.desc = f'{desc}...'
                    post.save()
                    return redirect(f'/posts/{id}/')
    redirect(f'/posts/{id}/')


def report_post(req, id, comm=None):  # Report to the admin - '/admin/'
    token = req.COOKIES.get('Auth_key_blog', None)
    data = {}
    if token != None:
        if exists_token(req):
            user_line = SessUsers.objects.get(token=token)
            path = f'/posts/{id}/'
            if comm:
                if Reports.objects.filter(path_page=path, id_user=user_line.id_user, comment=comm).exists():
                    return redirect(f'/posts/{id}/')

                comment = Comments.objects.get(id=comm)
                report = Reports.objects.create(path_page=path, id_user=user_line.id_user, comment=comm,
                                                text=comment.text[:49])
                data['url'] = f'/posts/{id}/'
                data['template_name'] = menu_login(req)

            else:
                if Reports.objects.filter(path_page=path, id_user=user_line.id_user).exists():
                    return redirect(f'/posts/{id}/')

                report = Reports.objects.create(path_page=path, id_user=user_line.id_user)
                data['url'] = f'/posts/{id}/'
                data['template_name'] = menu_login(req)

            return render(req, 'report_post_page.html', context=data)

    return redirect(f'/reg/')


# The author of post can delete post's comments
def delete_comment(req, id, comm):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            post = Post.objects.get(id=id)
            author = UsersAc.objects.get(id=post.author)
            line = SessUsers.objects.get(token=token)
            user_vis = UsersAc.objects.get(id=line.id_user)
            if author.id == user_vis.id:
                com = Comments.objects.get(id=comm)
                com.delete()
            return redirect(f'/posts/{id}/')

    return redirect(f'/reg/')


def main_page_with_posts(req):
    data = {}
    posts_list = list(Post.objects.order_by('-data_of_create').values('id', 'title', 'pic_1', 'desc'))
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            data['login'] = True
        else: # If user don't login he will see a block with message about need log
            cens = WindowCens.objects.get(id=2)
            data['login'] = False
            data['w_title'] = cens.title
            data['w_desc'] = cens.desc
            data['w_url'] = cens.url
    else:
        data['login'] = False
        cens = WindowCens.objects.get(id=2)
        data['w_title'] = cens.title
        data['w_desc'] = cens.desc
        data['w_url'] = cens.url

    if len(posts_list) > 15: # If on the page a lot of posts we can see button with redirect to the next page
        data['len_list'] = len(posts_list)
        if data['login'] == True:
            posts_list = posts_list[:16]
        else:
            posts_list = posts_list[:4]

        data['previous'] = None
        data['next'] = True
        data['link_next'] = '/posts/next_1/'
        data['posts_list'] = posts_list
    else: # There don't be a button
        if data['login'] != True:
            posts_list = posts_list[:4]

        data['len_list'] = len(posts_list)
        data['previous'] = None
        data['next'] = None
        data['posts_list'] = posts_list

    data['template_name'] = menu_login(req)
    for post in posts_list:
        if post['pic_1'] == None:
            post['pic_1'] = '/static/assets/images/16-4-800x530.jpeg'
    return render(req, 'main_posts.html', context=data)

# Then we on the next page, logic is change
def next_page_with_posts(req, id):
    data = {}
    posts_list = list(Post.objects.values('id', 'title', 'pic_1', 'desc'))
    posts_list = posts_list[15 * id:] # For the load not all posts

    if len(posts_list) > 15: # Button again, and button with return back on the main
        data['len_list'] = len(posts_list)
        posts_list = posts_list[:16]
        data['previous'] = True
        data['next'] = True
        data['link_next'] = f'/posts/next_{id + 1}/'
    elif len(posts_list) < 15 and id: # Only return back button
        data['len_list'] = len(posts_list)
        data['previous'] = True
        data['next'] = None

    if id > 1:
        data['link_prev'] = f'/posts/next_{id - 1}/'
    else: # If we on the second page, we need return to the main - '/posts/'
        data['link_prev'] = '/posts/'

    data['posts_list'] = posts_list
    data['template_name'] = menu_login(req)
    data['login'] = data['template_name'] == 'menu_login.html'
    print(data['login'])

    for post in posts_list:
        if post['pic_1'] == None: # If post doesn't have a pics, we see a default
            post['pic_1'] = '/static/assets/images/16-4-800x530.jpeg'

    return render(req, 'main_posts.html', context=data)

# Put like, if before we put dislike, it will delete and will be like
def like(req, id):
    token = req.COOKIES.get('Auth_key_blog', None)
    post = Post.objects.get(id=id)
    if token != None:
        if exists_token(req):
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            val = Likes.objects.filter(post_id=id, user=user.id)
            if val.exists():
                val = Likes.objects.get(post_id=id, user=user.id)
                val.delete()
                post.good_num -= 1 # good and bad numbers displayed on the post, we can see a count of opinions
            else:
                post.good_num += 1
                new = Likes.objects.create(post_id=id, user=user.id, is_like=True)
                if DisLikes.objects.filter(post_id=id, user=user.id).exists():
                    val = DisLikes.objects.get(post_id=id, user=user.id)
                    val.delete()
                    post.bad_num -= 1
                new.save()

            post.save()
            send_notf_new_like(id, post.author)
            return redirect(f'/posts/{id}/')

        else:
            return redirect('/reg/')
    else:
        return redirect('/reg/')

# Similar to likes
def dislike(req, id):
    token = req.COOKIES.get('Auth_key_blog', None)
    post = Post.objects.get(id=id)
    if token != None:
        if exists_token(req):
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            val = DisLikes.objects.filter(post_id=id, user=user.id)
            if val.exists():
                val = DisLikes.objects.get(post_id=id, user=user.id)
                val.delete()
                post.bad_num -= 1
            else:
                post.bad_num += 1
                new = DisLikes.objects.create(post_id=id, user=user.id, is_dislike=True)
                if Likes.objects.filter(post_id=id, user=user.id).exists():
                    val = Likes.objects.get(post_id=id, user=user.id)
                    val.delete()
                    post.good_num -= 1
                new.save()

            send_notf_new_like(id, post.author)
            post.save()
            return redirect(f'/posts/{id}/')

        else:
            return redirect('/reg/')
    else:
        return redirect('/reg/')

# List with ourself's subscriptions
def my_subs_list(req):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            user_line = SessUsers.objects.get(token=token)
            sub_val = Subs.objects.filter(subscriber=user_line.id_user).values()
            sub_list = list()
            data = {}
            for el in sub_val:
                if UsersAc.objects.filter(id=el['subscription']).exists():
                    user = UsersAc.objects.get(id=el['subscription'])
                    name_email = None
                    if user.full_name != 'Кто-то и как-то':
                        name_email = user.full_name
                    else:
                        name_email = user.email
                    sub_list.append(
                        {'id': user.id, 'name': name_email, 'pic': user.main_pic, 'desc': f'{str(user.desc)[:220]}...'})
            data['sub_list'] = sub_list
            data['template_name'] = menu_login(req)
            return render(req, 'subs.html', context=data)
        else:
            return redirect('/reg/')
    else:
        return redirect('/reg/')

# The default, even don't login users, time of posts displayed UTC time zone, there everybody can change time for himself
def change_time(req):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            time = req.POST.get('time', None)
            ind = time.find(' ')
            time = time[:ind + 1]
            time = time.replace('UTC', '')
            user.time_zone = time
            user.save()

    return redirect('/account/')


def notifications_page(req):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            data = {}
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            new_post = Notification.objects.filter(id_user=user_line.id_user, status='new_post').values() # New posts of subscriptions
            email_notf = user.true_email # If user don't apply his email
            new_comm = Notification.objects.filter(id_user=user_line.id_user, status='new_comm').values() # If someone comment user's post
            new_like = Notification.objects.filter(id_user=user_line.id_user, status='new_like').values() # If someone like or dislike user's post
            new_sub = Notification.objects.filter(id_user=user_line.id_user, status='new_sub').values() # If someone sub on user
            new_report = Notification.objects.filter(id_user=user_line.id_user, status='new_report').values() # If someone report on user and admin agree with complaint
            new_report_a = Notification.objects.filter(id_user=user_line.id_user,
                                                       status='new_report_ad').values() # Admin can send notification with unique text
            data['new_post'] = new_post
            data['new_comm'] = new_comm
            data['new_like'] = new_like
            data['new_sub'] = new_sub
            data['new_report'] = new_report
            data['email_notf'] = email_notf
            data['new_report_admin'] = new_report_a
            data['template_name'] = menu_login(req)
            return render(req, 'own_news.html', context=data)

    return redirect('/reg/')


def search_page(req):
    tags_str = req.POST.get('tags', None)
    return search_proc(tags_str, req) # The process with searching posts in the titles and posts text


def admin_menu(req): # There admin doing: ban user, send warnings, delete report if disagree
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            data = {}
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            if user.status_admin:
                if req.method == 'GET':
                    rep_list = Reports.objects.all().values()
                    data['list_report'] = rep_list
                    bad_users = []
                    with connection.cursor() as cursor:
                        cursor.execute(
                            'SELECT 1 as id, id_user, COUNT(*) count FROM blog_site_app_reportslistall GROUP BY id_user;')
                        users_rep_list = cursor.fetchall()

                    for t in users_rep_list:
                        count = t[2]
                        if count > 3:
                            id_user = t[1]
                            bad_users.append({'id_user': id_user})

                    data['users'] = bad_users
                    return render(req, 'reposts_list_admin.html', context=data)

                if req.method == 'POST':
                    id_bad_user = req.POST.get('id')
                    message = req.POST.get('message')
                    new_rep = ReportsListAll.objects.create(id_user=id_bad_user, data_of_rep=datetime.datetime.utcnow())
                    send_notf_new_rep_from_admin(id_bad_user, message)
                    return redirect('/admin/')
            else:
                return redirect('/account/')

    return redirect('/reg/')

# If we agree with report, we send a notification to guilty man
def agree_rep(req, id_rep):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            data = {}
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            rep = Reports.objects.get(id=id_rep)
            id_post = rep.path_page
            id_post = id_post.replace('/posts/', '')
            id_post = id_post.replace('/', '')
            if user.status_admin:
                if rep.comment:
                    com = Comments.objects.get(id=rep.comment)
                    bad_user = com.author_com
                else:
                    post = Post.objects.get(id=id_post)
                    bad_user = post.author

                agree = ReportsListAll.objects.create(id_user=bad_user, data_of_rep=datetime.datetime.utcnow())
                send_notf_new_rep(bad_user, id_post)
                rep.delete()
                return redirect('/admin/')

    return redirect('/account/')

# Similar top, but disagree
def disagree_rep(req, id_rep):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            data = {}
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            rep = Reports.objects.get(id=id_rep)
            id_post = rep.path_page
            id_post = id_post.replace('/posts/', '')
            id_post = id_post.replace('/', '')
            if user.status_admin:
                rep.delete()
                return redirect('/admin/')

    return redirect('/account/')

# Banning user
def do_ban(req, id_user):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None:
        if exists_token(req):
            data = {}
            user_line = SessUsers.objects.get(token=token)
            user = UsersAc.objects.get(id=user_line.id_user)
            if user.status_admin:
                user = UsersAc.objects.get(id=id_user)
                erase_dirty_user(user)
                user.delete()
                return redirect('/admin/')
    return redirect('/account/')


def contacts(req):
    if req.method == 'GET':
        data = {}
        data['template_name'] = menu_login(req)
        return render(req, 'contacts.html', context=data)
    elif req.method == 'POST':
        text = req.POST.get('quest', None)
        email = req.POST.get('email', None)
        if text and email:
            send_mail(
                subject='Бомбастик: ЗАДАЛИ ВОПРОС!',
                from_email="bombast@internet.ru",
                message=f'От кого: {email}, Вопрос: {text}',
                recipient_list=['avgustfavn@yandex.ru'],
                fail_silently=True
            )
        return redirect('/contacts/')


def chat(req):
    data = {}
    data['template_name'] = menu_login(req)
    return render(req, 'chat.html', context=data)

def send_apply_email(req):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None and exists_token(req):
        user_line = SessUsers.objects.get(token=token)
        user = UsersAc.objects.get(id=user_line.id_user)
        msg = render_to_string('message_page_apply.html')
        send_mail(
            subject='Бомбастик: Подтвердите почту',
            from_email="bombast@internet.ru",
            message='',
            html_message=msg,
            recipient_list=[user.email],
            fail_silently=True
        )
        return redirect('/account/')

    return redirect('/reg/')

def apply_email(req):
    token = req.COOKIES.get('Auth_key_blog', None)
    if token != None and exists_token(req):
        user_line = SessUsers.objects.get(token=token)
        user = UsersAc.objects.get(id=user_line.id_user)
        user.true_email = True
        user.save()
        return redirect('/account/')

    return redirect('/reg/')

