# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseNotAllowed, HttpResponse
from .models import User, Performance, Vacation, Out, Leave, Staff, Section, Position, Role, Message, Notice, Punch
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
import datetime

# Create your views here.


def get_login_response(request, user_obj):
    dr = {
        '超级管理员': 'root-homepage.html',
        '部门主管': 'superior-homepage.html',
        '普通员工': 'user-homepage.html',
    }
    notice = Notice.objects.filter(
        receiver=user_obj.role_id,
        date__gt=(datetime.date.today() - datetime.timedelta(days=10))
    )
    message = Message.objects.filter(
        staff_id=user_obj.staff,
        date__gt=(datetime.date.today() - datetime.timedelta(days=3))
    )
    staff_name = user_obj.staff.staff_name
    role_name = Role.objects.get(pk=user_obj.role_id).role_name
    return render(
        request,
        dr[role_name],
        {
            'notice': notice,
            'message': message,
            'staff_name': staff_name
        }
    )


def login(request):
    '''处理登录'''
    if request.method == "GET":
        return render(request, 'login.html')

    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        if username and password:
            username = username.strip()
            try:
                user_obj = User.objects.get(user_name=username)
                if check_password(password, user_obj.user_passwd):
                    request.session['user_id'] = user_obj.user_id
                    return get_login_response(request, user_obj)
                else:
                    return render(request, 'login.html', {'message': '密码错误'})
            except User.DoesNotExist:
                return render(request, 'login.html', {'message': '用户名不存在'})


def attendance(request):
    '''考勤页面显示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'attendance.html')


def get_performance(request):
    '''考勤数据获取'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    page = int(request.GET['page'])
    rows = int(request.GET['rows'])
    # 判断主管查询还是自己查询
    try:
        user_name = request.GET['user_name']
        # 主管查询
        user_obj = User.objects.get(user_name=user_name)
    except:
        # 自己查询
        try:
            user_obj = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return render(request, 'login.html', {'message': '用户信息过期，请重新登录'})

    performance_info = Performance.objects.filter(staff_id=user_obj.staff.staff_id).order_by('salaryMonth').values('salaryMonth', 'onday', 'lateday', 'offday', 'addday', 'outday')

    for i in performance_info:
        i['user_name'] = user_obj.user_name
        i['staff_name'] = user_obj.staff.staff_name
        i['salaryMonth'] = '{}-{}'.format(i['salaryMonth'].year,
                                          i['salaryMonth'].month)
    total = len(performance_info)
    res = {
        "total": total,
        "rows": performance_info[((page - 1) * rows):(page * rows)]
    }
    return JsonResponse(res)


def vacation(request):
    '''假期获取'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    userObj = User.objects.get(pk=user_id)
    vacationObj = Vacation.objects.get(staff_id=userObj.staff.staff_id)
    vacation_info = [
        {
            'field': '工号',
            'value': userObj.user_name,
        },
        {
            'field': '姓名',
            'value': userObj.staff.staff_name,
        },
        {
            'field': '年假',
            'value': vacationObj.yearday,
        },
        {
            'field': '病假',
            'value': vacationObj.illday,
        },
        {
            'field': '年休',
            'value': vacationObj.yearrest,
        },
        {
            'field': '病休',
            'value': vacationObj.illrest,
        },
        {
            'field': '剩余年假',
            'value': (int(vacationObj.yearday) - int(vacationObj.yearrest)),
        },
        {
            'field': '剩余病假',
            'value': (int(vacationObj.illday) - int(vacationObj.illrest)),
        },
    ]

    return render(request, 'vacation.html', {'vacation_info': vacation_info})


def punch(request):
    '''打卡处理'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    staff = User.objects.get(pk=user_id).staff
    try:
        Punch.objects.get(staff=staff, date__date=datetime.date.today())
        return HttpResponse('今天已经打卡了')
    except Punch.DoesNotExist:
        latetime = datetime.datetime.today().replace(hour=9, minute=0, second=0)
        performance = Performance.objects.get(staff=staff, salaryMonth__year=timezone.now(
        ).year, salaryMonth__month=timezone.now().month)
        if timezone.now() > latetime:
            Punch.objects.create(staff=staff, date=timezone.now(), late=True)
            performance.lateday += 1
        else:
            Punch.objects.create(staff=staff, date=timezone.now(), late=False)
        performance.onday += 1
        performance.save()
        return HttpResponse('打卡成功')
    return HttpResponseNotFound('404')


