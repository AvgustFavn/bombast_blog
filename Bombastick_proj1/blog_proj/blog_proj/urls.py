"""blog_proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.template.defaulttags import url
from django.urls import path, include
from blog_site_app.views import *

urlpatterns = [
    # url(r'^', include('blog_site_app.urls')),
    # path('admin/', admin.site.urls),
    path('', index),
    path('time/', change_time),
    path('rules/', rules),
    path('notifications/', notifications_page),
    path('reg/', registration),
    path('error/<int:id>/', error_page),
    path('account/delete/yes/', delete_acc),
    path('account/delete/', delete_page),
    path('account/send_apply/', send_apply_email),
    path('account/apply_email/', apply_email),
    path('account/logout/', logout),
    path('account/', owner_acc),
    path('user/sub/', my_subs_list),
    path('user/<int:id>/sub', plus_sub),
    path('user/<int:id>/unsub', unsub),
    path('user/<int:id>/', page_user),
    path('email/', apply_email),
    path('change_pass/', change_pass),
    path('posts/next_<int:id>/', next_page_with_posts),
    path('posts/create/', create_post),
    path('posts/<int:id>/report/<int:comm>/', report_post),
    path('posts/<int:id>/report/', report_post),
    path('posts/<int:id>/delete/<int:comm>/', delete_comment),
    path('posts/<int:id>/delete/', delete_post),
    path('posts/<int:id>/update/', update_post),
    path('posts/<int:id>/dis', dislike),
    path('posts/<int:id>/like', like),
    path('posts/search/', search_page),
    path('posts/<int:id>/', page_post),
    path('admin/ban/<int:id_user>/', do_ban),
    path('admin/agree/<int:id_rep>/', agree_rep),
    path('admin/disagree/<int:id_rep>/', disagree_rep),
    path('admin/', admin_menu),
    path('posts/', main_page_with_posts),
    path('contacts/', contacts),
    path('chat/', chat),
    path('<str:url>/', is_change_pass),
]
