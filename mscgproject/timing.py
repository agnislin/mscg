from user.models import Punch, Performance, Staff, User, Role, Leave, Out
import datetime


def absence():
    '''每天0点记录缺勤'''
    staff = Staff.objects.exclude(user__role__role_name='超级管理员')
    for i in staff:
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        try:
            Punch.objects.get(staff=i, date__date=yesterday)
        except Punch.DoesNotExist:
            try:
                Leave.objects.get(
                    staff=i, startday__lte=yesterday, endday__gt=yesterday, statu='pass')
            except Leave.DoesNotExist:
                try:
                    Out.objects.get(staff=i, startday__lte=yesterday,
                                    endday__gt=yesterday, statu='pass')
                except Out.DoesNotExist:
                    performance = Performance.objects.get(
                        staff=i, salaryMonth__year=today.year, salaryMonth__month=today.month)
                    performance.offday += 1
                    performance.save()


def updatePer():
    '''每月1号更新考勤记录'''
    staff = Staff.objects.exclude(user__role__role_name='超级管理员')
    # 上月
    lastmonth = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    lastmonth_year = lastmonth.year
    lastmonth_month = lastmonth.month
    for i in staff:
        lastmonth_p = Performance.objects.get(
            staff=i, salaryMonth__year=lastmonth_year, salaryMonth__month=lastmonth_month)
        Performance.objects.create(staff=i, basepay=lastmonth_p.basepay)
