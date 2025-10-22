import re
from datetime import datetime
from django.utils.timezone import now
from django.db import models
from django.core.validators import ValidationError


def alpha_only(value):
    if (re.match(r'^[a-zA-Z]*$', value) == None):
        raise ValidationError(
            'Enter only alphabet!', \
            params={'value': value},
        )

class YaListUrl(models.Model):
    targeturl = models.TextField(max_length=500, default='')
    filename = models.TextField(max_length=30, default='')
    create_date = models.DateTimeField(default=datetime.now)
    update_date = models.DateTimeField()
    db_update_date = models.DateTimeField()

    def __str__(self):
        return '<YaListUrl:id=' + str(self.id) + ', ' + \
               'filename[' + self.filename + '] >'

class YaItemList(models.Model):
    bid = models.TextField(max_length=50, default='')
    blink = models.TextField(max_length=300, default='')
    gid = models.TextField(max_length=50, default='')
    glink = models.TextField(max_length=300, default='')
    g_img_src = models.TextField(max_length=300, default='')
    g_img_alt = models.TextField(max_length=300, default='')
    create_date = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return '<YaItemList:id=' + str(self.id) + ', ' + \
               'bid[' + self.bid + '] gid[' + self.gid + '] >'

class YaItemDetail(models.Model):
    bid = models.TextField(max_length=50, default='')
    blink = models.TextField(max_length=300, default='')
    gid = models.TextField(max_length=50, default='')
    glink = models.TextField(max_length=300, default='')
    gtitle = models.TextField(max_length=300, default='')
    g_n_val = models.TextField(max_length=300, default='')
    g_s_val = models.TextField(max_length=300, default='')
    g_detail = models.TextField(max_length=300, default='')
    g_img_src_1 = models.TextField(max_length=300, default='')
    g_img_src_2 = models.TextField(max_length=300, default='')
    g_img_src_3 = models.TextField(max_length=300, default='')
    g_img_src_4 = models.TextField(max_length=300, default='')
    g_img_src_5 = models.TextField(max_length=300, default='')
    g_img_src_6 = models.TextField(max_length=300, default='')
    g_img_src_7 = models.TextField(max_length=300, default='')
    g_img_src_8 = models.TextField(max_length=300, default='')
    g_img_src_9 = models.TextField(max_length=300, default='')
    g_img_src_10 = models.TextField(max_length=300, default='')
    g_img_src_11 = models.TextField(max_length=300, default='')
    g_img_src_12 = models.TextField(max_length=300, default='')
    g_img_src_13 = models.TextField(max_length=300, default='')
    g_img_src_14 = models.TextField(max_length=300, default='')
    g_img_src_15 = models.TextField(max_length=300, default='')
    g_img_src_16 = models.TextField(max_length=300, default='')
    g_img_src_17 = models.TextField(max_length=300, default='')
    g_img_src_18 = models.TextField(max_length=300, default='')
    g_img_src_19 = models.TextField(max_length=300, default='')
    g_img_src_20 = models.TextField(max_length=300, default='')
    g_img_alt_1 = models.TextField(max_length=300, default='')
    g_img_alt_2 = models.TextField(max_length=300, default='')
    g_img_alt_3 = models.TextField(max_length=300, default='')
    g_img_alt_4 = models.TextField(max_length=300, default='')
    g_img_alt_5 = models.TextField(max_length=300, default='')
    g_img_alt_6 = models.TextField(max_length=300, default='')
    g_img_alt_7 = models.TextField(max_length=300, default='')
    g_img_alt_8 = models.TextField(max_length=300, default='')
    g_img_alt_9 = models.TextField(max_length=300, default='')
    g_img_alt_10 = models.TextField(max_length=300, default='')
    g_img_alt_11 = models.TextField(max_length=300, default='')
    g_img_alt_12 = models.TextField(max_length=300, default='')
    g_img_alt_13 = models.TextField(max_length=300, default='')
    g_img_alt_14 = models.TextField(max_length=300, default='')
    g_img_alt_15 = models.TextField(max_length=300, default='')
    g_img_alt_16 = models.TextField(max_length=300, default='')
    g_img_alt_17 = models.TextField(max_length=300, default='')
    g_img_alt_18 = models.TextField(max_length=300, default='')
    g_img_alt_19 = models.TextField(max_length=300, default='')
    g_img_alt_20 = models.TextField(max_length=300, default='')
    g_det_title_1 = models.TextField(max_length=300, default='')
    g_det_title_2 = models.TextField(max_length=300, default='')
    g_det_title_3 = models.TextField(max_length=300, default='')
    g_det_title_4 = models.TextField(max_length=300, default='')
    g_det_title_5 = models.TextField(max_length=300, default='')
    g_det_title_6 = models.TextField(max_length=300, default='')
    g_det_title_7 = models.TextField(max_length=300, default='')
    g_det_title_8 = models.TextField(max_length=300, default='')
    g_det_title_9 = models.TextField(max_length=300, default='')
    g_det_title_10 = models.TextField(max_length=300, default='')
    g_det_title_11 = models.TextField(max_length=300, default='')
    g_det_title_12 = models.TextField(max_length=300, default='')
    g_det_title_13 = models.TextField(max_length=300, default='')
    g_det_title_14 = models.TextField(max_length=300, default='')
    g_det_title_15 = models.TextField(max_length=300, default='')
    g_det_cont_1 = models.TextField(max_length=2000, default='')
    g_det_cont_2 = models.TextField(max_length=2000, default='')
    g_det_cont_3 = models.TextField(max_length=2000, default='')
    g_det_cont_4 = models.TextField(max_length=2000, default='')
    g_det_cont_5 = models.TextField(max_length=2000, default='')
    g_det_cont_6 = models.TextField(max_length=2000, default='')
    g_det_cont_7 = models.TextField(max_length=2000, default='')
    g_det_cont_8 = models.TextField(max_length=2000, default='')
    g_det_cont_9 = models.TextField(max_length=2000, default='')
    g_det_cont_10 = models.TextField(max_length=2000, default='')
    g_det_cont_11 = models.TextField(max_length=2000, default='')
    g_det_cont_12 = models.TextField(max_length=2000, default='')
    g_det_cont_13 = models.TextField(max_length=2000, default='')
    g_det_cont_14 = models.TextField(max_length=2000, default='')
    g_det_cont_15 = models.TextField(max_length=2000, default='')
    create_date = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return '<YaItemDetail:id=' + str(self.id) + ', ' + \
               'bid[' + self.bid + '] gid[' + self.gid + '] >'

class Friend(models.Model):
    name = models.CharField(max_length=100, \
                            validators=[alpha_only])
    mail = models.EmailField(max_length=200)
    gender = models.BooleanField()
    age = models.IntegerField()
    birthday = models.DateField()

    def __str__(self):
        return '<Friend:id=' + str(self.id) + ', ' + \
               self.name + '(' + str(self.age) + ')>'


class Message(models.Model):
    friend = models.ForeignKey(Friend, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=300)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '<Message:id=' + str(self.id) + ', ' + \
               self.title + '(' + str(self.pub_date) + ')>'

    class Meta:
        ordering = ('pub_date',)


# from django.core.validators import MinValueValidator

# validators=[MinValueValidator(0)]
