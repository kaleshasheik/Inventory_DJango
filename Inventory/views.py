from .serializers import UserSerializer, InventorySerializer, RequestInventorySerializer, UserInventorySerializer, UserHierarchySerializer, InventoryValueSerializer, UserRoleSerializer
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from rest_framework.response import Response
from . import models
from django.core.mail import send_mail
from django.contrib.auth.base_user import BaseUserManager
import requests
from django.urls import reverse
from urllib.parse import quote, urlencode
from django.http import HttpResponse, HttpResponseRedirect
from O365 import Message
from O365 import Account
from O365 import oauth_authentication_flow
import imp
import smtplib
from django.core import serializers
import json

@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def user(request):

    if request.method == 'GET':

        users = models.CustomUser.objects.all().values('id', 'name', 'email', 'created_on', 'is_superuser',  'contact_number','employee_id','is_first_login',  'userrole__supervisor_id', 'userrole__is_manager', 'userrole__is_admin').exclude(is_superuser=True)
        managers = models.CustomUser.objects.all().values('name', 'userrole__supervisor_id', 'userrole__is_manager').filter(userrole__is_manager=True )
        user_details = {'users': users, 'managers': managers}
        return Response(user_details, status=status.HTTP_200_OK)

    if request.method == 'POST':
        name = request.data.get('name', None)
        email = request.data.get('email', None)
        supervisor = request.data.get('supervisor_id', None)
        empId = request.data.get('employee_id', None)
        print(request.data)


        userserializer = UserSerializer(data=request.data)
        roleserializer = UserRoleSerializer(data=request.data)
        password = BaseUserManager().make_random_password(20)
        if userserializer.is_valid():
           user = userserializer.save()
           print(password)
           user.set_password(password)

           user.save()

           userid = models.CustomUser.objects.values_list('id', flat=True).filter(
               email=email).get()
           print('sup start')
           print(supervisor)
           print('super end')
           if supervisor and supervisor!='Self':
              supervisorid = models.CustomUser.objects.values_list('employee_id', flat=True).filter(
               name=supervisor).get()
           elif supervisor and supervisor == 'Self':
               supervisorid = empId
           else:
               supervisorid = empId
           print(roleserializer.is_valid())
           if roleserializer.is_valid():
              roleserializer.save(user_id= userid, supervisor_id= supervisorid)
           msgbody = ' <p>Please use below Credentials to login to Inventory Portal </p><p> User name:   ' + '<strong>' + email + '</strong>' + '</p> <p> Password:   ' + '<strong>' + password + '</strong>'+ '</p>'

           emailnotification(email, 'Hello ' + name + ', Your account is activated!', msgbody, None)
           queryset = models.CustomUser.objects.all()
         #  workprofile = models.CustomUser.objects.select_related('UserRole_set')
           print('printinh user data')
           #print(workprofile)
           serializer = UserSerializer(queryset, many=True)
           users = models.CustomUser.objects.all().values('id', 'name', 'email', 'created_on', 'is_superuser',
                                                          'contact_number', 'employee_id', 'is_first_login',
                                                          'userrole__supervisor_id', 'userrole__is_manager',
                                                          'userrole__is_admin').exclude(is_superuser=True)

           managers = models.CustomUser.objects.all().values('name', 'userrole__supervisor_id',
                                                             'userrole__is_manager').filter(userrole__is_manager=True)
           user_details = {'users': users, 'managers': managers}
           return Response(user_details, status=status.HTTP_200_OK)

        else:
            return Response(userserializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':

        email = request.data.get('email', None)
        supervisor = request.data.get('supervisor_id', None)
        employee_id = request.data.get('employee_id', None)
        if email is not None:
            queryset = models.CustomUser.objects.get(email=email)
            userid = models.CustomUser.objects.values_list('id', flat=True).filter(
                email=email).get()
            rolequeryset = models.UserRole.objects.get(user_id=userid)
            print(rolequeryset)
            serializer = UserSerializer(queryset, data=request.data, partial=True)
            roleserializer = UserRoleSerializer(rolequeryset, data=request.data, partial=True)
            print('supervisor', supervisor)
            if supervisor and supervisor!='Self':
               supervisorid = models.CustomUser.objects.values_list('employee_id', flat=True).filter(
                name=supervisor).get()
            else:
                supervisorid = employee_id
            if serializer.is_valid():
                serializer.save()
                print(request.data)
                if roleserializer.is_valid():
                    roleserializer.save(supervisor_id= supervisorid)

            users = models.CustomUser.objects.all().values('id', 'name', 'email', 'created_on', 'is_superuser',
                                                           'contact_number', 'employee_id', 'is_first_login',
                                                           'userrole__supervisor_id', 'userrole__is_manager',
                                                           'userrole__is_admin').exclude(is_superuser=True)

            managers = models.CustomUser.objects.all().values('name', 'userrole__supervisor_id',
                                                              'userrole__is_manager').filter(userrole__is_manager=True)
            user_details = {'users': users, 'managers': managers}
            return Response(user_details, status=status.HTTP_200_OK)

        else:
            return Response('failed to updated user details', status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        email = request.data.get('email', None)
        print(request.data)
        if email is not None:
            models.CustomUser.objects.filter(email=email).delete()
            users = models.CustomUser.objects.all().values('id', 'name', 'email', 'created_on', 'is_superuser',
                                                           'contact_number', 'employee_id', 'is_first_login',
                                                           'userrole__supervisor_id', 'userrole__is_manager',
                                                           'userrole__is_admin').exclude(is_superuser=True)

            managers = models.CustomUser.objects.all().values('name', 'userrole__supervisor_id',
                                                              'userrole__is_manager').filter(userrole__is_manager=True)
            user_details = {'users': users, 'managers': managers}
            return Response(user_details, status=status.HTTP_200_OK)




@api_view(['PUT'])
@permission_classes((AllowAny,))
def resetPassword(request):

    if request.method == 'PUT':
        email = request.data.get('email', None)
        print(email)
        if email is not None:
            queryset = models.CustomUser.objects.get(email=email)
            serializer = UserSerializer(queryset, data=request.data, partial=True)

            if serializer.is_valid():
                user = serializer.save()
                user.set_password(request.data.get("password"))
                user.save()
                Token.objects.filter(user=user).delete()
                token, _ = Token.objects.get_or_create(user=user)
                #queryset = models.CustomUser.objects.filter(email=user)
                results = models.CustomUser.objects.all().values('id', 'name', 'email', 'created_on','contact_number', 'employee_id',
                                                                 'is_first_login', 'userrole__supervisor_id',
                                                                 'userrole__is_manager', 'userrole__is_admin','is_superuser').filter(email=user)
                #serializer = UserSerializer(queryset, many=True)
                user_details = {'user': results, 'token': token.key}
                return Response(user_details,status=HTTP_200_OK)
            else:
                return Response('Failed to update password', status=HTTP_200_OK)

        else:
            return Response('Invalid User', status=HTTP_200_OK)


@api_view(['PUT'])
@permission_classes((AllowAny,))
def forgetPassword(request):

    if request.method == 'PUT':
        email = request.data.get('email', None)
        print(email)
        if email is not None:
            try:
                queryset = models.CustomUser.objects.get(email=email)
            except models.CustomUser.DoesNotExist:
                return Response('Invalid email', status=HTTP_404_NOT_FOUND)


            serializer = UserSerializer(queryset, data=request.data, partial=True)
            password = BaseUserManager().make_random_password(20)
            if serializer.is_valid():
                user = serializer.save()
                user.set_password(password)
                user.save()
                Token.objects.filter(user=user).delete()
                token, _ = Token.objects.get_or_create(user=user)
                #queryset = models.CustomUser.objects.filter(email=user)

                msgbody = ' <p>Please use below Credentials to login to Inventory Portal </p><p> User name:   ' + '<strong>' + email + '</strong>' + '</p> <p> Password:   ' + '<strong>' + password + '</strong>' + '</p>'

                emailnotification(email, 'Hello Your password reset was Successful!', msgbody, None)

                results = models.CustomUser.objects.all().values('id', 'name', 'email', 'created_on','contact_number', 'employee_id',
                                                                 'is_first_login', 'userrole__supervisor_id',
                                                                 'userrole__is_manager', 'userrole__is_admin','is_superuser').filter(email=user)
                #serializer = UserSerializer(queryset, many=True)
                user_details = {'user': results, 'token': token.key}
                return Response(user_details,status=HTTP_200_OK)




@api_view(['GET'])
@permission_classes((AllowAny,))
def inventory_types(request):
    queryset = models.Inventory.objects.all()
    serializer = InventorySerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):

    username = request.data.get("email")
    password = request.data.get("password")

    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},

                        status=HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if not user:
        return Response({'error': 'Invalid Credentials'},

                        status=HTTP_404_NOT_FOUND)

    Token.objects.filter(user=user).delete()

    token, _ = Token.objects.get_or_create(user=user)

    #queryset = models.CustomUser.objects.filter(email=user)
    results = models.CustomUser.objects.all().values('id', 'name', 'email', 'contact_number', 'employee_id',
                                                     'is_first_login', 'userrole__supervisor_id',
                                                     'userrole__is_manager', 'userrole__is_admin','is_superuser').filter(email=user)

    #serializer = UserSerializer(queryset, many=True)

    user_details = {'user': results, 'token': token.key}

    return Response(user_details,

                    status=HTTP_200_OK)


