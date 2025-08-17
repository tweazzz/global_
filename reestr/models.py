from django.db import models
from auth_user.models import User
from auth_user.models import Department

class Reestr(models.Model):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, db_index=True, verbose_name="Филиал")
    iin_bin = models.CharField(max_length=12, db_index=True, verbose_name="ИИН/БИН")
    customer_name = models.CharField(max_length=255, db_index=True, verbose_name="Наименование заказчика")
    payer = models.CharField(max_length=255, db_index=True, verbose_name="Плательщик")
    object_name = models.CharField(max_length=255, db_index=True, verbose_name="Наименование объекта оценки")
    object_address = models.CharField(max_length=255, db_index=True, verbose_name="Адрес объекта оценки")
    contract_number = models.CharField(max_length=100, db_index=True, verbose_name="№ Договора")
    contract_date = models.DateField(db_index=True, verbose_name="Дата договора")
    contract_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Сумма по договору")
    actual_payment = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Фактическая оплата")
    evaluation_count = models.PositiveIntegerField(verbose_name="Кол-во оценок")
    bank_name = models.CharField(max_length=255, db_index=True, verbose_name="Наименование Банка")
    cost = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Стоимость")
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Площадь кв.м.")
    cost_per_sqm = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Стоимость за кв.м.")
    title_number = models.CharField(max_length=100, db_index=True, verbose_name="Номер титулки")
    is_offsite = models.CharField(max_length=100, db_index=True, verbose_name="Выездной")
    executor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True, verbose_name="Исполнитель")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Дата и время внесения")
    is_paid = models.BooleanField(default=False, db_index=True, verbose_name="Статус оплаты")
    company = models.CharField(max_length=255, null=True, blank=True, db_index=True, verbose_name="Компания")

    class Meta:
        verbose_name_plural = "Реестр"

    # def save(self, *args, **kwargs):
    #     if self.area and self.area > 0:
    #         self.cost_per_sqm = self.cost / self.area
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - {self.contract_number}"