def salary_show(request):
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'salary.html')


def salary(request):
    '''工资获取'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    page = int(request.GET['page'])
    rows = int(request.GET['rows'])
    user_obj = User.objects.get(pk=user_id)
    vacation_obj = Vacation.objects.get(staff_id=user_obj.staff.staff_id)
    performance_info = Performance.objects.filter(staff_id=user_obj.staff.staff_id).order_by(
        'salaryMonth').values('onday', 'basepay', 'lateday', 'offday', 'addday', 'outday', 'salaryMonth')
    reslist = []
    total = len(performance_info)
    for i in performance_info:
        day_pay = i['basepay'] // 22
        overtime_pay = int(i['addday'] * day_pay * 1.5)
        outday_pay = int(i['outday'] * day_pay * 1.5)
        lateday_deduct = int(i['lateday'] * day_pay * 0.2)
        offday_deduct = int(i['offday'] * day_pay)
        busy_deduct = vacation_obj.busyday * day_pay
        if vacation_obj.illday - vacation_obj.illrest < 0:
            ill_deduct = (vacation_obj.illrest - vacation_obj.illday) * day_pay
        else:
            ill_deduct = 0
        salary = i['basepay'] + overtime_pay + outday_pay - \
            lateday_deduct - offday_deduct - busy_deduct - ill_deduct
        resdict = {
            'salaryMonth': '{}-{}'.format(i['salaryMonth'].year, i['salaryMonth'].month),
            'user_name': user_obj.user_name,
            'staff_name': user_obj.staff.staff_name,
            'onday': i['onday'],
            'basepay': i['basepay'],
            'overtime_pay': overtime_pay,
            'outday_pay': outday_pay,
            'lateday_deduct': lateday_deduct,
            'offday_deduct': offday_deduct,
            'busy_deduct': busy_deduct,
            'ill_deduct': ill_deduct,
            'totalpay': salary
        }
        reslist.append(resdict)
    res = {
        "total": total,
        "rows": reslist[((page - 1) * rows):(page * rows)]
    }
    return JsonResponse(res)


def overtime_show(request):
    '''加班申请展示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'jiaban.html')


def overtime_application(request):
    '''加班申请处理'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    if request.method == 'POST':
        startTime = request.POST.get('startTime')
        endTime = request.POST.get('endTime')
        startTime = datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M')
        endTime = datetime.datetime.strptime(endTime, '%Y-%m-%d %H:%M')
        subtime = endTime - startTime
        addday = round((subtime.days + subtime.seconds / 86400), 2)
        user_obj = User.objects.get(pk=user_id)
        performance_obj = Performance.objects.get(
            staff_id=user_obj.staff.staff_id, salaryMonth__year=timezone.now().year, salaryMonth__month=timezone.now().month)
        performance_obj.addday += addday
        performance_obj.save()
        return HttpResponse('提交成功')


def out_show(request):
    '''外出显示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'waichu.html')


def out_application(request):
    '''外出申请处理'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    if request.method == 'POST':
        destination = request.POST.get('destination')
        reason = request.POST.get('reason')
        startday = request.POST.get('startDay')
        endday = request.POST.get('endDay')
        if Out.objects.filter(startday__lt=endday, endday__gt=startday, statu__in=['unapproved', 'pass']):
            return HttpResponse('您在{}到{}已有外出在申请'.format(startday, endday))
        user_obj = User.objects.get(pk=user_id)
        Out.objects.create(destination=destination, reason=reason,
                           startday=startday, endday=endday,
                           staff_id=user_obj.staff.staff_id,
                           applytime=timezone.now())
        role = Role.objects.get(pk=user_obj.role_id).role_name
        if role == '普通员工':
            boss = Staff.objects.get(
                section__section_id=user_obj.staff.section_id, user__role__role_name='部门主管')
            Message.objects.create(staff=boss, title='外出申请', content='您的员工{}申请在{}到{}外出到{}，请处理'.format(
                user_obj.staff.staff_name, startday, endday, destination))
        elif role == '部门主管':
            boss = Staff.objects.filter(user__role__role_name='超级管理员')
            for i in boss:
                Message.objects.create(staff=i, title='外出申请', content='您的员工{}申请在{}到{}外出到{}，请处理'.format(
                    user_obj.staff.staff_name, startday, endday, destination))
        return HttpResponse('申请已提交，等待批复')
    return HttpResponseNotFound('404 not found')


def vacation_apply_show(request):
    '''请假申请展示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'qingjia.html')


