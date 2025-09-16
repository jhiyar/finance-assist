from django.db import models


class Profile(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount_minor = models.IntegerField()  # Amount in minor units (pennies)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.date} - {self.description}"


class Balance(models.Model):
    amount_minor = models.IntegerField(default=0)  # Balance in minor units (pennies)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Balance"
        verbose_name_plural = "Balances"

    def __str__(self):
        return f"Balance: {self.amount_minor} minor units"
