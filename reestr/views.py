from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.http import HttpResponse
import pandas as pd
from datetime import datetime
from .models import Reestr
from .serializers import ReestrReadSerializer, ReestrWriteSerializer
from .filters import ReestrFilter
from auth_user.permission import CanOnlyAccountantUpdateIsPaid
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from rest_framework.views import APIView
from auth_user.models import User  # если нужно для queryset в фильтрах ранее

class ReestrViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanOnlyAccountantUpdateIsPaid]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReestrFilter
    ordering = ['-created_at']
    ordering_fields = ['created_at', 'contract_amount', 'actual_payment']

    def get_queryset(self):
        user = self.request.user
        qs = Reestr.objects.select_related('department', 'executor').all().order_by('-created_at')
        if getattr(user, 'role', None) == 'employee':
            qs = qs.filter(executor=user)
        return qs

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReestrReadSerializer
        return ReestrWriteSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, 'role', None) == 'employee':
            serializer.save(executor=user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'], url_path='download-excel')
    def download_excel(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = self.get_queryset()

        if start_date:
            queryset = queryset.filter(contract_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(contract_date__lte=end_date)

        COLUMN_MAPPING = {
            'department__dep_name': 'Филиал',
            'iin_bin':              'ИИН/БИН',
            'customer_name':        'Наименование заказчика',
            'payer':                'Плательщик',
            'object_name':          'Наименование объекта оценки',
            'object_address':       'Адрес объекта оценки',
            'contract_number':      '№ Договора',
            'contract_date':        'Дата договора',
            'contract_amount':      'Сумма по договору',
            'payment_date':         'Дата оплаты',            # <-- добавлено
            'actual_payment':       'Фактическая оплата',
            'evaluation_count':     'Кол-во оценок',
            'bank_name':            'Наименование Банка',
            'cost':                 'Стоимость',
            'area':                 'Площадь, кв.м.',
            'cost_per_sqm':         'Стоимость за кв.м.',
            'title_number':         'Номер титулки',
            'is_offsite':           'Выездной',
            'executor__full_name':  'Исполнитель',
            'is_paid':              'Статус оплаты',
            'company':              'Компания',
        }

        # включаем payment_date в values
        data = queryset.values(
            'department__dep_name', 'iin_bin', 'customer_name', 'payer',
            'object_name', 'object_address', 'contract_number', 'contract_date',
            'contract_amount', 'payment_date', 'actual_payment', 'evaluation_count',
            'bank_name', 'cost', 'area', 'cost_per_sqm',
            'title_number', 'is_offsite', 'executor__full_name',
            'is_paid', 'company'
        )

        df = pd.DataFrame(list(data))

        # Переименуем столбцы на русские заголовки
        df.rename(columns=COLUMN_MAPPING, inplace=True)

        # Форматируем колонки с датами в DD.MM.YYYY (если есть)
        if 'Дата договора' in df.columns:
            df['Дата договора'] = pd.to_datetime(df['Дата договора'], errors='coerce').dt.strftime('%d.%m.%Y')
            df['Дата договора'] = df['Дата договора'].fillna('')

        if 'Дата оплаты' in df.columns:
            df['Дата оплаты'] = pd.to_datetime(df['Дата оплаты'], errors='coerce').dt.strftime('%d.%m.%Y')
            df['Дата оплаты'] = df['Дата оплаты'].fillna('')

        # Маппинг статуса оплаты в русские метки
        if 'Статус оплаты' in df.columns:
            df['Статус оплаты'] = df['Статус оплаты'].map({True: 'Оплачено', False: 'Не оплачено'}).fillna('')

        # Опционально: заменить NaN в остальных строках на пустую строку (чтобы в Excel не было NaN)
        df = df.fillna('')

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"Реестр_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename={filename}'

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reestr')

        return response


class ExcelUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'detail': 'Файл не прислан'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        except Exception as e:
            return Response({'detail': f'Не удалось прочитать Excel: {e}'},
                            status=status.HTTP_400_BAD_REQUEST)

        # helper: безопасно брать значение из строки по нескольким возможным заголовкам
        def get_val(row, *names, default=None):
            for n in names:
                if n in row and not pd.isna(row[n]):
                    return row[n]
            return default

        def parse_bool_status(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return False
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return bool(val) and val != 0
            s = str(val).strip().lower()
            if s in ('оплачено', 'paid', 'yes', 'true', '1', 'y', 'да'):
                return True
            if s in ('не оплачено', 'неоплачено', 'not paid', 'no', 'false', '0', 'n', 'нет'):
                return False
            try:
                return float(s) != 0
            except Exception:
                return False

        # helper: парсер даты -> возвращает date или None
        def parse_date(val, dayfirst=False):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            # pandas.Timestamp или datetime.date/datetime
            try:
                if hasattr(val, 'date') and not isinstance(val, str):
                    # Timestamp или datetime
                    return val.date()
            except Exception:
                pass
            # строка/число — пробуем распарсить
            try:
                dt = pd.to_datetime(val, dayfirst=dayfirst, errors='coerce')
                if pd.isna(dt):
                    return None
                return dt.date()
            except Exception:
                return None

        # Проходим по строкам, начиная со строки 2 (Excel)
        for idx, row in enumerate(df.to_dict(orient='records'), start=2):
            try:
                # department: ожидаем id. Если в файле имя — здесь нужно доп.логика.
                department_val = get_val(row, 'Филиал', 'department__dep_name', 'department')
                if department_val is None:
                    raise ValueError("пустое значение")
                department_id = int(department_val)
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'Филиал': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                iin_bin_raw = get_val(row, 'ИИН/БИН', 'iin_bin')
                if iin_bin_raw is None:
                    raise ValueError("пустое значение")
                iin_bin = str(iin_bin_raw).strip()[:12]
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'ИИН/БИН': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # другие поля (с поддержкой нескольких возможных заголовков)
            customer_name = get_val(row, 'Наименование заказчика', 'customer_name', default='')
            payer = get_val(row, 'Плательщик', 'payer', default='')
            object_name = get_val(row, 'Наименование объекта оценки', 'object_name', default='')
            object_address = get_val(row, 'Адрес объекта оценки', 'object_address', default='')

            # contract_number может быть под разными заголовками
            contract_number = get_val(row, '№ Договора', 'Номер договора', 'contract_number', default='')

            # contract_date — pandas может вернуть Timestamp или строку
            contract_date_val = get_val(row, 'Дата договора', 'contract_date')
            contract_date = parse_date(contract_date_val, dayfirst=False)

            try:
                contract_amount_val = get_val(row, 'Сумма по договору', 'contract_amount')
                contract_amount = float(contract_amount_val) if contract_amount_val is not None and not pd.isna(contract_amount_val) else 0.0
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'Сумма по договору': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # actual_payment
            actual_payment_val = get_val(row, 'Фактическая оплата', 'actual_payment')
            actual_payment = float(actual_payment_val) if actual_payment_val is not None and not pd.isna(actual_payment_val) else 0.0

            # evaluation_count — несколько вариантов заголовков
            eval_count_val = get_val(row, 'Количество оценок', 'Кол-во оценок', 'evaluation_count')
            try:
                evaluation_count = int(eval_count_val) if eval_count_val is not None and not pd.isna(eval_count_val) else 0
            except Exception:
                evaluation_count = 0

            bank_name = get_val(row, 'Наименование Банка', 'bank_name', default='')

            try:
                cost_val = get_val(row, 'Стоимость', 'cost')
                cost = float(cost_val) if cost_val is not None and not pd.isna(cost_val) else 0.0
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'Стоимость': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # area might be under "Площадь, кв.м." or "Площадь кв.м."
            try:
                area_val = get_val(row, 'Площадь, кв.м.', 'Площадь кв.м.', 'area')
                area = float(area_val) if area_val is not None and not pd.isna(area_val) else 0.0
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'Площадь кв.м.': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            cost_per_sqm_val = get_val(row, 'Стоимость за кв.м.', 'cost_per_sqm')
            cost_per_sqm = float(cost_per_sqm_val) if cost_per_sqm_val is not None and not pd.isna(cost_per_sqm_val) else None

            title_number = get_val(row, 'Номер титулки', 'title_number', default='')
            is_offsite = get_val(row, 'Выездной', 'is_offsite', default='')

            # Исполнитель: ожидаем id (если хотите поддержку по имени — можно добавить)
            executor_val = get_val(row, 'Исполнитель', 'executor')
            try:
                executor_id = int(executor_val) if executor_val is not None and not pd.isna(executor_val) else None
            except Exception:
                executor_id = None

            # Статус оплаты — читаем из столбца "Статус оплаты" (или "Оплачено")
            status_val = get_val(row, 'Статус оплаты', 'Оплачено', 'is_paid', default=None)
            is_paid = parse_bool_status(status_val)

            # Новое: дата оплаты (поддерживаем несколько названий колонок)
            payment_date_val = get_val(row, 'Дата оплаты', 'payment_date', 'payment')
            payment_date = parse_date(payment_date_val, dayfirst=False)

            # Компания
            company = get_val(row, 'Компания', 'company', default=None)

            # Создаём запись (включая payment_date)
            try:
                Reestr.objects.create(
                    department_id=department_id,
                    iin_bin=iin_bin,
                    customer_name=customer_name,
                    payer=payer,
                    object_name=object_name,
                    object_address=object_address,
                    contract_number=contract_number,
                    contract_date=contract_date,
                    contract_amount=contract_amount,
                    payment_date=payment_date,           # <-- добавлено поле "Дата оплаты"
                    actual_payment=actual_payment,
                    evaluation_count=evaluation_count,
                    bank_name=bank_name,
                    cost=cost,
                    area=area,
                    cost_per_sqm=cost_per_sqm,
                    title_number=title_number,
                    is_offsite=is_offsite,
                    executor_id=executor_id,
                    is_paid=is_paid,
                    company=company
                )
            except Exception as e:
                return Response({'detail': f"Ошибка при создании записи в строке {idx}: {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'Импорт завершён успешно'})