def vacation_apply(request):
    '''请假申请处理'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    if request.method == 'POST':
        kind = request.POST.get('kind')
        reason = request.POST.get('reason')
        startday = request.POST.get('startDay')
        endday = request.POST.get('endDay')
        if Leave.objects.filter(startday__lt=endday, endday__gt=startday, statu__in=['unapproved', 'pass']):
            return HttpResponse('您在{}到{}已有请假在申请'.format(startday, endday))
        user_obj = User.objects.get(pk=user_id)
        staff_id = user_obj.staff.staff_id
        applytime = timezone.now()
        statu = 'unapproved'
        Leave.objects.create(kind=kind, reason=reason, startday=startday,
                             endday=endday, staff_id=staff_id, applytime=applytime, statu=statu)
        role = Role.objects.get(pk=user_obj.role_id).role_name
        if role == '普通员工':
            boss = Staff.objects.get(
                section__section_id=user_obj.staff.section_id, user__role__role_name='部门主管')
            Message.objects.create(staff=boss, title='请假申请', content='您的员工{}申请在{}到{}请假，请处理'.format(
                user_obj.staff.staff_name, startday, endday))
        elif role == '部门主管':
            boss = Staff.objects.filter(user__role__role_name='超级管理员')
            for i in boss:
                Message.objects.create(staff=i, title='请假申请', content='您的员工{}申请在{}到{}请假，请处理'.format(
                    user_obj.staff.staff_name, startday, endday))
        return HttpResponse('提交成功，等待审批')
    return HttpResponseNotFound('404 not found')


def addresslist_show(request):
    '''通讯录页面展示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'addresslist.html')


def addresslist(request):
    '''通讯录查询'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    page = int(request.GET['page'])
    rows = int(request.GET['rows'])
    user_obj = User.objects.exclude(
        role_id=Role.objects.get(role_name='超级管理员').role_id)
    staff_obj = Staff.objects.all()
    section_obj = Section.objects.all()
    position_obj = Position.objects.all()
    rowslist = []
    for i in user_obj:
        staff = staff_obj.get(staff_id=i.staff.staff_id)
        idict = {
            'user_name': i.user_name,
            'staff_name': staff.staff_name,
            'gender': humansee(staff.gender),
            'Email': staff.Email,
            'phone': staff.phone_num,
            'section': section_obj.get(section_id=staff.section_id).section_name,
            'position': position_obj.get(position_id=staff.position_id).position_name,
        }
        rowslist.append(idict)
    total = len(user_obj)
    res = {
        "total": total,
        "rows": rowslist[((page - 1) * rows):(page * rows)]
    }
    return JsonResponse(res)


def personal(request):
    '''个人信息显示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    try:
        user_obj = User.objects.get(pk=user_id)
        staff = user_obj.staff
        user_name = user_obj.user_name
        section = Section.objects.get(section_id=staff.section_id).section_name
        position = Position.objects.get(
            position_id=staff.position_id).position_name
        staff = staff
        month = staff.birth.month
        if month < 10:
            month = '0' + str(month)
        day = staff.birth.day
        if day < 10:
            day = '0' + str(day)
        birth = '{}-{}-{}'.format(staff.birth.year,
                                  month, day)
        return render(request, 'personal.html', locals())
    except Exception as e:
        print(e)


def personal_submit(request):
    '''个人信息修改'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    if request.method == 'POST':
        staff = User.objects.get(pk=user_id).staff
        staff_name = request.POST.get('staffName')
        gender = request.POST.get('gender')
        birth = request.POST.get('birth')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        try:
            photo = request.FILES['photo']
            if photo:
                staff.photo = photo
        except KeyError:
            pass
        staff.staff_name = staff_name
        staff.gender = gender
        staff.birth = birth
        staff.phone_num = phone
        staff.Email = email
        staff.save()
        return redirect('personal')
    return HttpResponseNotFound('404 not found')


def section_information_show(request):
    '''部门信息页面显示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'section-information.html')