@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def request_inventory(request):

      if request.method == 'GET':
         emp_id = request.query_params.get('employee_id', None)
         is_manager = request.query_params.get('isManager', None)
         supervisor_id = request.query_params.get('supervisor_id', None)
         is_admin = request.query_params.get('isAdmin', None)
         print(is_manager)
         print(emp_id)
         if is_manager == 'false':
            role = 'Employee'
         else:
             role = 'Manager'

         print('entering in get')
         if emp_id is not None:
            print('in get')
            queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='Laptop').filter(status__in=['1', '2', '5'])
            laptopSerializer = RequestInventorySerializer(queryset, many=True)
            queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='DataCard').filter(status__in=['1', '2', '5'])
            datacardSerializer = RequestInventorySerializer(queryset, many=True)

            queryset = models.RequestInventory.objects.filter(status='7')
            approvedRequests = RequestInventorySerializer(queryset, many=True)
            print(role)
            if role =='Employee':
                print('in employee')
                queryset = models.RequestInventory.objects.filter(employee_id=emp_id, status__in=['8', '7','3','4'])
                history = RequestInventorySerializer(queryset, many=True)
                request_details = {'laptopRequest': laptopSerializer.data, 'datacardRequest': datacardSerializer.data,
                                   'history': history.data, 'approved': [],'pending': []}
                return Response(request_details, status=HTTP_200_OK)
            else:
                if role =='Manager':
                   print('in Manager')

                   users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                       supervisor_id=emp_id)

                   l1Queryset = models.RequestInventory.objects.filter(status__in=['8', '7', '3', '4']).filter(
                       employee_id=emp_id)

                   empQueryset = models.RequestInventory.objects.filter(status__in=['8', '7','3','4']).filter(employee_id__in=[users_list_L1])

                   hisqueryset = l1Queryset | empQueryset
                   history = RequestInventorySerializer(hisqueryset, many=True)

                   users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                       supervisor_id=emp_id)

                   users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                       supervisor_id__in=[users_list_L1])

                   queryset_L1 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L1]).filter(
                       status='1')
                   queryset_L2 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L2]).filter(
                       status='1')
                   queryset = queryset_L1 | queryset_L2
                   pendingRequests = RequestInventorySerializer(queryset, many=True)

                   request_details = {'laptopRequest': laptopSerializer.data, 'datacardRequest': datacardSerializer.data , 'history': history.data,
                                      'approved': approvedRequests.data, 'pending': pendingRequests.data}
                   return Response(request_details, status=HTTP_200_OK)

                elif role =='Inventory Manager':
                    queryset = models.RequestInventory.objects.filter(status__in=['8', '7','3','4'])
                    history = RequestInventorySerializer(queryset, many=True)


                    queryset = models.RequestInventory.objects.filter(
                        status__in=['2', '6'])

                    pendingRequests = RequestInventorySerializer(queryset, many=True)

                    request_details = {'laptopRequest': laptopSerializer.data,
                                       'datacardRequest': datacardSerializer.data, 'history': history.data,
                                       'approved': approvedRequests.data, 'pending': pendingRequests.data}
                    return Response(request_details, status=HTTP_200_OK)




      elif request.method == 'POST':
          inv_type = request.data.get("product_type")
          emp_id = request.data.get("employee_id", None)

          is_manager = request.data.get('isManager', None)
          supervisor_id = request.data.get('supervisor_id', None)
          is_admin = request.data.get('isAdmin', None)
          print(is_manager)
          print(emp_id)
          if is_manager == 'false':
              role = 'Employee'
          else:
              role = 'Manager'

          serializer = RequestInventorySerializer(data=request.data)
          print(request.data)
          print(role)
          if serializer.is_valid():
              if inv_type == 'Both':
                  laptopserializer = RequestInventorySerializer(data=request.data)
                  datacardserializer = RequestInventorySerializer(data=request.data)

                  if laptopserializer.is_valid():
                      laptop= laptopserializer.save(product_type='Laptop')
                      req_id = 'REQ_LAP' + str(laptop.id)
                      laptopserializer.save(product_type='Laptop', request_id=req_id, comment='Laptop Request')

                      email = models.CustomUser.objects.values_list('email', flat=True).filter(
                          employee_id=emp_id).get()
                      supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                          employee_id=supervisor_id).get()
                      msgbody = ' <p>Your Laptop Request was submitted Successfully and its Pending with your Manager </p><p> Request No :   ' + '<strong>' + req_id + '</strong>' + '</p> <p> Request Type:   ' + '<strong>' + 'Laptop' + '</strong>' + '</p>'
                      emailnotification(email,
                                        'Hello, Your Laptop Request ' + req_id + ' was submitted Successfully!',
                                        msgbody, supervisoremail)


                  if datacardserializer.is_valid():
                     datacard = datacardserializer.save(product_type='DataCard')
                     req_id = 'REQ_DAT' + str(datacard.id)
                     datacardserializer.save(product_type='DataCard', request_id=req_id, comment='DataCard Request')

                     email = models.CustomUser.objects.values_list('email', flat=True).filter(
                         employee_id=emp_id).get()
                     supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                         employee_id=supervisor_id).get()
                     msgbody = ' <p>Your DataCard Request was submitted Successfully and its Pending with your Manager </p><p> Request No :   ' + '<strong>' + req_id + '</strong>' + '</p> <p> Request Type:   ' + '<strong>' + 'DataCard' + '</strong>' + '</p>'
                     emailnotification(email,
                                       'Hello, Your DataCard Request ' + req_id + ' was submitted Successfully!',
                                       msgbody, supervisoremail)

                  if emp_id is not None:
                      queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='Laptop').filter(
                          status__in=['1', '2', '5'])
                      laptopSerializer = RequestInventorySerializer(queryset, many=True)
                      queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='DataCard').filter(
                          status__in=['1', '2', '5'])
                      datacardSerializer = RequestInventorySerializer(queryset, many=True)

                      queryset = models.RequestInventory.objects.filter(status='7')
                      approvedRequests = RequestInventorySerializer(queryset, many=True)

                      if role == 'Employee':
                          queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                            status__in=['8', '7',
                                                                                        '3',
                                                                                        '4'])
                          history = RequestInventorySerializer(queryset, many=True)
                          request_details = {'laptopRequest': laptopSerializer.data,
                                             'datacardRequest': datacardSerializer.data,
                                             'history': history.data, 'approved': [], 'pending': []}
                          return Response(request_details, status=HTTP_200_OK)
                      else:
                          if role == 'Manager':
                              print('in Manager')
                              users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                  supervisor_id=emp_id)

                              l1Queryset = models.RequestInventory.objects.filter(
                                  status__in=['8', '7', '3', '4']).filter(
                                  employee_id=emp_id)

                              empQueryset = models.RequestInventory.objects.filter(
                                  status__in=['8', '7', '3', '4']).filter(employee_id__in=[users_list_L1])

                              hisqueryset = l1Queryset | empQueryset
                              history = RequestInventorySerializer(hisqueryset, many=True)

                              users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                  supervisor_id=emp_id)

                              users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                  supervisor_id__in=[users_list_L1])

                              queryset_L1 = models.RequestInventory.objects.filter(
                                  employee_id__in=[users_list_L1]).filter(
                                  status='1')
                              queryset_L2 = models.RequestInventory.objects.filter(
                                  employee_id__in=[users_list_L2]).filter(
                                  status='1')
                              queryset = queryset_L1 | queryset_L2
                              pendingRequests = RequestInventorySerializer(queryset, many=True)

                              request_details = {'laptopRequest': laptopSerializer.data,
                                                 'datacardRequest': datacardSerializer.data, 'history': history.data,
                                                 'approved': approvedRequests.data, 'pending': pendingRequests.data}
                              return Response(request_details, status=HTTP_200_OK)

                          elif role == 'Inventory Manager':
                              queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                status__in=['8', '7',
                                                                                            '3',
                                                                                            '4'])
                              history = RequestInventorySerializer(queryset, many=True)

                              queryset = models.RequestInventory.objects.filter(
                                  status__in=['2', '6'])
                              pendingRequests = RequestInventorySerializer(queryset, many=True)

                              request_details = {'laptopRequest': laptopSerializer.data,
                                                 'datacardRequest': datacardSerializer.data, 'history': history.data,
                                                 'approved': approvedRequests.data, 'pending': pendingRequests.data}
                              return Response(request_details, status=HTTP_200_OK)


              else:
                  if inv_type == 'Laptop':
                      laptopserializer = RequestInventorySerializer(data=request.data)
                      if laptopserializer.is_valid():
                         laptop = laptopserializer.save(product_type='Laptop')
                         req_id = 'REQ_LAP' + str(laptop.id)
                         laptopserializer.save(product_type='Laptop', request_id=req_id, comment='Laptop Request')

                         email = models.CustomUser.objects.values_list('email', flat=True).filter(
                             employee_id=emp_id).get()
                         supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                             employee_id=supervisor_id).get()

                         msgbody = ' <p>Your Laptop Request was submitted Successfully and its Pending with your Manager </p><p> Request No :   ' + '<strong>' + req_id + '</strong>' + '</p> <p> Request Type:   ' + '<strong>' + 'Laptop' + '</strong>' + '</p>'
                         emailnotification(email,
                                           'Hello, Your Laptop Request ' + req_id + ' was submitted Successfully!',
                                           msgbody,supervisoremail)

                      if emp_id is not None:
                         queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='Laptop').filter(
                           status__in=['1', '2', '5'])
                         laptopSerializer = RequestInventorySerializer(queryset, many=True)
                         queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='DataCard').filter(
                           status__in=['1', '2', '5'])
                         datacardSerializer = RequestInventorySerializer(queryset, many=True)

                         queryset = models.RequestInventory.objects.filter(status='7')
                         approvedRequests = RequestInventorySerializer(queryset, many=True)

                      if role == 'Employee':
                          queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                            status__in=['8', '7',
                                                                                        '3',
                                                                                        '4'])
                          history = RequestInventorySerializer(queryset, many=True)
                          request_details = {'laptopRequest': laptopSerializer.data,
                                             'datacardRequest': datacardSerializer.data,
                                             'history': history.data, 'approved': [], 'pending': []}
                          return Response(request_details, status=HTTP_200_OK)
                      else:
                          if role == 'Manager':
                              print('in Manager')
                              users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                  supervisor_id=emp_id)

                              l1Queryset = models.RequestInventory.objects.filter(
                                  status__in=['8', '7', '3', '4']).filter(
                                  employee_id=emp_id)

                              empQueryset = models.RequestInventory.objects.filter(
                                  status__in=['8', '7', '3', '4']).filter(employee_id__in=[users_list_L1])

                              hisqueryset = l1Queryset | empQueryset
                              history = RequestInventorySerializer(hisqueryset, many=True)

                              users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                  supervisor_id=emp_id)

                              users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                  supervisor_id__in=[users_list_L1])

                              queryset_L1 = models.RequestInventory.objects.filter(
                                  employee_id__in=[users_list_L1]).filter(
                                  status='1')
                              queryset_L2 = models.RequestInventory.objects.filter(
                                  employee_id__in=[users_list_L2]).filter(
                                  status='1')
                              queryset = queryset_L1 | queryset_L2
                              pendingRequests = RequestInventorySerializer(queryset, many=True)

                              request_details = {'laptopRequest': laptopSerializer.data,
                                                 'datacardRequest': datacardSerializer.data, 'history': history.data,
                                                 'approved': approvedRequests.data, 'pending': pendingRequests.data}
                              return Response(request_details, status=HTTP_200_OK)

                          elif role == 'Inventory Manager':
                              queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                status__in=['8', '7',
                                                                                            '3',
                                                                                            '4'])
                              history = RequestInventorySerializer(queryset, many=True)

                              queryset = models.RequestInventory.objects.filter(
                                  status__in=['2', '6'])
                              pendingRequests = RequestInventorySerializer(queryset, many=True)

                              request_details = {'laptopRequest': laptopSerializer.data,
                                                 'datacardRequest': datacardSerializer.data, 'history': history.data,
                                                 'approved': approvedRequests.data, 'pending': pendingRequests.data}
                              return Response(request_details, status=HTTP_200_OK)



                  elif inv_type == 'DataCard':
                       print('datacard request')
                       datacardserializer = RequestInventorySerializer(data=request.data)
                       if datacardserializer.is_valid():
                          datacard = datacardserializer.save(product_type='DataCard')
                          req_id = 'REQ_DAT' + str(datacard.id)
                          datacardserializer.save(product_type='DataCard', request_id=req_id,
                                                  comment='DataCard Request')

                          email = models.CustomUser.objects.values_list('email', flat=True).filter(
                              employee_id=emp_id).get()
                          supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                              employee_id=supervisor_id).get()

                          msgbody = ' <p>Your DataCard Request was submitted Successfully and its Pending with your Manager </p><p> Request No :   ' + '<strong>' + req_id + '</strong>' + '</p> <p> Request Type:   ' + '<strong>' + 'DataCard' + '</strong>' + '</p>'
                          emailnotification(email,
                                            'Hello, Your DataCard Request ' + req_id + ' was submitted Successfully!',
                                            msgbody, supervisoremail)

                          if emp_id is not None:
                              queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                product_type='Laptop').filter(
                                  status__in=['1', '2', '5'])
                              laptopSerializer = RequestInventorySerializer(queryset, many=True)
                              queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                product_type='DataCard').filter(
                                  status__in=['1', '2', '5'])
                              datacardSerializer = RequestInventorySerializer(queryset, many=True)

                              queryset = models.RequestInventory.objects.filter(status='7')
                              approvedRequests = RequestInventorySerializer(queryset, many=True)

                              if role == 'Employee':
                                  queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                    status__in=['8', '7',
                                                                                                '3',
                                                                                                '4'])
                                  history = RequestInventorySerializer(queryset, many=True)
                                  request_details = {'laptopRequest': laptopSerializer.data,
                                                     'datacardRequest': datacardSerializer.data,
                                                     'history': history.data, 'approved': [], 'pending': []}
                                  return Response(request_details, status=HTTP_200_OK)
                              else:
                                  if role == 'Manager':
                                      print('in Manager')
                                      users_list_L1 = models.UserRole.objects.values_list('employee_id',
                                                                                          flat=True).filter(
                                          supervisor_id=emp_id)

                                      l1Queryset = models.RequestInventory.objects.filter(
                                          status__in=['8', '7', '3', '4']).filter(
                                          employee_id=emp_id)

                                      empQueryset = models.RequestInventory.objects.filter(
                                          status__in=['8', '7', '3', '4']).filter(employee_id__in=[users_list_L1])

                                      hisqueryset = l1Queryset | empQueryset
                                      history = RequestInventorySerializer(hisqueryset, many=True)

                                      users_list_L1 = models.UserRole.objects.values_list('employee_id',
                                                                                          flat=True).filter(
                                          supervisor_id=emp_id)

                                      users_list_L2 = models.UserRole.objects.values_list('employee_id',
                                                                                          flat=True).filter(
                                          supervisor_id__in=[users_list_L1])

                                      queryset_L1 = models.RequestInventory.objects.filter(
                                          employee_id__in=[users_list_L1]).filter(
                                          status='1')
                                      queryset_L2 = models.RequestInventory.objects.filter(
                                          employee_id__in=[users_list_L2]).filter(
                                          status='1')
                                      queryset = queryset_L1 | queryset_L2
                                      pendingRequests = RequestInventorySerializer(queryset, many=True)

                                      request_details = {'laptopRequest': laptopSerializer.data,
                                                         'datacardRequest': datacardSerializer.data,
                                                         'history': history.data,
                                                         'approved': approvedRequests.data,
                                                         'pending': pendingRequests.data}
                                      return Response(request_details, status=HTTP_200_OK)

                                  elif role == 'Inventory Manager':
                                      queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                        status__in=['8', '7',
                                                                                                    '3',
                                                                                                    '4'])
                                      history = RequestInventorySerializer(queryset, many=True)

                                      queryset = models.RequestInventory.objects.filter(
                                          status__in=['2', '6'])
                                      pendingRequests = RequestInventorySerializer(queryset, many=True)

                                      request_details = {'laptopRequest': laptopSerializer.data,
                                                         'datacardRequest': datacardSerializer.data,
                                                         'history': history.data,
                                                         'approved': approvedRequests.data,
                                                         'pending': pendingRequests.data}
                                      return Response(request_details, status=HTTP_200_OK)



                  else:

                       return Response('Invalid Inventory Type', status=HTTP_200_OK)

          else:
              return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

      elif request.method == 'PUT':

           requestId = request.data.get("request_id", None)

           is_manager = request.data.get('isManager', None)
           employee_id = request.data.get('employee_id', None)
           supervisor_id = request.data.get('supervisor_id', None)
           is_admin = request.data.get('isAdmin', None)
           status = request.data.get('status', None)
           email = request.data.get('email', None)
           print(is_manager)

           if is_manager == 'false':
               role = 'Employee'
           else:
               role = 'Manager'

           print(requestId)
           print(role)
           if requestId is not None:
              queryset = models.RequestInventory.objects.get(request_id=requestId)
              print(queryset)
              serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
              print(request.data)

              if serializer.is_valid():
                 serializer.save()
                 message = ''
                 subject =''
                 if status is not None and status == '8':
                     message = 'User has cancelled the request'
                     subject = 'Cancelled Successfully!'
                 elif status is not None and status == '6':
                     message = 'Request pending with admin'
                     subject = 'sent to Admin for Approval'

                 supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                            employee_id=supervisor_id).get()

                 msgbody = ' <p>' + message + '</p><p> Request No :   ' + '<strong>' + requestId + '</strong>'
                 emailnotification(email,
                                   'Hello, Request ' + requestId + ' was ' + subject,
                                   msgbody, supervisoremail)

                 print(serializer.data)
                 emp_id = request.data.get('employee_id', None)
                 print(emp_id)

                 queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='Laptop').filter(
                     status__in=['1', '2', '5'])
                 laptopSerializer = RequestInventorySerializer(queryset, many=True)
                 queryset = models.RequestInventory.objects.filter(employee_id=emp_id, product_type='DataCard').filter(
                     status__in=['1', '2', '5'])
                 datacardSerializer = RequestInventorySerializer(queryset, many=True)

                 queryset = models.RequestInventory.objects.filter(status='7')
                 approvedRequests = RequestInventorySerializer(queryset, many=True)

                 if role == 'Employee':
                     queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                       status__in=['8', '7',
                                                                                   '3',
                                                                                   '4'])
                     history = RequestInventorySerializer(queryset, many=True)
                     request_details = {'laptopRequest': laptopSerializer.data,
                                        'datacardRequest': datacardSerializer.data,
                                        'history': history.data, 'approved': [], 'pending': []}
                     return Response(request_details, status=HTTP_200_OK)
                 else:
                     if role == 'Manager':
                         print('in Manager')
                         users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                             supervisor_id=emp_id)

                         l1Queryset = models.RequestInventory.objects.filter(status__in=['8', '7', '3', '4']).filter(
                             employee_id=emp_id)

                         empQueryset = models.RequestInventory.objects.filter(status__in=['8', '7', '3', '4']).filter(
                             employee_id__in=[users_list_L1])

                         hisqueryset = l1Queryset | empQueryset
                         history = RequestInventorySerializer(hisqueryset, many=True)

                         users_list_L1 = models.UserRole.objects.values_list('employee_id',
                                                                             flat=True).filter(
                             supervisor_id=emp_id)

                         users_list_L2 = models.UserRole.objects.values_list('employee_id',
                                                                             flat=True).filter(
                             supervisor_id__in=[users_list_L1])

                         queryset_L1 = models.RequestInventory.objects.filter(
                             employee_id__in=[users_list_L1]).filter(
                             status='1')
                         queryset_L2 = models.RequestInventory.objects.filter(
                             employee_id__in=[users_list_L2]).filter(
                             status='1')
                         queryset = queryset_L1 | queryset_L2
                         pendingRequests = RequestInventorySerializer(queryset, many=True)

                         request_details = {'laptopRequest': laptopSerializer.data,
                                            'datacardRequest': datacardSerializer.data,
                                            'history': history.data,
                                            'approved': approvedRequests.data,
                                            'pending': pendingRequests.data}
                         return Response(request_details, status=HTTP_200_OK)

                     elif role == 'Inventory Manager':
                         queryset = models.RequestInventory.objects.filter(status__in=['8', '7', '3', '4'])
                         history = RequestInventorySerializer(queryset, many=True)

                         queryset = models.RequestInventory.objects.filter(
                             status__in=['2', '6'])
                         pendingRequests = RequestInventorySerializer(queryset, many=True)

                         request_details = {'laptopRequest': laptopSerializer.data,
                                            'datacardRequest': datacardSerializer.data, 'history': history.data,
                                            'approved': approvedRequests.data, 'pending': pendingRequests.data}
                         return Response(request_details, status=HTTP_200_OK)

              else:
                 return Response(
                  serializer.errors, status=HTTP_400_BAD_REQUEST)
           else:
               return Response(
                   "Invalid Request", status=HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def inventory_Values(request):

    if request.method == 'GET':
        iStatus = request.query_params.get('status', None)
        if iStatus is not None:
           queryset = models.InventoryValues.objects.filter(status= iStatus, product_type_id= 1)


           lapserializer = InventoryValueSerializer(queryset, many=True)

           queryset = models.InventoryValues.objects.filter(status=iStatus, product_type_id= 2)
           dataserializer = InventoryValueSerializer(queryset, many=True)
           request_details = {'laptopDetails': lapserializer.data,
                              'datacardDetails': dataserializer.data}
           return Response(request_details, status=HTTP_200_OK)

        else:
            inv_details = models.InventoryValues.objects.all().values('id', 'product_type_id', 'model', 'serial_no',
                                                                      'sim_no',
                                                                      'status', 'manufacturer', 'configuration',
                                                                      'purchase_dt', 'creation_dt',
                                                                      'userinventory__employee_id',
                                                                      )

            print('inv_details in else', inv_details)
            queryset = models.InventoryValues.objects.all()
            serializer = InventoryValueSerializer(queryset, many=True)
            return Response(inv_details, status=HTTP_200_OK)

    if request.method == 'POST':
        print('new inventory details',request.data)
        serial_no = request.data.get("serial_no", None)
        print('serial_no',serial_no)
        serializer = InventoryValueSerializer(data=request.data)
        userInventoryserializer = UserInventorySerializer(data=request.data, partial=True)
        print('serializer.is_valid()', serializer.is_valid())
        if serializer.is_valid():
            serializer.save()

            product_id = models.InventoryValues.objects.values_list('id', flat=True).filter(
                serial_no=serial_no).get()
            print('product_id', product_id)
            print('userInventoryserializer.is_valid()', userInventoryserializer.is_valid())
        if userInventoryserializer.is_valid():
            userInventoryserializer.save(product_id= product_id)

            queryset = models.InventoryValues.objects.all()
            serializer = InventoryValueSerializer(queryset, many=True)
            print('new inv', serializer.data)
            return Response(serializer.data, status=HTTP_200_OK)

        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':

        serial_no = request.data.get('serial_no', None)
        old_serial_no = request.data.get('old_serial_no', None)
        print('put inventory' , request.data)
        print(old_serial_no)
        if old_serial_no is not None:
            queryset = models.InventoryValues.objects.get(serial_no= old_serial_no)
            serializer = InventoryValueSerializer(queryset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                queryset = models.InventoryValues.objects.all()
                serializer = InventoryValueSerializer(queryset, many=True)
                return Response(serializer.data, status=HTTP_200_OK)

        else:
            return Response('failed to updated Inventory details', status=HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        serial_no = request.data.get('serial_no', None)
        print(request.data)
        if serial_no is not None:
            models.InventoryValues.objects.filter(serial_no=serial_no).delete()
            queryset = models.InventoryValues.objects.all()
            serializer = InventoryValueSerializer(queryset, many=True)
            return Response(serializer.data, status=HTTP_200_OK)



@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def requests(request):

    if request.method == 'GET':
        emp_id = request.query_params.get('employee_id', None)

        is_manager = request.query_params.get('isManager', None)
        supervisor_id = request.query_params.get('supervisor_id', None)
        is_admin = request.query_params.get('isAdmin', None)
        print(is_manager)

        if is_manager == 'false':
            role = 'Employee'
        else:
            role = 'Manager'

        if emp_id is not None:

            # user = models.CustomUser.objects.filter(employee_id__in=[24415, 112424])

            #role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
            print(role)
            if is_manager == 'true' and is_admin == 'false':
                print('in manager')
                users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                    supervisor_id=emp_id)

                users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                    supervisor_id__in=[users_list_L1])

                lapqueryset_L1 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L1]).filter(
                    status='1', product_type='Laptop')

                lapqueryset_L2 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L2]).filter(
                    status='1',product_type='Laptop')

                dataqueryset_L1 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L1]).filter(
                    status='1',product_type='DataCard')

                dataqueryset_L2 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L2]).filter(
                    status='1', product_type='DataCard')



                lapqueryset =  lapqueryset_L1 | lapqueryset_L2
                dataqueryset = dataqueryset_L1 | dataqueryset_L2

                lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                request_details = {'laptopRequest': lapserializer.data,
                                   'datacardRequest': dataserializer.data}

                return Response({'requests': request_details}, status=HTTP_200_OK)

            elif is_manager == 'true' and is_admin == 'true':
                print('manager and admin')
                users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                    supervisor_id=emp_id)

                users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                    supervisor_id__in=[users_list_L1])

                lapqueryset_L1 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L1]).filter(
                    status='1',product_type='Laptop')

                lapqueryset_L2 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L2]).filter(
                    status='1', product_type='Laptop')

                dataqueryset_L1 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L1]).filter(
                    status='1', product_type='DataCard')

                dataqueryset_L2 = models.RequestInventory.objects.filter(employee_id__in=[users_list_L2]).filter(
                    status='1', product_type='DataCard')

                lapqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],product_type='Laptop')

                dataqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],product_type='DataCard')

                lapqueryset = lapqueryset_L1 | lapqueryset_L2 | lapqueryset_admin
                dataqueryset = dataqueryset_L1 | dataqueryset_L2 | dataqueryset_admin

                lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                request_details = {'laptopRequest': lapserializer.data,
                                   'datacardRequest': dataserializer.data}

                return Response({'requests': request_details}, status=HTTP_200_OK)


            elif is_admin == 'true':
               print('is_admin')
               lapqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],product_type='Laptop')

               dataqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],product_type='DataCard')

               lapserializer = RequestInventorySerializer(lapqueryset, many=True)
               dataserializer = RequestInventorySerializer(dataqueryset, many=True)
               request_details = {'laptopRequest': lapserializer.data,
                                  'datacardRequest': dataserializer.data}

               return Response({'requests': request_details}, status=HTTP_200_OK)
            else:
                print('retrurning empty')
                return Response([], status=HTTP_200_OK)

    elif request.method == 'PUT':
         print('request data', request.data)
         requestId = request.data.get("request_id", None)

         emp_id = request.data.get("emp_id", None)
         invValue = request.data.get("invValue", None)
         invType = request.data.get("invType", None)
         iStatus = request.data.get("status", None)
         is_manager = request.data.get('isManager', None)
         is_admin = request.data.get('isAdmin', None)
         assigned_To = request.data.get('assignedTo', None)

         print(emp_id)

         queryset = models.InventoryValues.objects.filter(status='Available', product_type_id=1)
         lapserializer = InventoryValueSerializer(queryset, many=True)

         queryset = models.InventoryValues.objects.filter(status='Available', product_type_id=2)
         dataserializer = InventoryValueSerializer(queryset, many=True)
         available_inv = {'laptopDetails': lapserializer.data,
                          'datacardDetails': dataserializer.data}

         if requestId is not None:
            queryset = models.RequestInventory.objects.get(request_id=requestId)
            #role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)

            role = ''   # role is not required. Remove the unnecessary code

           # L2_User = models.UserRole.objects.values_list('supervisor_id', flat=True).filter(
                #employee_id=emp_id)

            print(queryset)

            print(iStatus)


            if iStatus == '5':
                    print('Assigning the inventory')
                    print('in ', request.data)
                    user = models.RequestInventory.objects.values_list('employee_id', flat=True).filter(
                        request_id=requestId).first()
                    print(user)
                    if invType == 'Laptop':
                       serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                       if serializer.is_valid():
                          serializer.save(laptopNO=invValue)
                          print('Assigned laptop inventory')
                          queryset = models.InventoryValues.objects.filter(serial_no=invValue, product_type_id=1 ,status='Available').first()
                          print(queryset)

                          lapserializer = InventoryValueSerializer(queryset, data=request.data, partial=True)
                          print(lapserializer.is_valid())
                          if lapserializer.is_valid():
                             lapserializer.save(status='Assigned')

                             product_id = models.InventoryValues.objects.values_list('id', flat=True).filter(
                                 serial_no=invValue).get()
                             user_inv = models.UserInventory.objects.get(product_id =product_id)
                             print(user_inv)
                             userInventoryserializer = UserInventorySerializer(user_inv, data=request.data, partial=True)
                             if userInventoryserializer.is_valid():
                                 userInventoryserializer.save(employee_id=assigned_To)

                                 useremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                     employee_id=assigned_To).get()

                                 supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                     employee_id=emp_id).get()

                                 msgbody = '<p> Your Request was Approved by Admin </p> <br/>' + ' <p> Below are the Inventory details: </p><p> Laptop serial No:   ' + '<strong>' + invValue +'</strong>' + '</p>'

                                 emailnotification(useremail,
                                                   'Hello, Your Laptop Request ' + requestId + ' was approved!',
                                                   msgbody, supervisoremail)


                             if is_manager == 'true' and is_admin == 'false':
                                 print('manager')
                                 users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id=emp_id)

                                 users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id__in=[users_list_L1])

                                 lapqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='Laptop')

                                 lapqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='Laptop')

                                 dataqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='DataCard')

                                 dataqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='DataCard')

                                 lapqueryset = lapqueryset_L1 | lapqueryset_L2
                                 dataqueryset = dataqueryset_L1 | dataqueryset_L2

                                 lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                 dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                 request_details = {'laptopRequest': lapserializer.data,
                                                    'datacardRequest': dataserializer.data}

                                 return Response({'requests': request_details}, status=HTTP_200_OK)

                             elif is_manager == 'true' and is_admin == 'true':
                                 print('manager')
                                 users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id=emp_id)

                                 users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id__in=[users_list_L1])

                                 lapqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='Laptop')

                                 lapqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='Laptop')

                                 dataqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='DataCard')

                                 dataqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='DataCard')

                                 lapqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                            product_type='Laptop')

                                 dataqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                             product_type='DataCard')

                                 lapqueryset = lapqueryset_L1 | lapqueryset_L2 | lapqueryset_admin
                                 dataqueryset = dataqueryset_L1 | dataqueryset_L2 | dataqueryset_admin

                                 lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                 dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                 request_details = {'laptopRequest': lapserializer.data,
                                                    'datacardRequest': dataserializer.data}

                                 return Response({'requests': request_details}, status=HTTP_200_OK)


                             elif is_admin == 'true':

                                 lapqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                      product_type='Laptop')

                                 dataqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                       product_type='DataCard')

                                 lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                 dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                 request_details = {'laptopRequest': lapserializer.data,
                                                    'datacardRequest': dataserializer.data}

                                 return Response({'requests': request_details}, status=HTTP_200_OK)

                          else:
                              return Response(
                                  serializer.errors, status=HTTP_400_BAD_REQUEST)
                    elif invType == 'DataCard':
                        serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                        if serializer.is_valid():
                            serializer.save(dataCardNO=invValue)
                            print('Assigned datacard inventory')
                            queryset = models.InventoryValues.objects.filter(sim_no=invValue, product_type_id=2 ,status='Available').first()
                            print(queryset)
                            dataserializer = InventoryValueSerializer(queryset, data=request.data, partial=True)
                            print(dataserializer.is_valid())
                            if dataserializer.is_valid():
                                dataserializer.save(status='Assigned')

                                product_id = models.InventoryValues.objects.values_list('id', flat=True).filter(
                                    sim_no=invValue).get()
                                user_inv = models.UserInventory.objects.get(product_id=product_id)
                                print(user_inv)
                                userInventoryserializer = UserInventorySerializer(user_inv, data=request.data,
                                                                                  partial=True)
                                if userInventoryserializer.is_valid():
                                    userInventoryserializer.save(employee_id=assigned_To)

                                    useremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                        employee_id=assigned_To).get()

                                    supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                        employee_id=emp_id).get()

                                    msgbody = '<p> Your Request was Approved by Admin </p> <br/>' + ' <p>Below are the Inventory details: </p><p> DataCard serial No:   ' + '<strong>' + invValue + '</strong>' + '</p>'

                                    emailnotification(useremail,
                                                      'Hello, Your DataCard Request ' + requestId + ' was approved!',
                                                      msgbody, supervisoremail)

                                if is_manager == 'true' and is_admin == 'false':
                                    print('manager')
                                    users_list_L1 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id=emp_id)

                                    users_list_L2 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id__in=[users_list_L1])

                                    lapqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='Laptop')

                                    lapqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='Laptop')

                                    dataqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='DataCard')

                                    dataqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='DataCard')

                                    lapqueryset = lapqueryset_L1 | lapqueryset_L2
                                    dataqueryset = dataqueryset_L1 | dataqueryset_L2

                                    lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                    dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                    request_details = {'laptopRequest': lapserializer.data,
                                                       'datacardRequest': dataserializer.data}

                                    return Response({'requests': request_details}, status=HTTP_200_OK)

                                elif is_manager == 'true' and is_admin == 'true':
                                    print('manager')
                                    users_list_L1 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id=emp_id)

                                    users_list_L2 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id__in=[users_list_L1])

                                    lapqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='Laptop')

                                    lapqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='Laptop')

                                    dataqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='DataCard')

                                    dataqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='DataCard')

                                    lapqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                               product_type='Laptop')

                                    dataqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                                product_type='DataCard')

                                    lapqueryset = lapqueryset_L1 | lapqueryset_L2 | lapqueryset_admin
                                    dataqueryset = dataqueryset_L1 | dataqueryset_L2 | dataqueryset_admin

                                    lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                    dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                    request_details = {'laptopRequest': lapserializer.data,
                                                       'datacardRequest': dataserializer.data}

                                    return Response({'requests': request_details}, status=HTTP_200_OK)


                                elif is_admin == 'true':

                                    lapqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                         product_type='Laptop')

                                    dataqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                          product_type='DataCard')

                                    lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                    dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                    request_details = {'laptopRequest': lapserializer.data,
                                                       'datacardRequest': dataserializer.data}

                                    return Response({'requests': request_details}, status=HTTP_200_OK)

                            else:
                                return Response(
                                    serializer.errors, status=HTTP_400_BAD_REQUEST)
                        else:
                            return Response(
                                serializer.errors, status=HTTP_400_BAD_REQUEST)

            elif iStatus == '7':
                    print('Releasing the inventory')
                    print('in ', request.data)
                    user = models.RequestInventory.objects.values_list('employee_id', flat=True).filter(
                        request_id=requestId).first()
                    if invType == 'Laptop':
                       serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                       if serializer.is_valid():
                          serializer.save()
                          print('Releasing laptop inventory')
                          queryset = models.InventoryValues.objects.filter(serial_no=invValue,product_type_id=1 ,status='Assigned').first()
                          print(queryset)
                          lapserializer = InventoryValueSerializer(queryset,  data=request.data, partial=True)
                          if lapserializer.is_valid():
                             lapserializer.save(status='Available')

                             product_id = models.InventoryValues.objects.values_list('id', flat=True).filter(
                                 serial_no=invValue).get()
                             user_inv = models.UserInventory.objects.get(product_id=product_id)
                             print(user_inv)
                             userInventoryserializer = UserInventorySerializer(user_inv, data=request.data,
                                                                               partial=True)
                             if userInventoryserializer.is_valid():
                                 userInventoryserializer.save(employee_id='')

                                 useremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                     employee_id=assigned_To).get()

                                 supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                     employee_id=emp_id).get()

                                 msgbody = '<p> Your Request was Closed by Admin </p> <br/>' + ' <p>Below are the Inventory details: </p><p> Laptop serial No:   ' + '<strong>' + invValue + '</strong>' + '</p>'

                                 emailnotification(useremail,
                                                   'Hello, Your Laptop Request ' + requestId + ' was Closed!',
                                                   msgbody, supervisoremail)


                             if is_manager == 'true' and is_admin == 'false':
                                 print('manager')
                                 users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id=emp_id)

                                 users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id__in=[users_list_L1])

                                 lapqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='Laptop')

                                 lapqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='Laptop')

                                 dataqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='DataCard')

                                 dataqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='DataCard')

                                 lapqueryset = lapqueryset_L1 | lapqueryset_L2
                                 dataqueryset = dataqueryset_L1 | dataqueryset_L2

                                 lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                 dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                 request_details = {'laptopRequest': lapserializer.data,
                                                    'datacardRequest': dataserializer.data}

                                 return Response({'requests': request_details}, status=HTTP_200_OK)

                             elif is_manager == 'true' and is_admin == 'true':
                                 print('manager')
                                 users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id=emp_id)

                                 users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                                     supervisor_id__in=[users_list_L1])

                                 lapqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='Laptop')

                                 lapqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='Laptop')

                                 dataqueryset_L1 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L1]).filter(
                                     status='1', product_type='DataCard')

                                 dataqueryset_L2 = models.RequestInventory.objects.filter(
                                     employee_id__in=[users_list_L2]).filter(
                                     status='1', product_type='DataCard')

                                 lapqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                            product_type='Laptop')

                                 dataqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                             product_type='DataCard')

                                 lapqueryset = lapqueryset_L1 | lapqueryset_L2 | lapqueryset_admin
                                 dataqueryset = dataqueryset_L1 | dataqueryset_L2 | dataqueryset_admin

                                 lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                 dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                 request_details = {'laptopRequest': lapserializer.data,
                                                    'datacardRequest': dataserializer.data}

                                 return Response({'requests': request_details}, status=HTTP_200_OK)


                             elif is_admin == 'true':

                                 lapqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                      product_type='Laptop')

                                 dataqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                       product_type='DataCard')

                                 lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                 dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                 request_details = {'laptopRequest': lapserializer.data,
                                                    'datacardRequest': dataserializer.data}

                                 return Response({'requests': request_details}, status=HTTP_200_OK)

                          else:
                              return Response(
                                  serializer.errors, status=HTTP_400_BAD_REQUEST)
                    elif invType == 'DataCard':
                        serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            print('Assigned datacard inventory')
                            queryset = models.InventoryValues.objects.filter(sim_no=invValue,product_type_id=2 ,status='Assigned').first()
                            print(queryset)
                            dataserializer = InventoryValueSerializer(queryset, data=request.data, partial=True)
                            if dataserializer.is_valid():
                                dataserializer.save(status='Available')

                                product_id = models.InventoryValues.objects.values_list('id', flat=True).filter(
                                    sim_no=invValue).get()
                                user_inv = models.UserInventory.objects.get(product_id=product_id)
                                print(user_inv)
                                userInventoryserializer = UserInventorySerializer(user_inv, data=request.data,
                                                                                  partial=True)
                                if userInventoryserializer.is_valid():
                                    userInventoryserializer.save(employee_id='')

                                    useremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                        employee_id=assigned_To).get()

                                    supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                                        employee_id=emp_id).get()

                                    msgbody = '<p> Your Request was Closed by Admin </p> <br/>' + ' <p>Below are the Inventory details: </p><p> DataCard serial No:   ' + '<strong>' + invValue + '</strong>' + '</p>'

                                    emailnotification(useremail,
                                                      'Hello, Your DataCard Request ' + requestId + ' was Closed!',
                                                      msgbody, supervisoremail)


                                if is_manager == 'true' and is_admin == 'false':
                                    print('manager')
                                    users_list_L1 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id=emp_id)

                                    users_list_L2 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id__in=[users_list_L1])

                                    lapqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='Laptop')

                                    lapqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='Laptop')

                                    dataqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='DataCard')

                                    dataqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='DataCard')

                                    lapqueryset = lapqueryset_L1 | lapqueryset_L2
                                    dataqueryset = dataqueryset_L1 | dataqueryset_L2

                                    lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                    dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                    request_details = {'laptopRequest': lapserializer.data,
                                                       'datacardRequest': dataserializer.data}

                                    return Response({'requests': request_details}, status=HTTP_200_OK)

                                elif is_manager == 'true' and is_admin == 'true':
                                    print('manager')
                                    users_list_L1 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id=emp_id)

                                    users_list_L2 = models.UserRole.objects.values_list('employee_id',
                                                                                        flat=True).filter(
                                        supervisor_id__in=[users_list_L1])

                                    lapqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='Laptop')

                                    lapqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='Laptop')

                                    dataqueryset_L1 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L1]).filter(
                                        status='1', product_type='DataCard')

                                    dataqueryset_L2 = models.RequestInventory.objects.filter(
                                        employee_id__in=[users_list_L2]).filter(
                                        status='1', product_type='DataCard')

                                    lapqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                               product_type='Laptop')

                                    dataqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                                product_type='DataCard')

                                    lapqueryset = lapqueryset_L1 | lapqueryset_L2 | lapqueryset_admin
                                    dataqueryset = dataqueryset_L1 | dataqueryset_L2 | dataqueryset_admin

                                    lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                    dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                    request_details = {'laptopRequest': lapserializer.data,
                                                       'datacardRequest': dataserializer.data}

                                    return Response({'requests': request_details}, status=HTTP_200_OK)


                                elif is_admin == 'true':

                                    lapqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                         product_type='Laptop')

                                    dataqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                          product_type='DataCard')

                                    lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                                    dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                                    request_details = {'laptopRequest': lapserializer.data,
                                                       'datacardRequest': dataserializer.data}

                                    return Response({'requests': request_details}, status=HTTP_200_OK)

                            else:
                                return Response(
                                    serializer.errors, status=HTTP_400_BAD_REQUEST)
                        else:
                            return Response(
                                serializer.errors, status=HTTP_400_BAD_REQUEST)

            else:
                print('in else', request.data)
                serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                if serializer.is_valid():
                   serializer.save()

                   useremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                       employee_id=assigned_To).get()

                   supervisoremail = models.CustomUser.objects.values_list('email', flat=True).filter(
                       employee_id=emp_id).get()

                   subject = ''
                   message = ''
                   if iStatus is not None and iStatus == '3':
                       message = 'Your request was Rejected by L1'
                       subject = 'Rejected by L1!'
                   elif iStatus is not None and iStatus == '4':
                       message = 'Your request was Rejected by Admin'
                       subject = 'Rejected by Admin!'
                   elif iStatus is not None and iStatus == '2':
                       message = 'Your request was Approved by L1 and Pending with Admin'
                       subject = 'Approved by L1 and Pending with Admin!'

                   msgbody = ' <p>' + message + '</p><p> Request No :   ' + '<strong>' + requestId + '</strong>'
                   emailnotification(useremail,
                                     'Hello, Request ' + requestId + ' was ' + subject,
                                     msgbody, supervisoremail)


                   if is_manager == 'true' and is_admin == 'false':
                       print('manager',emp_id )
                       users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                           supervisor_id=emp_id)

                       users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                           supervisor_id__in=[users_list_L1])

                       lapqueryset_L1 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L1]).filter(
                           status='1', product_type='Laptop')

                       lapqueryset_L2 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L2]).filter(
                           status='1', product_type='Laptop')

                       dataqueryset_L1 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L1]).filter(
                           status='1', product_type='DataCard')

                       dataqueryset_L2 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L2]).filter(
                           status='1', product_type='DataCard')

                       lapqueryset = lapqueryset_L1 | lapqueryset_L2
                       dataqueryset = dataqueryset_L1 | dataqueryset_L2

                       lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                       dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                       request_details = {'laptopRequest': lapserializer.data,
                                          'datacardRequest': dataserializer.data}

                       return Response({'requests': request_details}, status=HTTP_200_OK)

                   if is_manager == 'true' and is_admin == 'true':
                       print('manager and admin', emp_id)
                       users_list_L1 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                           supervisor_id=emp_id)

                       users_list_L2 = models.UserRole.objects.values_list('employee_id', flat=True).filter(
                           supervisor_id__in=[users_list_L1])

                       lapqueryset_L1 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L1]).filter(
                           status='1', product_type='Laptop')

                       lapqueryset_L2 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L2]).filter(
                           status='1', product_type='Laptop')

                       dataqueryset_L1 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L1]).filter(
                           status='1', product_type='DataCard')

                       dataqueryset_L2 = models.RequestInventory.objects.filter(
                           employee_id__in=[users_list_L2]).filter(
                           status='1', product_type='DataCard')

                       lapqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                  product_type='Laptop')

                       dataqueryset_admin = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                                   product_type='DataCard')

                       lapqueryset = lapqueryset_L1 | lapqueryset_L2 | lapqueryset_admin
                       dataqueryset = dataqueryset_L1 | dataqueryset_L2 | dataqueryset_admin

                       lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                       dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                       request_details = {'laptopRequest': lapserializer.data,
                                          'datacardRequest': dataserializer.data}

                       return Response({'requests': request_details}, status=HTTP_200_OK)

                   elif is_admin == 'true':
                       print('admin', emp_id)
                       lapqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                            product_type='Laptop')

                       dataqueryset = models.RequestInventory.objects.filter(status__in=[2, 6],
                                                                             product_type='DataCard')

                       lapserializer = RequestInventorySerializer(lapqueryset, many=True)
                       dataserializer = RequestInventorySerializer(dataqueryset, many=True)
                       request_details = {'laptopRequest': lapserializer.data,
                                          'datacardRequest': dataserializer.data}

                       return Response({'requests': request_details}, status=HTTP_200_OK)
                   else:
                       return Response([], status=HTTP_200_OK)

                else:
                  return Response(
                    serializer.errors, status=HTTP_400_BAD_REQUEST)


