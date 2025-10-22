from django.contrib import admin
from django.utils.safestring import mark_safe
from django.forms import ModelForm, Textarea
from django.db import models

from yaget.forms import WowmaOrderinfoForm
from .models import (
Friend,
Message,
YaItemList,
YaItemDetail,
YaAmaGoodsDetail,
YaShopAmaGoodsDetail,
YaBuyersItemList,
YaBuyersItemDetail,
WowmaOrderInfo,
WowmaOrderDetail,
)


class WowmaOrderInfoAdmin(admin.ModelAdmin):

    """
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
            attrs={'rows': 1,
                   'cols': 10})},
    }
    """

    form = WowmaOrderinfoForm
    #list_per_page = 50


class YaBuyersItemDetailAdmin(admin.ModelAdmin):

    def icon_image(self, obj):
        return mark_safe('<img src="{}" style="width:100px;height:auto;">'.format(obj.g_img_src_1))

    icon_image.short_description = 'プレビュー'

    list_display = ('gid', 'icon_image', 'wow_gname', 'wow_on_flg', 'wow_price', 'stock', 'wow_gdetail', 'create_date', 'update_date')
    list_filter = ('wow_on_flg', 'stock', 'create_date', 'update_date')
    list_editable = ('wow_gname', 'wow_on_flg', 'wow_price', 'stock', 'wow_gdetail')
    radio_fields = {'wow_on_flg': admin.VERTICAL}
    search_fields = ('gid', 'wow_gname', 'gname', 'gdetail', 'wow_gdetail')
    actions_on_bottom = True
    date_hierarchy = 'create_date'
    list_per_page = 50
    actions = ['change_wow_on_flg_on', 'change_wow_on_flg_off']

    # 追加するアクションの関数
    def change_wow_on_flg_on (self, request, queryset):  # 出品OKに
        queryset.update(wow_on_flg=1)
    def change_wow_on_flg_off (self, request, queryset):  # 出品NGに
        queryset.update(wow_on_flg=0)

    change_wow_on_flg_on.short_description = 'ステータスを出品OKに一括更新'  # アクションの名前
    change_wow_on_flg_off.short_description = 'ステータスを出品NGに一括更新'  # アクションの名前

# Register your models here.
#admin.site.register(Friend)
#admin.site.register(Message)
#admin.site.register(YaItemList)
#admin.site.register(YaItemDetail)
#admin.site.register(YaAmaGoodsDetail)
#admin.site.register(YaShopAmaGoodsDetail)
admin.site.register(YaBuyersItemList)
admin.site.register(YaBuyersItemDetail, YaBuyersItemDetailAdmin)
#admin.site.register(WowmaOrderInfo)
admin.site.register(WowmaOrderInfo, WowmaOrderInfoAdmin)
admin.site.register(WowmaOrderDetail)
