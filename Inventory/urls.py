
from django.urls import path
from django.conf.urls import url

from .views import *

urlpatterns = [

    path('api/login', login),
    path('api/user', user),
    path('api/resetPassword', resetPassword),
    path('api/forgetPassword', forgetPassword),
    path('api/fetchInventoryTypes', inventory_types),
    path('api/requestInventory', request_inventory),
    path('api/sendEmail', sendEmail),
    path('api/requests', requests),
    path('api/inventory', inventory_Values),
    path('api/gettoken', gettoken, name='api/gettoken'),

]