def section_information(request):
    '''部门主管的部门信息'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    if request.method == 'GET':
        page = int(request.GET['page'])
        rows = int(request.GET['rows'])
        user_obj = User.objects.get(pk=user_id)
        if Role.objects.get(pk=user_obj.role_id).role_name == '部门主管':
            staff = Staff.objects.filter(
                section=user_obj.staff.section).exclude(user=user_id)
            rowlist = []
            for i in staff:
                idict = {
                    'section': Section.objects.get(pk=i.section_id).section_name,
                    'user_name': i.user.user_name,
                    'staff_name': i.staff_name,
                    'gender': humansee(i.gender),
                    'position': Position.objects.get(pk=i.position_id).position_name,
                    'email': i.Email,
                    'phone': i.phone_num,
                    'degree': i.degree,
                    'school': i.school,
                    'hiredate': i.hiredate,
                }
                rowlist.append(idict)
            total = len(staff)
            res = {
                "total": total,
                "rows": rowlist[((page - 1) * rows):(page * rows)],
            }
            return JsonResponse(res)


def humansee(string):
    strdict = {
        "pass": "通过",
        "refuse": "拒绝",
        "unapproved": "未批复",
        "sthday": "事假",
        "illday": "病假",
        "year": "年休",
        'male': '男',
        'female': '女',
    }
    return strdict[string]


def approval(request, atype):
    '''处理请假外出记录显示'''

    def deal(a_value):
        rowlist = []
        for l in a_value:
            staff = Staff.objects.get(pk=l['staff_id'])
            ldict = {
                'date': l['applytime'],
                'user_name': User.objects.get(staff=staff).user_name,
                'staff_name': staff.staff_name,
                'section': Section.objects.get(pk=staff.section_id).section_name,
                'position': Position.objects.get(pk=staff.position_id).position_name,
                'reason': l['reason'],
                'startday': l['startday'],
                'endday': l['endday'],
                'status': humansee(l['statu']),
            }
            if atype == Out:
                ldict['destination'] = l['destination']
                ldict['id'] = l['out_id']
            if atype == Leave:
                ldict['kind'] = humansee(l['kind'])
                ldict['id'] = l['leave_id']
            rowlist.append(ldict)
        total = len(a_value)
        res = {
            "total": total,
            "rows": rowlist[((page - 1) * rows):(page * rows)]
        }
        return res
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    if request.method == 'GET':
        user_obj = User.objects.get(pk=user_id)
        page = int(request.GET.get('page'))
        rows = int(request.GET.get('rows'))
        role = Role.objects.get(role_id=user_obj.role_id)
        if role.role_name == '部门主管':
            a_value = atype.objects.filter(staff__section_id=user_obj.staff.section_id, statu='unapproved').exclude(
                staff=user_obj.staff).values()
            return deal(a_value)
        elif role.role_name == '超级管理员':
            a_value = atype.objects.filter(
                staff__user__role__role_name='部门主管', statu='unapproved').values()
            return deal(a_value)
        return 403
    return 404


def vacation_approval_show(request):
    '''请假页面显示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'qingjiacheck.html')


def vacation_approval(request):
    '''请假记录查询'''
    res = approval(request, Leave)
    if type(res).__name__ == 'dict':
        return JsonResponse(res)
    elif res == 403:
        return HttpResponseNotAllowed('无此权限')
    else:
        return HttpResponseNotFound('404 not found')


def leave_deal(request):
    '''请假审批处理'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    role = Role.objects.get(pk=User.objects.get(pk=user_id).role_id)
    if role.role_name == '普通员工':
        return HttpResponseNotAllowed('无此权限')
    if request.method == 'POST':
        ids = request.POST.get('ids')
        app = request.POST.get('app')
        ids = map(lambda x: int(x), ids.split())
        exmess = ''
        if app == 'pass':
            for i in ids:
                leave = Leave.objects.get(pk=i)
                staff = Staff.objects.get(pk=leave.staff_id)
                if leave.statu != 'unapproved':
                    exmess += ' {}的请假已被其他人处理 '.format(staff.staff_name)
                    continue
                leave.statu = 'pass'
                day = (leave.endday - leave.startday).days
                vacation = Vacation.objects.get(staff_id=leave.staff_id)
                if leave.kind == 'sthday':
                    vacation.busyday += day
                elif leave.kind == 'illday':
                    vacation.illrest += day
                elif leave.kind == 'year':
                    if vacation.yearrest + day > vacation.yearday:
                        return HttpResponse('{}的年假不足!'.format(staff.staff_name))
                    vacation.yearrest += day
                else:
                    return HttpResponseNotFound('404')
                leave.save()
                vacation.save()
                Message.objects.create(staff_id=staff.staff_id, title='请假审批回复',
                                       content='您从{}到{}的请假已被批准!!'.format(leave.startday, leave.endday))
            return HttpResponse('操作成功' + exmess)
        elif app == 'reject':
            Leave.objects.filter(pk__in=ids).update(statu='refuse')
            for i in ids:
                leave = Leave.objects.get(pk=i)
                staff = Staff.objects.get(pk=leave.staff_id)
                if leave.statu != 'unapproved':
                    exmess += ' {}的请假已被其他人处理 '.format(staff.staff_name)
                    continue
                Message.objects.create(staff_id=staff.staff_id, title='请假审批回复',
                                       content='您从{}到{}的请假已被拒绝!!'.format(leave.startday, leave.endday))
            return HttpResponse('操作成功' + exmess)
    return HttpResponseNotFound('404')


def out_approval_show(request):
    '''外出页面显示'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    return render(request, 'waichucheck.html')


