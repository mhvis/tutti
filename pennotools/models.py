from django.db import models
from datetime import datetime, timedelta

# Create your models here.
class Qrekening(models.Model):
    date = models.DateField(auto_now_add=True)
    due = models.DateField(default=datetime.today() + timedelta(weeks=2))
    qrekening = models.FileField(editable=False)



class DavilexData(models.Model):
    qrekening = models.ForeignKey(Qrekening, on_delete=models.PROTECT)
    type = models.CharField(
        max_length=20,
        choices=(('debtor', 'Debtors'), ('creditor', 'Creditors'))
    )
    file = models.FileField(upload_to='qrekening')