def emailnotification(email, subject, body,cc):
    credentials = ('2a5de2f6-18ca-41db-ba77-a67bf53e2b88', 'zpyloQRVLU548?#qjQR62(~')
    account = Account(credentials)
    # result = oauth_authentication_flow('2a5de2f6-18ca-41db-ba77-a67bf53e2b88', 'zpyloQRVLU548?#qjQR62(~', ['basic', 'message_all'])
    if not account.is_authenticated:
        account.authenticate(scopes=['basic', 'message_all'])
    m = account.new_message()
    m.to.add(email)
    if cc is not None:
       m.cc.add(cc)
    m.subject = subject
    m.body = body
    m.send()



@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def sendEmail(request):
    if request.method == 'GET':
        # send_mail('testing', 'Here is the new message.', 'kalesha.sheik@aricent.com', ['kalesha.sheik@aricent.com'], fail_silently=False,)

      #  token = None
        #with open('o365_token.txt', 'r') as file:
         #   for line in file:
         #      # print(line)
          #      if 'access_token' in line:
          #          token = line.split(':')[-1].strip()

       # print(token)
        credentials = ('2a5de2f6-18ca-41db-ba77-a67bf53e2b88', 'zpyloQRVLU548?#qjQR62(~')
        account = Account(credentials)
        #result = oauth_authentication_flow('2a5de2f6-18ca-41db-ba77-a67bf53e2b88', 'zpyloQRVLU548?#qjQR62(~', ['basic', 'message_all'])
        if not account.is_authenticated:
            account.authenticate(scopes=['basic', 'message_all'])
        m = account.new_message()
        m.to.add('kalesha.sheik@aricent.com')

        m.subject = 'new testing mail 15th feb!'
        m.body = "U have new mail"
        m.send()

        return Response('Email Sent', status=HTTP_200_OK)

    elif request.method == 'POST':
        mailserver = smtplib.SMTP('smtp.office365.com', 587)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login('kalesha.sheik@aricent.com', 'SKhappy@029')
        mailserver.sendmail('kalesha.sheik@aricent.com')
        mailserver.quit()
        return Response('Email Sent using smtp', status=HTTP_200_OK)



def gettoken(request):
  auth_code = request.GET['code']
  return HttpResponse('Authorization code: {0}'.format(auth_code))



