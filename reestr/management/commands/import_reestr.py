import pandas as pd
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from reestr.models import Reestr
import os

class Command(BaseCommand):
    help = 'Импорт данных в модель Reestr из Excel-файла'

    def handle(self, *args, **kwargs):
        file_path = '/var/www/globalcapital.kz/global_/reestr/management/commands/Реестр.xlsx'

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден'))
            return

        df = pd.read_excel(file_path, engine='openpyxl')

        for _, row in df.iterrows():
            try:
                Reestr.objects.create(
                    department_id=int(row['Филиал']),
                    iin_bin=str(row['ИИН/БИН'])[:12],  # обрезаем до 12 символов
                    customer_name=row['Наименование заказчика'],
                    payer=row['Плательщик'],
                    object_name=row['Наименование объекта оценки'],
                    object_address=row['Адрес объекта оценки'],
                    contract_number=row['Номер договора'],  # исправлено: раньше было с большой буквы "Д"
                    contract_date=row['Дата договора'],
                    contract_amount=float(row['Сумма по договору']),
                    actual_payment=float(row['Фактическая оплата']) if not pd.isna(row['Фактическая оплата']) else 0.0,
                    evaluation_count=int(row['Количество оценок']) if not pd.isna(row['Количество оценок']) else 0,  # исправлено название колонки
                    bank_name=row['Наименование Банка'],
                    cost=float(row['Стоимость']),
                    area=float(row['Площадь кв.м.']),
                    cost_per_sqm=float(row['Стоимость за кв.м.']) if not pd.isna(row['Стоимость за кв.м.']) else None,  # исправлено: убран двойной пробел
                    title_number=row['Номер титулки'],
                    is_offsite=row['Выездной'],
                    executor_id=int(row['Исполнитель']) if not pd.isna(row['Исполнитель']) else None,
                    is_paid=bool(row['Фактическая оплата']) if not pd.isna(row['Фактическая оплата']) else False  # исправлено поведение
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка при обработке строки: {e}'))

        self.stdout.write(self.style.SUCCESS('Импорт завершён успешно'))
