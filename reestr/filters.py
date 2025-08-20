import django_filters
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

    # Фильтр по исполнителю:
    # - ?executor=Iv         -> поиск по executor.username (icontains)
    # - ?executor_id=12      -> поиск по PK исполнителя
    executor = django_filters.CharFilter(field_name='executor__username', lookup_expr='icontains', label='Исполнитель (по username)')
    executor_id = django_filters.ModelChoiceFilter(field_name='executor', queryset=User.objects.all(), label='Исполнитель (по id)')

    # Фильтр по департаменту (как было)
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
            'iin_bin', 'executor', 'executor_id', 'department__dep_name',
            'company',
            'contract_start_date', 'contract_end_date'
        ]
