from django.shortcuts import render
from django.views import generic
from data.models import Position
from data.models import Driver
from django.db.models import Max

class MenuView(generic.list.ListView):
    # model = Position
    def get_queryset(self):
        queryset = Position.objects.raw('select * '
										+ 'from data_position a '
										+ 'where time = (select max(time) from data_position where taxi_id = a.taxi_id);')
        return queryset

class DriverSelectionView(generic.list.ListView):
    # model = Position
    def get_queryset(self):
        queryset = Driver.objects.exclude(firstname='', lastname='')
        return queryset

class DriverChangeView(generic.TemplateView):
    # model = Position
    template_name = "driver_change.html"
    result = "";
    def get_context_data(self, **kwargs):
        try:
            taxi = self.kwargs['taxi']
            driver_id_old = self.kwargs['driver_id_old']
            driver_id_new = self.kwargs['driver_id_new']
            Position.objects.filter(driver_id=driver_id_old).update(driver_id=driver_id_new)
            self.kwargs["result"] = "OK"
        except:
            self.kwargs["result"] = "Fail"