def out_approval(request):
    '''外出记录查询'''
    res = approval(request, Out)
    if type(res).__name__ == 'dict':
        return JsonResponse(res)
    elif res == 403:
        return HttpResponseNotAllowed('无此权限')
    else:
        return HttpResponseNotFound('404 not found')


def out_deal(request):
    '''外出审批处理'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    role = Role.objects.get(pk=User.objects.get(pk=user_id).role_id)
    if role.role_name == '普通员工':
        return HttpResponseNotAllowed('无此权限')
    if request.method == 'POST':
        ids = request.POST.get('ids')
        app = request.POST.get('app')
        ids = map(lambda x: int(x), ids.split())
        exmess = ''
        if app == 'pass':
            for i in ids:
                out = Out.objects.get(pk=i)
                staff = Staff.objects.get(pk=out.staff_id)
                if out.statu != 'unapproved':
                    exmess += ' {}的外出已被其他人处理 '.format(staff.staff_name)
                    continue
                out.statu = 'pass'
                day = (out.endday - out.startday).days
                performance = Performance.objects.get(
                    staff_id=staff, salaryMonth__year=out.startday.year, salaryMonth__month=out.startday.month)
                performance.outday += day
                Message.objects.create(staff_id=staff.staff_id, title='外出审批回复',
                                       content='您从{}到{}的外出已被批准!!'.format(out.startday, out.endday))
                out.save()
                performance.save()
                return HttpResponse('操作成功' + exmess)
        elif app == 'reject':
            for i in ids:
                out = Out.objects.get(pk=i)
                staff = Staff.objects.get(pk=out.staff_id)
                if out.statu != 'unapproved':
                    exmess += ' {}的外出已被其他人处理 '.format(staff.staff_name)
                    continue
                out.statu = 'refuse'
                Message.objects.create(staff_id=staff.staff_id, title='外出审批回复',
                                       content='您从{}到{}的外出已被拒绝!!'.format(leave.startday, leave.endday))
            return HttpResponse('操作成功' + exmess)
    return HttpResponseNotFound('404')


def logout(request):
    '''退出系统'''
    del request.session['user_id']
    return render(request, 'login.html')


def showjob(request):
    '''返回职位页面'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    user_obj = User.objects.get(pk=user_id)
    if Role.objects.get(role_id=user_obj.role_id).role_name == '超级管理员':
        section = Section.objects.exclude(pk=user_obj.staff.section_id)
        return render(request, 'job.html', {'section': section})
    return HttpResponseNotAllowed('无此权限')


def getjob(request):
    '''获取职位数据'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    user_obj = User.objects.get(pk=user_id)
    if Role.objects.get(role_id=user_obj.role_id).role_name == '超级管理员':
        page = request.GET['page']
        rows = request.GET['rows']
        Position_list = list(Position.objects.exclude(pk=user_obj.staff.position_id).values(
            'position_id', 'position_name', 'section_id'))
        for i in Position_list:
            i["section_name"] = Section.objects.get(
                section_id=i["section_id"]).section_name
        total = len(Position_list)
        p = int(page) - 1
        r = int(rows)
        row = Position_list[(p * r):]
        joblist = {"total": total, "rows": row}
        return JsonResponse(joblist)
    return HttpResponseNotAllowed('无此权限')


def showsection(request):
    '''返回部门页面'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    return render(request, 'section.html')


