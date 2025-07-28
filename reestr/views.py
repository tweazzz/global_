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

class ReestrViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanOnlyAccountantUpdateIsPaid]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReestrFilter
    ordering = ['-created_at']
    ordering_fields = ['created_at', 'contract_amount', 'actual_payment']

    def get_queryset(self):
        user = self.request.user
        qs = Reestr.objects.select_related('department', 'executor').all().order_by('-created_at')
        if user.role == 'employee':
            qs = qs.filter(executor=user)
        return qs

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReestrReadSerializer
        return ReestrWriteSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'employee':
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
        }
        data = queryset.values(
            'department__dep_name', 'iin_bin', 'customer_name', 'payer',
            'object_name', 'object_address', 'contract_number', 'contract_date',
            'contract_amount', 'actual_payment', 'evaluation_count',
            'bank_name', 'cost', 'area', 'cost_per_sqm',
            'title_number', 'is_offsite', 'executor__full_name',
            'is_paid'
        )

        df = pd.DataFrame(data)
        df.rename(columns=COLUMN_MAPPING, inplace=True)
        df['Статус оплаты'] = df['Статус оплаты'].map({True: 'Оплачено', False: 'Не оплачено'})
        
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

        # Проходим по строкам, начиная с Excel-номера строки 2 (т.к. 1 — заголовки)
        for idx, row in enumerate(df.to_dict(orient='records'), start=2):
            # Список полей и их преобразований
            try:
                department_id     = int(row['Филиал'])
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'Филиал': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                iin_bin           = str(row['ИИН/БИН'])[:12]
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'ИИН/БИН': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # … повторяем для всех нужных столбцов …

            try:
                contract_amount   = float(row['Сумма по договору'])
            except Exception as e:
                return Response({'detail': f"Ошибка в строке {idx}, столбец 'Сумма по договору': {e}"},
                                status=status.HTTP_400_BAD_REQUEST)

            # Если все поля прошли валидацию — создаём запись
            Reestr.objects.create(
                department_id=department_id,
                iin_bin=iin_bin,
                customer_name=row['Наименование заказчика'],
                payer=row['Плательщик'],
                object_name=row['Наименование объекта оценки'],
                object_address=row['Адрес объекта оценки'],
                contract_number=row['Номер договора'],
                contract_date=row['Дата договора'],
                contract_amount=contract_amount,
                actual_payment=float(row['Фактическая оплата']) if not pd.isna(row['Фактическая оплата']) else 0.0,
                evaluation_count=int(row['Количество оценок']) if not pd.isna(row['Количество оценок']) else 0,
                bank_name=row['Наименование Банка'],
                cost=float(row['Стоимость']),
                area=float(row['Площадь кв.м.']),
                cost_per_sqm=float(row['Стоимость за кв.м.']) if not pd.isna(row['Стоимость за кв.м.']) else None,
                title_number=row['Номер титулки'],
                is_offsite=row['Выездной'],
                executor_id=int(row['Исполнитель']) if not pd.isna(row['Исполнитель']) else None,
                is_paid=bool(row['Фактическая оплата']) if not pd.isna(row['Фактическая оплата']) else False
            )

        return Response({'status': 'Импорт завершён успешно'})