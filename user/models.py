# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
# Create your models here.


class User(models.Model):
    user_id = models.AutoField(
        primary_key=True, verbose_name="用户ID")
    user_name = models.CharField(
        max_length=20, unique=True, verbose_name="用户名", default='null')
    user_passwd = models.CharField(
        max_length=128, verbose_name="密码", default='null')
    role = models.ForeignKey(
        'Role', null=True, verbose_name="角色ID", on_delete=models.CASCADE)

    def __str__(self):
        return self.user_name


def user_photo_path(instance, filename):
    return '{0}/{1}'.format(instance.user.user_id, filename)


class Staff(models.Model):
    sex = (
        ('male', '男'),
        ('female', '女'),
    )
    staff_id = models.AutoField(
        primary_key=True, unique=True, verbose_name="员工id")
    staff_name = models.CharField(
        max_length=20, verbose_name="员工姓名")
    gender = models.CharField(
        max_length=10, choices=sex, default='男', verbose_name="性别")
    birth = models.DateField(verbose_name='生日', default=timezone.now)
    photo = models.ImageField(
        upload_to=user_photo_path, default='default/default.jpg')
    address = models.CharField(max_length=50, verbose_name="地址")
    section = models.ForeignKey(
        'Section', null=True, blank=True, verbose_name="部门ID", on_delete=models.CASCADE)
    position = models.ForeignKey(
        'Position', null=True, blank=True, verbose_name="职位ID", on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    degree = models.CharField(max_length=10, verbose_name="学历")
    Email = models.EmailField(unique=True, verbose_name="邮箱")
    phone_num = models.CharField(max_length=30, verbose_name="电话号码")
    hiredate = models.DateField(verbose_name="入职日期", default=timezone.now)
    school = models.CharField(max_length=25, verbose_name="毕业院校")
    staff_remarks = models.TextField('备注', null=True)

    def __str__(self):
        return self.staff_name


class Section(models.Model):
    section_id = models.AutoField(
        primary_key=True, verbose_name="部门ID")
    section_name = models.CharField(max_length=25, verbose_name="部门名称")
    section_num = models.PositiveIntegerField("部门人数", default=0)
    section_remarks = models.TextField("备注", null=True)

    def __str__(self):
        return self.section_name


class Position(models.Model):
    position_id = models.AutoField(
        primary_key=True, verbose_name="职位ID")
    position_name = models.CharField(max_length=25, verbose_name="职位名称")
    section = models.ForeignKey(
        'Section', verbose_name="部门ID", null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.position_name


class Role(models.Model):
    role_id = models.AutoField(
        primary_key=True, unique=True, verbose_name="角色ID")
    role_name = models.CharField(max_length=20, verbose_name="角色名称")

    def __str__(self):
        return self.role_name


class Performance(models.Model):
    performance_id = models.AutoField(primary_key=True, verbose_name="考勤ID")
    staff = models.ForeignKey(
        'Staff', null=True, verbose_name="员工ID", on_delete=models.CASCADE)
    basepay = models.FloatField(verbose_name="基本工资")
    onday = models.PositiveSmallIntegerField("出勤天数", default=0)
    offday = models.PositiveSmallIntegerField("缺勤天数", default=0)
    addday = models.FloatField("加班天数", default=0)
    outday = models.PositiveSmallIntegerField("外出天数", default=0)
    lateday = models.PositiveSmallIntegerField('迟到天数', default=0)
    salaryMonth = models.DateField(verbose_name="日期", default=timezone.now)

    def __str__(self):
        return str(self.performance_id)


class Vacation(models.Model):
    vacation_id = models.AutoField(primary_key=True, verbose_name="假期ID")
    staff = models.ForeignKey(
        'Staff', null=True, verbose_name="员工ID", on_delete=models.CASCADE)
    yearday = models.PositiveSmallIntegerField(verbose_name="年假", default=0)
    illday = models.PositiveSmallIntegerField(verbose_name="病假", default=0)
    busyday = models.PositiveSmallIntegerField(verbose_name='事假', default=0)
    yearrest = models.PositiveSmallIntegerField(default=0, verbose_name="年休")
    illrest = models.PositiveSmallIntegerField(default=0, verbose_name="病休")

    def __str__(self):
        return str(self.vacation_id)


class Notice(models.Model):
    notice_id = models.AutoField(primary_key=True, verbose_name="通知ID")
    date = models.DateField(auto_now=True, verbose_name='通知时间')
    title = models.CharField(
        max_length=20, verbose_name='通知标题', default='通知标题')
    content = models.TextField(
        verbose_name='内容', max_length=500, default='通知内容')
    receiver = models.ManyToManyField(Role)
    sender = models.ForeignKey(
        'Staff', null=True, verbose_name='发送人ID', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.notice_id)


class Out(models.Model):
    '''外出表'''
    select_statu = (
        ("pass", "通过"),
        ("refuse", "拒绝"),
        ("unapproved", "未批复"),
    )
    out_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(
        'Staff', null=True, verbose_name="员工ID", on_delete=models.CASCADE)
    destination = models.CharField(max_length=36, verbose_name="目的地")
    reason = models.TextField(
        max_length=200, verbose_name="外出事由", default='外出事由')
    applytime = models.DateField(auto_now=True, verbose_name="申请时间")
    startday = models.DateField(verbose_name="外出起始日期", default=timezone.now)
    endday = models.DateField(verbose_name="外出结束日期", default=timezone.now)
    statu = models.CharField(
        max_length=10, choices=select_statu, default="unapproved", verbose_name="申请状态")

    def __str__(self):
        return str(self.out_id)


class Leave(models.Model):
    '''请假表'''
    select_statu = (
        ("pass", "通过"),
        ("refuse", "拒绝"),
        ("unapproved", "未批复"),
    )
    leave_type = (
        ("sthday", "事假"),
        ("illday", "病假"),
        ("year", "年休"),
    )
    leave_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(
        'Staff', null=True, verbose_name="员工ID", on_delete=models.CASCADE)
    kind = models.CharField(
        max_length=25, choices=leave_type, default="年休")
    reason = models.TextField(
        max_length=200, verbose_name="请假理由", default='请假理由')
    applytime = models.DateField(auto_now=True, verbose_name="申请时间")
    startday = models.DateField(verbose_name="请假起始日期", default=timezone.now)
    endday = models.DateField(verbose_name="请假结束日期", default=timezone.now)
    statu = models.CharField(
        max_length=10, choices=select_statu, default="unapproved", verbose_name="批复状态")

    def __str__(self):
        return str(self.leave_id)


class Message(models.Model):
    '''个人消息表'''
    message_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(
        'Staff', null=True, verbose_name='员工ID', on_delete=models.CASCADE)
    date = models.DateField(auto_now=True, verbose_name='消息时间')
    title = models.CharField(max_length=20, default='个人消息')
    content = models.TextField(max_length=500, default='个人消息内容')

    def __str__(self):
        return str(self.message_id)


class Punch(models.Model):
    '''打卡表'''
    punch_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(
        'Staff', null=True, verbose_name='员工ID', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True, verbose_name='打卡时间')
    late = models.BooleanField(verbose_name='是否迟到', default=False)

    def __str__(self):
        return str(self.punch_id)
