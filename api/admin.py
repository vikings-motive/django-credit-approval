from django.contrib import admin
from .models import Customer, Loan

# Register models to make them visible in admin interface
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'phone_number', 'monthly_salary', 'approved_limit']
    search_fields = ['first_name', 'last_name', 'phone_number']
    list_filter = ['age']

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'loan_amount', 'interest_rate', 'tenure', 'monthly_repayment', 'start_date', 'end_date']
    search_fields = ['customer__first_name', 'customer__last_name']
    list_filter = ['interest_rate', 'start_date', 'end_date']
