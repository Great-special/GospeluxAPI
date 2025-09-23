from django.contrib import admin
from .models import Category, Tag, UserFeedBack, ApplicationAPK, AccessModel
from bible.models import Book, Chapter, Verse, BibleVersion, ReadingPlan, ReadingPlanDay, Bookmark 

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

@admin.register(UserFeedBack)
class UserFeedBackAdmin(admin.ModelAdmin):
    list_display = ('email', 'subject', 'created_at')
    search_fields = ('email', 'subject')
    ordering = ('subject',)
    
@admin.register(ApplicationAPK)
class ApplicationAdminAPK(admin.ModelAdmin):
    list_display = ('name', 'version', 'type', 'created_at')
    search_fields = ('name', 'version', 'type')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('version',)







class CustomAdminSite(admin.AdminSite):
    site_header = 'Gospelux Administration'
    site_title = 'Gospelux Admin Portal'
    index_title = 'Welcome to Gospelux Admin'

admin_site = CustomAdminSite(name='custom_admin')
admin_site.register(Category, CategoryAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(UserFeedBack, UserFeedBackAdmin)
admin_site.register(ApplicationAPK, ApplicationAdminAPK)
admin_site.register(Book)
admin_site.register(Chapter)
admin_site.register(Verse)
admin_site.register(BibleVersion)
admin_site.register(ReadingPlan)
admin_site.register(ReadingPlanDay)
admin_site.register(Bookmark)
admin_site.register(AccessModel)
