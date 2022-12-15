import os
from blog_proj.settings import BASE_DIR


def valid_user(user):
    # email valid
    if not '@' in user.email:
        return {'email': False}
    elif not '.' in user.email:
        return {'email': False}
    elif len(user.email) < 5:
        return {'email': False}

    # password valid
    v_pass = valid_p(user.password)
    if v_pass:
        return v_pass

    # pic valid
    if user.main_pic != None and os.path.getsize(os.path.join(BASE_DIR, 'blog_site_app') + user.main_pic) > 1048576:  # 1mb
        return {'pic': False}


def valid_post(post):
    # pic valid
    if post.pic_mini != None and os.path.getsize(
            os.path.join(BASE_DIR, 'blog_site_app') + post.pic_mini) > 1048576:
        return {'pic': False}
    elif post.pic_1 != None and os.path.getsize(os.path.join(BASE_DIR, 'blog_site_app') + post.pic_1) > 1048576:  # 1mb
        return {'pic': False}
    elif post.pic_2 != None and os.path.getsize(os.path.join(BASE_DIR, 'blog_site_app') + post.pic_2) > 1048576:  # 1mb
        return {'pic': False}
    elif post.pic_3 != None and os.path.getsize(os.path.join(BASE_DIR, 'blog_site_app') + post.pic_3) > 1048576:  # 1mb
        return {'pic': False}

def valid_p(passw):
    if len(passw) < 3:
        return {'password': False}

