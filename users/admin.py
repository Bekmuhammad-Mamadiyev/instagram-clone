from django.contrib import admin

from users.models import User,UserConfirmation


class UserModelAdmin(admin.ModelAdmin):
    list_display = ['id','username',"email","auth_type"]
admin.site.register(User,UserModelAdmin)
admin.site.register(UserConfirmation)