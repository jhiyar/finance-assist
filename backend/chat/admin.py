from django.contrib import admin
from .models import Profile, Transaction, Balance


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'address', 'created_at', 'updated_at']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'amount_minor', 'created_at']
    list_filter = ['date']
    search_fields = ['description']
    readonly_fields = ['created_at']
    ordering = ['-date']


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ['amount_minor', 'updated_at']
    readonly_fields = ['updated_at']
