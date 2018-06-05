from django.shortcuts import render
from django.core.cache import cache
from sites.models import Category, CoolSite


def index(request):
    categorys = cache.get('sites_categorys')
    if not categorys:
        category_list = Category.objects.all()
        categorys = []
        for category in category_list:
            sites = {
                'category_name': category.name,
                'category_sites': CoolSite.objects.filter(category=category),
            }
            categorys.append(sites)
        cache.set('sites_categorys', categorys, 120)
    return render(request, 'sites/index.html', {'categorys': categorys})
