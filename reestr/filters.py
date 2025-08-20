import django_filters
from django.db.models import Q
from .models import Reestr
from auth_user.models import User

class ReestrFilter(django_filters.FilterSet):
    # Поиск по текстовым полям
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    payer = django_filters.CharFilter(lookup_expr='icontains')
    object_name = django_filters.CharFilter(lookup_expr='icontains')
    object_address = django_filters.CharFilter(lookup_expr='icontains')
    contract_number = django_filters.CharFilter(lookup_expr='icontains')
    bank_name = django_filters.CharFilter(lookup_expr='icontains')
    title_number = django_filters.CharFilter(lookup_expr='icontains')
    is_offsite = django_filters.CharFilter(lookup_expr='icontains')
    iin_bin = django_filters.CharFilter(lookup_expr='icontains')

    # Универсальный фильтр исполнителя: ?executor=Iv -> ищет по username или full_name
    executor = django_filters.CharFilter(method='filter_executor', label='Исполнитель (username или full_name)')

    # Совместимость с запросом ?executor__full_name=... (если фронт посылает именно такое имя параметра)
    executor__full_name = django_filters.CharFilter(field_name='executor__full_name', lookup_expr='icontains', label='Исполнитель (full_name legacy)')

    # По id: ?executor_id=12
    executor_id = django_filters.ModelChoiceFilter(field_name='executor', queryset=User.objects.all(), label='Исполнитель (по id)')

    # Фильтр по департаменту
    department__dep_name = django_filters.CharFilter(field_name='department__dep_name', lookup_expr='icontains')

    # Фильтр по компании (подстрока)
    company = django_filters.CharFilter(lookup_expr='icontains')

    # Фильтрация по дате договора
    contract_start_date = django_filters.DateFilter(field_name='contract_date', lookup_expr='gte')
    contract_end_date = django_filters.DateFilter(field_name='contract_date', lookup_expr='lte')

    class Meta:
        model = Reestr
        fields = [
            'customer_name', 'payer', 'object_name', 'object_address',
            'contract_number', 'bank_name', 'title_number', 'is_offsite',
            'iin_bin', 'executor', 'executor_id', 'executor__full_name', 'department__dep_name',
            'company',
            'contract_start_date', 'contract_end_date'
        ]

    def filter_executor(self, queryset, name, value):
        """
        Ищем по executor.username ИЛИ по executor.full_name (icontains).
        Если хотите, можно расширить на email и т.д.
        """
        if not value:
            return queryset
        return queryset.filter(
            Q(executor__username__icontains=value) |
            Q(executor__full_name__icontains=value)
        )
