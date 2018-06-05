from django.contrib import admin
from sites.models import Category, CoolSite


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class CoolSiteAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'created_on']
    list_filter = ['category']


admin.site.register(Category, CategoryAdmin)
admin.site.register(CoolSite, CoolSiteAdmin)