def getsection(request):
    '''获取部门数据'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    user_obj = User.objects.get(pk=user_id)
    if Role.objects.get(role_id=user_obj.role_id).role_name == '超级管理员':
        page = int(request.GET['page'])
        rows = int(request.GET['rows'])
        Section_list = list(Section.objects.exclude(
            pk=user_obj.staff.section_id).values())
        total = len(Section_list)
        row = Section_list[((page - 1) * rows):(page * rows)]
        sectionlist = {"total": total, "rows": row}
        return JsonResponse(sectionlist)
    return HttpResponseNotAllowed('无此权限')


def showstaff(request):
    '''返回员工页面'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    user_obj = User.objects.get(pk=user_id)
    if Role.objects.get(pk=user_obj.role_id).role_name == '超级管理员':
        role = Role.objects.exclude(role_name='超级管理员')
        section = Section.objects.exclude(pk=user_obj.staff.section_id)
        position = Position.objects.exclude(pk=user_obj.staff.position_id)
        return render(request, 'staff.html',
                      {'role': role, 'section': section, 'position': position})
    return HttpResponseNotAllowed('无此权限')


def getstaff(request):
    '''获取员工数据'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    page = int(request.GET['page'])
    rows = int(request.GET['rows'])
    if Role.objects.get(role_id=User.objects.get(pk=user_id).role_id).role_name == '超级管理员':
        Staff_list = list(Staff.objects.exclude(user__role__role_name='超级管理员').values(
            'staff_id', 'staff_name', 'gender', 'birth', 'degree',
            'Email', 'phone_num', 'hiredate', 'school', 'staff_remarks',
            'position_id', 'section_id', 'user_id', 'address'))
        for i in Staff_list:
            userobj = User.objects.filter(user_id=i['user_id']).first()
            i['gender'] = Staff.objects.get(
                staff_id=i['staff_id']).get_gender_display()
            i['yearday'] = Vacation.objects.get(staff_id=i['staff_id']).yearday
            i['illday'] = Vacation.objects.get(staff_id=i['staff_id']).illday
            i['user_id'] = userobj.user_name
            i['role_name'] = Role.objects.get(
                role_id=userobj.role_id).role_name
            i['role_id'] = Role.objects.get(role_id=userobj.role_id).role_id
            i['staff_id'] = Performance.objects.get(
                staff_id=i['staff_id']).basepay
            i['section_name'] = Section.objects.filter(
                section_id=i['section_id']).first().section_name
            i['position_name'] = Position.objects.get(
                position_id=i['position_id']).position_name
            i['section_id'] = Section.objects.filter(
                section_id=i['section_id']).first().section_id
            i['position_id'] = Position.objects.get(
                position_id=i['position_id']).position_id
        total = len(Staff_list)
        row = Staff_list[((page - 1) * rows):(page * rows)]
        stafflist = {'total': total, 'rows': row}
        return JsonResponse(stafflist)
    return HttpResponseNotAllowed('无此权限')


def showupdatepwd(request):
    '''返回修改密码页面'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    return render(request, 'updatepwd.html')


def getupdatepwd(request):
    '''修改密码'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    if request.method == 'POST':
        opwd = request.POST.get('opwd')
        npwd = request.POST.get('npwd')
        getuser = User.objects.get(user_id=request.session['user_id'])
        pwd = getuser.user_passwd
        if check_password(opwd, pwd):
            npwd = make_password(npwd)
            getuser.user_passwd = npwd
            getuser.save()
            return HttpResponse('修改成功')
    return HttpResponse('原密码输入不正确！')


def shownotice(request):
    '''返回发送通知页面'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    return render(request, 'notice.html')


def sendnotice(request):
    '''发送通知'''
    try:
        user_id = request.session['user_id']
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            title = request.POST.get('title')
            content = request.POST.get('content')
            staff = request.POST.get('staff')
            superior = request.POST.get('superior')
            isstaff = request.POST.get('isstaff')
            issuperior = request.POST.get('issuperior')
            if isstaff == 'false' and issuperior == 'false':
                return HttpResponse('未选择接收人！！')
            # str_ = ''
            # if isstaff == 'true':
            #     num1 = Role.objects.get(role_name=str(staff)).role_id
            #     str_ += str(num1) + ' '
            # if issuperior == 'true':
            #     num2 = Role.objects.get(role_name=str(superior)).role_id
            #     str_ += str(num2) + ' '
            if isstaff == 'true':
                noticeobj = Notice(title=title, content=content,
                                   receiver=3, sender=User.objects.get(pk=user_id).staff)
                noticeobj.save()
            if issuperior == 'true':
                noticeobj = Notice(title=title, content=content,
                                   receiver=2, sender=User.objects.get(pk=user_id).staff)
                noticeobj.save()
    except:
        return HttpResponse('发送失败')
    else:
        return HttpResponse('发送成功')


