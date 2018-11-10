# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""mscgproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path
from user import views as user_views
from django.conf import settings             # 新加入
from django.conf.urls.static import static   # 新加入
# 定时任务
from apscheduler.schedulers.background import BackgroundScheduler
from .timing import absence, updatePer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.login, name='login'),
    path('attendance/', user_views.attendance, name='attendance'),
    path('get_performance/', user_views.get_performance, name='get_performance'),
    path('vacation/', user_views.vacation, name='vacation'),
    path('punch/', user_views.punch, name='punch'),
    path('salary_show/', user_views.salary_show, name='salary_show'),
    path('salary/', user_views.salary, name='salary'),
    path('overtime_show/', user_views.overtime_show, name='overtime_show'),
    path('overtime_application/', user_views.overtime_application,
         name='overtime_application'),
    path('out_show/', user_views.out_show, name='out_show'),
    path('out_application/', user_views.out_application, name='out_application'),
    path('vacation_apply_show/', user_views.vacation_apply_show,
         name='vacation_apply_show'),
    path('vacation_apply/', user_views.vacation_apply, name='vacation_apply'),
    path('addresslist_show/', user_views.addresslist_show, name='addresslist_show'),
    path('addresslist/', user_views.addresslist, name='addresslist'),
    path('personal/', user_views.personal, name='personal'),
    path('personal_submit/', user_views.personal_submit, name='personal_submit'),
    path('section_information_show/', user_views.section_information_show,
         name='section_information_show'),
    path('section_information/', user_views.section_information,
         name='section_information'),
    path('vacation_approval_show/', user_views.vacation_approval_show,
         name='vacation_approval_show'),
    path('vacation_approval/', user_views.vacation_approval,
         name='vacation_approval'),
    path('leave_deal/', user_views.leave_deal, name='leave_deal'),
    path('out_approval_show/', user_views.out_approval_show,
         name='out_approval_show'),
    path('out_approval/', user_views.out_approval, name='out_approval'),
    path('out_deal/', user_views.out_deal, name='out_deal'),
    path('logout/', user_views.logout, name='logout'),
    path('getjob/', user_views.getjob, name='getjob'),
    path('showjob/', user_views.showjob, name='showjob'),
    path('getsection/', user_views.getsection, name='getsection'),
    path('showsection/', user_views.showsection, name='showsection'),
    path('getstaff/', user_views.getstaff, name='getstaff'),
    path('showstaff/', user_views.showstaff, name='showstaff'),
    path('getupdatepwd/', user_views.getupdatepwd, name='getupdpwd'),
    path('showupdatepwd/', user_views.showupdatepwd, name='showupdpwd'),
    path('shownotice/', user_views.shownotice, name='shownotice'),
    path('sendnotice/', user_views.sendnotice, name='sendnotice'),
    path('addstaff/', user_views.addstaff, name='addstaff'),
    path('updstaff/', user_views.updstaff, name='updstaff'),
    path('delstaff/', user_views.delstaff, name='delstaff'),
    path('addsection/', user_views.addsection, name='addsection'),
    path('updsection/', user_views.updsection, name='updsection'),
    path('delsection/', user_views.delsection, name='delsection'),
    path('addjob/', user_views.addjob, name='addjob'),
    path('updjob/', user_views.updjob, name='updjob'),
    path('deljob/', user_views.deljob, name='deljob'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


sched = BackgroundScheduler()

sched.add_job(absence, 'cron', day_of_week='mon-fri', hour='0')

sched.add_job(updatePer, 'cron', day='1')

sched.start()
