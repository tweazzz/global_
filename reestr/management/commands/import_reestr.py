import os
import pandas as pd
from django.core.management.base import BaseCommand
from reestr.models import Reestr
from django.utils.dateparse import parse_date

class Command(BaseCommand):
    help = 'Импорт данных в модель Reestr из Excel-файла'

    def handle(self, *args, **kwargs):
        file_path = '/var/www/globalcapital.kz/global_/reestr/management/commands/Реестр.xlsx'

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден'))
            return

        # Если у вас .xlsx, лучше явно указывать engine
        df = pd.read_excel(file_path, engine='openpyxl')

        for idx, row in df.iterrows():
            try:
                # --- расчёт actual_payment и is_paid ---
                raw_payment = row.get('Фактическая оплата')
                if pd.isna(raw_payment):
                    actual_payment = 0.0
                    is_paid = False
                else:
                    actual_payment = float(raw_payment)
                    is_paid = actual_payment > 0

                # --- создаём запись ---
                Reestr.objects.create(
                    department_id=int(row['Филиал']),
                    iin_bin=str(row['ИИН/БИН']),
                    customer_name=row['Наименование заказчика'],
                    payer=row['Плательщик'],
                    object_name=row['Наименование объекта оценки'],
                    object_address=row['Адрес объекта оценки'],
                    # название столбца в файле — с маленькой «д»
                    contract_number=row['Номер договора'],
                    # тоже с маленькой «д»
                    contract_date=row['Дата договора'],
                    contract_amount=float(row['Сумма по договору']),
                    actual_payment=actual_payment,
                    # в файле — «Количество оценок»
                    evaluation_count=int(row['Количество оценок']),
                    bank_name=row['Наименование Банка'],
                    cost=float(row['Стоимость']),
                    area=float(row['Площадь кв.м.']),
                    # в файле — «Стоимость за кв.м.» (без двойного пробела)
                    cost_per_sqm=(
                        float(row['Стоимость за кв.м.'])
                        if not pd.isna(row['Стоимость за кв.м.'])
                        else None
                    ),
                    title_number=row['Номер титулки'],
                    is_offsite=row['Выездной'],
                    executor_id=(
                        int(row['Исполнитель'])
                        if not pd.isna(row['Исполнитель'])
                        else None
                    ),
                    is_paid=is_paid,
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка в строке {idx+2}: {e}')
                )

        self.stdout.write(self.style.SUCCESS('Импорт завершён успешно'))