def addstaff(request):
    '''添加员工信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            for key, value in request.POST.items():
                if not value and key != 'staff_remarks' and key != 'csrfmiddlewaretoken':
                    return HttpResponse('亲，不填数据想啥呢！', status=400)
            staffnum = request.POST.get('user_id')
            for u in User.objects.values('user_name'):
                if staffnum == u['user_name']:
                    return HttpResponse('已存在该工号', status=400)
            userpwd = request.POST.get('user_passwd')
            role_id = request.POST.get('role_id')
            section = request.POST.get('section_id')
            salary = request.POST.get('staff_id')
            job = request.POST.get('position_id')
            yearday = request.POST.get('yearday')
            illday = request.POST.get('illday')
            print(type(yearday))
            if int(yearday) < 0 or int(yearday) > 100:
                return HttpResponse('年假填写有误!', status=400)
            if int(illday) < 0 or int(illday) > 100:
                return HttpResponse('病假填写有误!', status=400)
            degree = request.POST.get('degree')
            school = request.POST.get('school')
            staffname = request.POST.get('staff_name')
            gender = request.POST.get('gender')
            hiredate = request.POST.get('hiredate')
            birth = request.POST.get('birth')
            if datetime.datetime.strptime(hiredate, '%Y-%m-%d') > datetime.datetime.today():
                return HttpResponse('入职日期填写有误', status=400)
            if datetime.datetime.strptime(birth, '%Y-%m-%d') > datetime.datetime.today():
                return HttpResponse('出生日期填写有误', status=400)
            phonenum = request.POST.get('phone_num')
            if len(phonenum) != 11:
                return HttpResponse('电话号码必须为11位!', status=400)
            Email = request.POST.get('Email')
            for e in Staff.objects.values('Email'):
                if Email == e['Email']:
                    return HttpResponse('已存在该邮箱', status=400)
            remarks = request.POST.get('staff_remarks')
            address = request.POST.get("address")
            userpwd = make_password(userpwd)
            with transaction.atomic():
                u = User(user_name=staffnum, user_passwd=userpwd,
                         role_id=role_id)
                u.save()
                s = Staff(staff_name=staffname, gender=gender, birth=birth,
                          address=address, degree=degree, Email=Email,
                          phone_num=phonenum, hiredate=hiredate, school=school,
                          staff_remarks=remarks, section_id=section,
                          position_id=job, user_id=u.user_id)
                s.save()
                sec = Section.objects.get(pk=section)
                sec.section_num += 1
                sec.save()
                p = Performance(
                    basepay=salary, onday=0, offday=0,
                    addday=0, outday=0, staff_id=s.staff_id)
                p.save()
                v = Vacation(yearday=yearday, illday=illday,
                             staff_id=s.staff_id)
                v.save()
    except Exception as e:
        print(e)
        return HttpResponse('添加失败', status=400)
    else:
        return HttpResponse('添加成功')


def updstaff(request):
    '''修改员工信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            for key, value in request.POST.items():
                if not value and key != 'staff_remarks' and key != 'csrfmiddlewaretoken' and key != 'user_passwd':
                    return HttpResponse('亲，不填数据想啥呢！')
            staffnum = request.POST.get('user_id')
            userpwd = request.POST.get('user_passwd')
            role_id = request.POST.get('role_id')
            section = request.POST.get('section_id')
            salary = request.POST.get('staff_id')
            job = request.POST.get('position_id')
            yearday = request.POST.get('yearday')
            illday = request.POST.get('illday')
            remarks = request.POST.get('staff_remarks')
            user_obj = User.objects.filter(user_name=staffnum).first()
            staff_obj = user_obj.staff
            with transaction.atomic():
                if userpwd:
                    userpwd = make_password(userpwd)
                    user_obj.user_passwd = userpwd
                user_obj.role_id = role_id
                user_obj.save()
                section_obj1 = Section.objects.filter(
                    section_id=staff_obj.section_id).first()
                section_obj1.section_num -= 1
                section_obj1.save()
                section_obj2 = Section.objects.filter(
                    section_id=section).first()
                section_obj2.section_num += 1
                section_obj2.save()
                staff_obj.staff_remarks = remarks
                staff_obj.section_id = section
                staff_obj.position_id = job
                staff_obj.save()
                Performance.objects.filter(
                    staff_id=staff_obj, salaryMonth__year=timezone.now().year,
                    salaryMonth__month=timezone.now().month).update(basepay=salary)
                Vacation.objects.filter(staff_id=staff_obj).update(
                    yearday=yearday, illday=illday)
                Message.objects.create(
                    staff=staff_obj, title='个人信息修改', content='您的个人信息已被修改，请到个人信息页面查看！')
    except Exception as e:
        print(e)
        return HttpResponse('修改失败')
    else:
        return HttpResponse('修改成功')


