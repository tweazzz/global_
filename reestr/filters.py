import django_filters
from .models import Reestr

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
    executor__username = django_filters.CharFilter(field_name='executor__username', lookup_expr='icontains')
    department__dep_name = django_filters.CharFilter(field_name='department__dep_name', lookup_expr='icontains')

    # Фильтрация по дате договора
    contract_start_date = django_filters.DateFilter(field_name='contract_date', lookup_expr='gte')
    contract_end_date = django_filters.DateFilter(field_name='contract_date', lookup_expr='lte')

    class Meta:
        model = Reestr
        fields = [
            'customer_name', 'payer', 'object_name', 'object_address',
            'contract_number', 'bank_name', 'title_number', 'is_offsite',
            'iin_bin', 'executor__username', 'department__dep_name',
            'contract_start_date', 'contract_end_date'
        ]
