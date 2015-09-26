from django.shortcuts import render
from django.views import generic
from data.models import Position
from django.db.models import Max

class MenuView(generic.list.ListView):
    # model = Position
    def get_queryset(self):
        queryset = Position.objects.raw('select distinct * '
										+ 'from data_position a '
										+ 'where time = (select max(b.time) from data_position b where b.taxi_id = a.taxi_id) '
										+ 'group by taxi_id;')
        return queryset