def delstaff(request):
    '''删除员工信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            staffnum = request.POST.get('user_name')
            with transaction.atomic():
                user_obj = User.objects.filter(user_name=staffnum).first()
                staff_obj = user_obj.staff
                section_obj = Section.objects.filter(
                    pk=staff_obj.section_id).first()
                section_obj.section_num -= 1
                section_obj.save()
                user_obj.delete()
    except Exception as e:
        print(e)
        return HttpResponse('删除失败')
    else:
        return HttpResponse('删除成功')


def addsection(request):
    '''增加部门信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            for key, value in request.POST.items():
                if not value and key != 'csrfmiddlewaretoken' and key != 'section_remarks':
                    return HttpResponse('亲，不填数据想啥呢！')
            section_name = request.POST.get('section_name')
            section_remarks = request.POST.get('section_remarks')
            with transaction.atomic():
                s = Section(
                    section_name=section_name, section_remarks=section_remarks)
                s.save()
    except Exception as e:
        print(e)
        return HttpResponse('添加失败')
    else:
        return HttpResponse('添加成功')


def updsection(request):
    '''修改部门信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            for key, value in request.POST.items():
                if not value and key != 'csrfmiddlewaretoken' and key != 'section_remarks':
                    return HttpResponse('亲，不填数据想啥呢！')
            section_id = request.POST.get('section_id')
            section_name = request.POST.get('section_name')
            section_remarks = request.POST.get('section_remarks')
            print(request.POST)
            with transaction.atomic():
                Section.objects.filter(section_id=section_id).update(
                    section_name=section_name, section_remarks=section_remarks)
    except Exception as e:
        print(e)
        return HttpResponse('修改失败')
    else:
        return HttpResponse('修改成功')


def delsection(request):
    '''删除部门信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            section_id = request.POST.get('section_id')
            with transaction.atomic():
                Section.objects.filter(section_id=section_id).delete()
    except Exception as e:
        print(e)
        return HttpResponse('删除失败')
    else:
        return HttpResponse('删除成功')


def addjob(request):
    '''增加职位信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            for key, value in request.POST.items():
                if not value and key != 'csrfmiddlewaretoken' and key != 'position_id':
                    return HttpResponse('亲，不填数据想啥呢！')
            position_name = request.POST.get('position_name')
            section_id = request.POST.get('section_id')
            with transaction.atomic():
                p = Position(position_name=position_name,
                             section_id=section_id)
                p.save()
    except Exception as e:
        print(e)
        return HttpResponse('添加失败')
    else:
        return HttpResponse('添加成功')


def updjob(request):
    '''修改职位信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            for key, value in request.POST.items():
                if not value and key != 'csrfmiddlewaretoken':
                    return HttpResponse('亲，不填数据想啥呢！')
            position_id = request.POST.get('position_id')
            position_name = request.POST.get('position_name')
            section_id = request.POST.get('section_id')
            print(request.POST)
            with transaction.atomic():
                Position.objects.filter(position_id=position_id).update(
                    position_name=position_name, section_id=section_id)
    except Exception as e:
        print(e)
        return HttpResponse('修改失败')
    else:
        return HttpResponse('修改成功')


def deljob(request):
    '''删除职位信息'''
    try:
        eval("request.session['user_id']")
    except KeyError:
        return redirect('login')
    try:
        if request.method == 'POST':
            position_id = request.POST.get('position_id')
            boo = Staff.objects.filter(position_id=position_id).first()
            if(boo):
                return HttpResponse('亲，不能这样子删除数据哦！')
            else:
                with transaction.atomic():
                    Position.objects.filter(position_id=position_id).delete()

    except Exception as e:
        print(e)
        return HttpResponse('删除失败')
    else:
        return HttpResponse('删除成功')
