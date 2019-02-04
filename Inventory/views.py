from .serializers import UserSerializer, InventorySerializer, RequestInventorySerializer, UserHierarchySerializer, InventoryValueSerializer
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

@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def user(request):

    if request.method == 'GET':
        queryset = models.CustomUser.objects.filter(is_active=True)
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        role = request.data.get('role', None)
        serializer = UserSerializer(data=request.data)
        password = BaseUserManager().make_random_password(20)
        if serializer.is_valid():
           user = serializer.save()
           print(password)
           user.set_password(password)

           user.save()
           queryset = models.CustomUser.objects.filter(is_active=True)
           serializer = UserSerializer(queryset, many=True)
           return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':

        email = request.data.get('email', None)
        if email is not None:
            queryset = models.CustomUser.objects.get(email=email)
            serializer = UserSerializer(queryset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                queryset = models.CustomUser.objects.filter(is_active=True)
                serializer = UserSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response('failed to updated user details', status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        email = request.data.get('email', None)
        print(request.data)
        if email is not None:
            models.CustomUser.objects.filter(email=email).delete()
            queryset = models.CustomUser.objects.filter(is_active=True)
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)




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
                queryset = models.CustomUser.objects.filter(email=user)
                serializer = UserSerializer(queryset, many=True)
                user_details = {'user': serializer.data, 'token': token.key}
                return Response(user_details,status=HTTP_200_OK)
            else:
                return Response('Failed to update password', status=HTTP_200_OK)

        else:
            return Response('Email is empty', status=HTTP_200_OK)



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

    queryset = models.CustomUser.objects.filter(email=user)

    serializer = UserSerializer(queryset, many=True)

    user_details = {'user': serializer.data, 'token': token.key}

    return Response(user_details,

                    status=HTTP_200_OK)


@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def request_inventory(request):

      if request.method == 'GET':
         emp_id = request.query_params.get('employee_id', None)
         role = request.query_params.get('role', None)


         if emp_id is not None:
            queryset = models.RequestInventory.objects.filter(employee_id=emp_id, type='Laptop').filter(status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin', 'Assigned to User'])
            laptopSerializer = RequestInventorySerializer(queryset, many=True)
            queryset = models.RequestInventory.objects.filter(employee_id=emp_id, type='DataCard').filter(status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin','Assigned to User'])
            datacardSerializer = RequestInventorySerializer(queryset, many=True)

            queryset = models.RequestInventory.objects.filter(status='Completed')
            approvedRequests = RequestInventorySerializer(queryset, many=True)

            if role =='Employee':
                queryset = models.RequestInventory.objects.filter(employee_id=emp_id, status__in=['User Cancelled', 'Completed','L1 Rejected','L2 Rejected', 'Admin Rejected'])
                history = RequestInventorySerializer(queryset, many=True)
                request_details = {'laptopRequest': laptopSerializer.data, 'datacardRequest': datacardSerializer.data,
                                   'history': history.data, 'approved': [],'pending': []}
                return Response(request_details, status=status.HTTP_200_OK)
            else:
                if role =='L1 Manager':
                   queryset = models.RequestInventory.objects.filter(status__in=['User Cancelled', 'Completed','L1 Rejected','L2 Rejected', 'Admin Rejected'])
                   history = RequestInventorySerializer(queryset, many=True)

                   users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                       supervisor_1=emp_id)
                   queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                       status='Pending With L1')
                   pendingRequests = RequestInventorySerializer(queryset, many=True)

                   request_details = {'laptopRequest': laptopSerializer.data, 'datacardRequest': datacardSerializer.data , 'history': history.data,
                                      'approved': approvedRequests.data, 'pending': pendingRequests.data}
                   return Response(request_details, status=status.HTTP_200_OK)

                elif role =='L2 Manager':
                    queryset = models.RequestInventory.objects.filter(status__in=['User Cancelled', 'Completed','L1 Rejected','L2 Rejected', 'Admin Rejected'])
                    history = RequestInventorySerializer(queryset, many=True)

                    users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                        supervisor_2=emp_id)
                    queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                        status='Pending With L2')
                    pendingRequests = RequestInventorySerializer(queryset, many=True)

                    request_details = {'laptopRequest': laptopSerializer.data,
                                       'datacardRequest': datacardSerializer.data, 'history': history.data,
                                       'approved': approvedRequests.data, 'pending': pendingRequests.data}
                    return Response(request_details, status=status.HTTP_200_OK)

                elif role =='Inventory Manager':
                    queryset = models.RequestInventory.objects.filter(status__in=['User Cancelled', 'Completed','L1 Rejected','L2 Rejected', 'Admin Rejected'])
                    history = RequestInventorySerializer(queryset, many=True)


                    queryset = models.RequestInventory.objects.filter(
                        status__in=['Pending With Admin', 'Surender Pending'])

                    pendingRequests = RequestInventorySerializer(queryset, many=True)

                    request_details = {'laptopRequest': laptopSerializer.data,
                                       'datacardRequest': datacardSerializer.data, 'history': history.data,
                                       'approved': approvedRequests.data, 'pending': pendingRequests.data}
                    return Response(request_details, status=status.HTTP_200_OK)




      elif request.method == 'POST':
          inv_type = request.data.get("type")
          emp_id = request.data.get("employee_id", None)
          role = request.data.get("role", None)
          serializer = RequestInventorySerializer(data=request.data)
          print(request.data)

          if serializer.is_valid():
              if inv_type == 'Both':
                  laptopserializer = RequestInventorySerializer(data=request.data)
                  datacardserializer = RequestInventorySerializer(data=request.data)
                  if laptopserializer.is_valid():
                      laptop= laptopserializer.save(type='Laptop')
                      req_id = 'REQ_LAP' + str(laptop.id)
                      laptopserializer.save(type='Laptop', request_id=req_id, comment='Laptop Request')


                  if datacardserializer.is_valid():
                     datacard = datacardserializer.save(type='DataCard')
                     req_id = 'REQ_DAT' + str(datacard.id)
                     datacardserializer.save(type='DataCard', request_id=req_id, comment='DataCard Request')

                  if emp_id is not None:
                      queryset = models.RequestInventory.objects.filter(employee_id=emp_id, type='Laptop').filter(
                          status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin', 'Assigned to User'])
                      laptopSerializer = RequestInventorySerializer(queryset, many=True)
                      queryset = models.RequestInventory.objects.filter(employee_id=emp_id, type='DataCard').filter(
                          status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin', 'Assigned to User'])
                      datacardSerializer = RequestInventorySerializer(queryset, many=True)

                      queryset = models.RequestInventory.objects.filter(status='Completed')
                      approvedRequests = RequestInventorySerializer(queryset, many=True)

                      if role == 'Employee':
                          queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                            status__in=['User Cancelled', 'Completed',
                                                                                        'L1 Rejected', 'L2 Rejected',
                                                                                        'Admin Rejected'])
                          history = RequestInventorySerializer(queryset, many=True)
                          request_details = {'laptopRequest': laptopSerializer.data,
                                             'datacardRequest': datacardSerializer.data,
                                             'history': history.data, 'approved': [], 'pending': []}
                          return Response(request_details, status=status.HTTP_200_OK)
                      else:
                          if role == 'L1 Manager':
                              queryset = models.RequestInventory.objects.filter(
                                  status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                              'Admin Rejected'])
                              history = RequestInventorySerializer(queryset, many=True)

                              users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                  supervisor_1=emp_id)
                              queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                  status='Pending With L1')
                              pendingRequests = RequestInventorySerializer(queryset, many=True)

                              request_details = {'laptopRequest': laptopSerializer.data,
                                                 'datacardRequest': datacardSerializer.data, 'history': history.data,
                                                 'approved': approvedRequests.data, 'pending': pendingRequests.data}
                              return Response(request_details, status=status.HTTP_200_OK)

                          elif role == 'L2 Manager':
                              queryset = models.RequestInventory.objects.filter(
                                  status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                              'Admin Rejected'])
                              history = RequestInventorySerializer(queryset, many=True)

                              users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                  supervisor_2=emp_id)
                              queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                  status='Pending With L2')
                              pendingRequests = RequestInventorySerializer(queryset, many=True)

                              request_details = {'laptopRequest': laptopSerializer.data,
                                                 'datacardRequest': datacardSerializer.data, 'history': history.data,
                                                 'approved': approvedRequests.data, 'pending': pendingRequests.data}
                              return Response(request_details, status=status.HTTP_200_OK)

                          elif role == 'Inventory Manager':
                              queryset = models.RequestInventory.objects.filter(
                                  status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                              'Admin Rejected'])
                              history = RequestInventorySerializer(queryset, many=True)

                              queryset = models.RequestInventory.objects.filter(
                                  status__in=['Pending With Admin', 'Surender Pending'])
                              pendingRequests = RequestInventorySerializer(queryset, many=True)

                              request_details = {'laptopRequest': laptopSerializer.data,
                                                 'datacardRequest': datacardSerializer.data, 'history': history.data,
                                                 'approved': approvedRequests.data, 'pending': pendingRequests.data}
                              return Response(request_details, status=status.HTTP_200_OK)


              else:
                  if inv_type == 'Laptop':
                      laptopserializer = RequestInventorySerializer(data=request.data)
                      if laptopserializer.is_valid():
                         laptop = laptopserializer.save(type='Laptop')
                         req_id = 'REQ_LAP' + str(laptop.id)
                         laptopserializer.save(type='Laptop', request_id=req_id, comment='Laptop Request')
                         if emp_id is not None:
                             queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                               type='Laptop').filter(
                                 status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin',
                                             'Assigned to User'])
                             laptopSerializer = RequestInventorySerializer(queryset, many=True)
                             queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                               type='DataCard').filter(
                                 status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin',
                                             'Assigned to User'])
                             datacardSerializer = RequestInventorySerializer(queryset, many=True)

                             queryset = models.RequestInventory.objects.filter(status='Completed')
                             approvedRequests = RequestInventorySerializer(queryset, many=True)

                             if role == 'Employee':
                                 queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                   status__in=['User Cancelled',
                                                                                               'Completed',
                                                                                               'L1 Rejected',
                                                                                               'L2 Rejected',
                                                                                               'Admin Rejected'])
                                 history = RequestInventorySerializer(queryset, many=True)
                                 request_details = {'laptopRequest': laptopSerializer.data,
                                                    'datacardRequest': datacardSerializer.data,
                                                    'history': history.data, 'approved': [], 'pending': []}
                                 return Response(request_details, status=status.HTTP_200_OK)
                             else:
                                 if role == 'L1 Manager':
                                     queryset = models.RequestInventory.objects.filter(
                                         status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                                     'Admin Rejected'])
                                     history = RequestInventorySerializer(queryset, many=True)

                                     users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                         supervisor_1=emp_id)
                                     queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                         status='Pending With L1')
                                     pendingRequests = RequestInventorySerializer(queryset, many=True)

                                     request_details = {'laptopRequest': laptopSerializer.data,
                                                        'datacardRequest': datacardSerializer.data,
                                                        'history': history.data,
                                                        'approved': approvedRequests.data,
                                                        'pending': pendingRequests.data}
                                     return Response(request_details, status=status.HTTP_200_OK)

                                 elif role == 'L2 Manager':
                                     queryset = models.RequestInventory.objects.filter(
                                         status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                                     'Admin Rejected'])
                                     history = RequestInventorySerializer(queryset, many=True)

                                     users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                         supervisor_2=emp_id)
                                     queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                         status='Pending With L2')
                                     pendingRequests = RequestInventorySerializer(queryset, many=True)

                                     request_details = {'laptopRequest': laptopSerializer.data,
                                                        'datacardRequest': datacardSerializer.data,
                                                        'history': history.data,
                                                        'approved': approvedRequests.data,
                                                        'pending': pendingRequests.data}
                                     return Response(request_details, status=status.HTTP_200_OK)

                                 elif role == 'Inventory Manager':
                                     queryset = models.RequestInventory.objects.filter(
                                         status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                                     'Admin Rejected'])
                                     history = RequestInventorySerializer(queryset, many=True)

                                     queryset = models.RequestInventory.objects.filter(
                                         status__in=['Pending With Admin', 'Surender Pending'])
                                     pendingRequests = RequestInventorySerializer(queryset, many=True)

                                     request_details = {'laptopRequest': laptopSerializer.data,
                                                        'datacardRequest': datacardSerializer.data,
                                                        'history': history.data,
                                                        'approved': approvedRequests.data,
                                                        'pending': pendingRequests.data}
                                     return Response(request_details, status=status.HTTP_200_OK)


                  elif inv_type == 'DataCard':
                       datacardserializer = RequestInventorySerializer(data=request.data)
                       if datacardserializer.is_valid():
                          datacard = datacardserializer.save(type='DataCard')
                          req_id = 'REQ_DAT' + str(datacard.id)
                          datacardserializer.save(type='DataCard', request_id=req_id, comment='DataCard Request')
                          if emp_id is not None:
                              queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                type='Laptop').filter(
                                  status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin',
                                              'Assigned to User'])
                              laptopSerializer = RequestInventorySerializer(queryset, many=True)
                              queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                type='DataCard').filter(
                                  status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin',
                                              'Assigned to User'])
                              datacardSerializer = RequestInventorySerializer(queryset, many=True)

                              queryset = models.RequestInventory.objects.filter(status='Completed')
                              approvedRequests = RequestInventorySerializer(queryset, many=True)

                              if role == 'Employee':
                                  queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                                    status__in=['User Cancelled',
                                                                                                'Completed',
                                                                                                'L1 Rejected',
                                                                                                'L2 Rejected',
                                                                                                'Admin Rejected'])
                                  history = RequestInventorySerializer(queryset, many=True)
                                  request_details = {'laptopRequest': laptopSerializer.data,
                                                     'datacardRequest': datacardSerializer.data,
                                                     'history': history.data, 'approved': [], 'pending': []}
                                  return Response(request_details, status=status.HTTP_200_OK)
                              else:
                                  if role == 'L1 Manager':
                                      queryset = models.RequestInventory.objects.filter(
                                          status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                                      'Admin Rejected'])
                                      history = RequestInventorySerializer(queryset, many=True)

                                      users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                          supervisor_1=emp_id)
                                      queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                          status='Pending With L1')
                                      pendingRequests = RequestInventorySerializer(queryset, many=True)

                                      request_details = {'laptopRequest': laptopSerializer.data,
                                                         'datacardRequest': datacardSerializer.data,
                                                         'history': history.data,
                                                         'approved': approvedRequests.data,
                                                         'pending': pendingRequests.data}
                                      return Response(request_details, status=status.HTTP_200_OK)

                                  elif role == 'L2 Manager':
                                      queryset = models.RequestInventory.objects.filter(
                                          status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                                      'Admin Rejected'])
                                      history = RequestInventorySerializer(queryset, many=True)

                                      users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                          supervisor_2=emp_id)
                                      queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                          status='Pending With L2')
                                      pendingRequests = RequestInventorySerializer(queryset, many=True)

                                      request_details = {'laptopRequest': laptopSerializer.data,
                                                         'datacardRequest': datacardSerializer.data,
                                                         'history': history.data,
                                                         'approved': approvedRequests.data,
                                                         'pending': pendingRequests.data}
                                      return Response(request_details, status=status.HTTP_200_OK)

                                  elif role == 'Inventory Manager':
                                      queryset = models.RequestInventory.objects.filter(
                                          status__in=['User Cancelled', 'Completed', 'L1 Rejected', 'L2 Rejected',
                                                      'Admin Rejected'])
                                      history = RequestInventorySerializer(queryset, many=True)

                                      queryset = models.RequestInventory.objects.filter(
                                          status__in=['Pending With Admin', 'Surender Pending'])
                                      pendingRequests = RequestInventorySerializer(queryset, many=True)

                                      request_details = {'laptopRequest': laptopSerializer.data,
                                                         'datacardRequest': datacardSerializer.data,
                                                         'history': history.data,
                                                         'approved': approvedRequests.data,
                                                         'pending': pendingRequests.data}
                                      return Response(request_details, status=status.HTTP_200_OK)


                  else:

                       return Response('Invalid Inventory Type', status=status.HTTP_201_CREATED)

          else:
              return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

      elif request.method == 'PUT':

           requestId = request.data.get("request_id", None)

           role = request.data.get("role", None)

           print(requestId)
           print(role)
           if requestId is not None:
              queryset = models.RequestInventory.objects.get(request_id=requestId)
              print(queryset)
              serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
              print(request.data)
              if serializer.is_valid():
                 serializer.save()
                 print(serializer.data)
                 emp_id = request.data.get('employee_id', None)
                 print(emp_id)

                 queryset = models.RequestInventory.objects.filter(employee_id=emp_id, type='Laptop').filter(
                     status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin', 'Assigned to User'])
                 laptopSerializer = RequestInventorySerializer(queryset, many=True)
                 queryset = models.RequestInventory.objects.filter(employee_id=emp_id, type='DataCard').filter(
                     status__in=['Pending With L1', 'Pending With L2', 'Pending With Admin', 'Assigned to User'])
                 datacardSerializer = RequestInventorySerializer(queryset, many=True)

                 queryset = models.RequestInventory.objects.filter(status='Completed')
                 approvedRequests = RequestInventorySerializer(queryset, many=True)

                 if role == 'Employee':
                     queryset = models.RequestInventory.objects.filter(employee_id=emp_id,
                                                                       status__in=['User Cancelled', 'Completed',
                                                                                   'L1 Rejected', 'L2 Rejected',
                                                                                   'Admin Rejected'])
                     history = RequestInventorySerializer(queryset, many=True)
                     request_details = {'laptopRequest': laptopSerializer.data,
                                        'datacardRequest': datacardSerializer.data,
                                        'history': history.data, 'approved': [], 'pending': []}
                     return Response(request_details, status=status.HTTP_200_OK)
                 else:
                     if role == 'L1 Manager':
                         queryset = models.RequestInventory.objects.filter(status__in=['User Cancelled', 'Completed','L1 Rejected','L2 Rejected', 'Admin Rejected'])
                         history = RequestInventorySerializer(queryset, many=True)

                         users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                             supervisor_1=emp_id)
                         queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                             status='Pending With L1')
                         pendingRequests = RequestInventorySerializer(queryset, many=True)

                         request_details = {'laptopRequest': laptopSerializer.data,
                                            'datacardRequest': datacardSerializer.data, 'history': history.data,
                                            'approved': approvedRequests.data, 'pending': pendingRequests.data}
                         return Response(request_details, status=status.HTTP_200_OK)

                     elif role == 'L2 Manager':
                         queryset = models.RequestInventory.objects.filter(status__in=['User Cancelled', 'Completed','L1 Rejected','L2 Rejected', 'Admin Rejected'])
                         history = RequestInventorySerializer(queryset, many=True)

                         users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                             supervisor_2=emp_id)
                         queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                             status='Pending With L2')
                         pendingRequests = RequestInventorySerializer(queryset, many=True)

                         request_details = {'laptopRequest': laptopSerializer.data,
                                            'datacardRequest': datacardSerializer.data, 'history': history.data,
                                            'approved': approvedRequests.data, 'pending': pendingRequests.data}
                         return Response(request_details, status=status.HTTP_200_OK)

                     elif role == 'Inventory Manager':
                         queryset = models.RequestInventory.objects.filter(status__in=['User Cancelled', 'Completed','L1 Rejected','L2 Rejected', 'Admin Rejected'])
                         history = RequestInventorySerializer(queryset, many=True)

                         queryset = models.RequestInventory.objects.filter(
                             status__in=['Pending With Admin', 'Surender Pending'])
                         pendingRequests = RequestInventorySerializer(queryset, many=True)

                         request_details = {'laptopRequest': laptopSerializer.data,
                                            'datacardRequest': datacardSerializer.data, 'history': history.data,
                                            'approved': approvedRequests.data, 'pending': pendingRequests.data}
                         return Response(request_details, status=status.HTTP_200_OK)

              else:
                 return Response(
                  serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           else:
               return Response(
                   "Invalid Request", status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def inventory_Values(request):

    if request.method == 'GET':
        iStatus = request.query_params.get('status', None)
        if iStatus is not None:
           queryset = models.InventoryValues.objects.filter(status= iStatus, product_type='Laptop')
           lapserializer = InventoryValueSerializer(queryset, many=True)

           queryset = models.InventoryValues.objects.filter(status=iStatus, product_type='DataCard')
           dataserializer = InventoryValueSerializer(queryset, many=True)
           request_details = {'laptopDetails': lapserializer.data,
                              'datacardDetails': dataserializer.data}
           return Response(request_details, status=status.HTTP_200_OK)

        else:
            queryset = models.InventoryValues.objects.all()
            serializer = InventoryValueSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        print(request.data)
        serializer = InventoryValueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            queryset = models.InventoryValues.objects.all()
            serializer = InventoryValueSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':

        serial_no = request.data.get('serial_no', None)
        print(serial_no)
        if serial_no is not None:
            queryset = models.InventoryValues.objects.get(serial_no= serial_no)
            serializer = InventoryValueSerializer(queryset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                queryset = models.InventoryValues.objects.all()
                serializer = InventoryValueSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response('failed to updated Inventory details', status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        serial_no = request.data.get('serial_no', None)
        print(request.data)
        if serial_no is not None:
            models.InventoryValues.objects.filter(serial_no=serial_no).delete()
            queryset = models.InventoryValues.objects.all()
            serializer = InventoryValueSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def requests(request):

    if request.method == 'GET':
        emp_id = request.query_params.get('employee_id', None)
        if emp_id is not None:

            # user = models.CustomUser.objects.filter(employee_id__in=[24415, 112424])

            role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
            print(role)
            if role == 'L1 Manager':
               users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(supervisor_1=emp_id)
               queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(status='Pending With L1')
               requests = RequestInventorySerializer(queryset, many=True)
               return Response(requests.data, status=status.HTTP_200_OK)

            elif role == 'L2 Manager':
               users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(supervisor_2=emp_id)
               queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(status='Pending With L2')
               requests = RequestInventorySerializer(queryset, many=True)
               return Response(requests.data, status=status.HTTP_200_OK)

            elif role == 'Inventory Manager':

               queryset = models.RequestInventory.objects.filter(status__in=['Pending With Admin', 'Surender Pending'])
               requests = RequestInventorySerializer(queryset, many=True)
               return Response(requests.data, status=status.HTTP_200_OK)
            else:
                return Response([], status=status.HTTP_200_OK)

    elif request.method == 'PUT':
         requestId = request.data.get("request_id", None)

         emp_id = request.data.get("emp_id", None)
         invValue = request.data.get("invValue", None)
         invType = request.data.get("invType", None)
         iStatus = request.data.get("status", None)

         print(emp_id)

         queryset = models.InventoryValues.objects.filter(status='Available', product_type='Laptop')
         lapserializer = InventoryValueSerializer(queryset, many=True)

         queryset = models.InventoryValues.objects.filter(status='Available', product_type='DataCard')
         dataserializer = InventoryValueSerializer(queryset, many=True)
         available_inv = {'laptopDetails': lapserializer.data,
                          'datacardDetails': dataserializer.data}

         if requestId is not None:
            queryset = models.RequestInventory.objects.get(request_id=requestId)
            role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
            print(queryset)
            print(role)
            print(iStatus)
            if role == 'Inventory Manager' and iStatus == 'Assigned to User':
                    print('Assigning the inventory')
                    user = models.RequestInventory.objects.values_list('employee_id', flat=True).filter(
                        request_id=requestId).first()
                    print(user)
                    if invType == 'Laptop':
                       serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                       if serializer.is_valid():
                          serializer.save(laptopNO=invValue)
                          print('Assigned laptop inventory')
                          queryset = models.InventoryValues.objects.filter(serial_no=invValue, product_type='Laptop',status='Available').first()
                          print(queryset)
                          lapserializer = InventoryValueSerializer(queryset,  data=request.data, partial=True)
                          if lapserializer.is_valid():
                             lapserializer.save(status='Assigned', assignedTo=user)

                          if emp_id is not None:
                              role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
                              print(role)
                              if role == 'L1 Manager':
                                  users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                      supervisor_1=emp_id)
                                  queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                      status='Pending With L1')
                                  requests = RequestInventorySerializer(queryset, many=True)
                                  return Response(requests.data, status=status.HTTP_200_OK)

                              if role == 'L2 Manager':
                                  users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                      supervisor_2=emp_id)
                                  queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                      status='Pending With L2')
                                  requests = RequestInventorySerializer(queryset, many=True)
                                  return Response(requests.data, status=status.HTTP_200_OK)

                              if role == 'Inventory Manager':
                                  queryset = models.RequestInventory.objects.filter(
                                      status__in=['Pending With Admin', 'Surender Pending'])
                                  requests = RequestInventorySerializer(queryset, many=True)
                                  return Response(requests.data, status=status.HTTP_200_OK)
                          else:
                              return Response(
                                  serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    elif invType == 'DataCard':
                        serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                        if serializer.is_valid():
                            serializer.save(datacardNO=invValue)
                            print('Assigned datacard inventory')
                            queryset = models.InventoryValues.objects.filter(sim_no=invValue, product_type='DataCard',status='Available').first()
                            print(queryset)
                            dataserializer = InventoryValueSerializer(queryset, data=request.data, partial=True)
                            if dataserializer.is_valid():
                                dataserializer.save(status='Assigned', assignedTo=user)
                            if emp_id is not None:
                                role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
                                print(role)
                                if role == 'L1 Manager':
                                    users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                        supervisor_1=emp_id)
                                    queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                        status='Pending With L1')
                                    requests = RequestInventorySerializer(queryset, many=True)
                                    return Response(requests.data, status=status.HTTP_200_OK)

                                if role == 'L2 Manager':
                                    users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                        supervisor_2=emp_id)
                                    queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                        status='Pending With L2')
                                    requests = RequestInventorySerializer(queryset, many=True)
                                    return Response(requests.data, status=status.HTTP_200_OK)

                                if role == 'Inventory Manager':
                                    queryset = models.RequestInventory.objects.filter(
                                        status__in=['Pending With Admin', 'Surender Pending'])
                                    requests = RequestInventorySerializer(queryset, many=True)
                                    return Response(requests.data, status=status.HTTP_200_OK)
                            else:
                                return Response(
                                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            return Response(
                                serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            elif role == 'Inventory Manager' and iStatus == 'Completed':
                    print('Releasing the inventory')

                    user = models.RequestInventory.objects.values_list('employee_id', flat=True).filter(
                        request_id=requestId).first()
                    if invType == 'Laptop':
                       serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                       if serializer.is_valid():
                          serializer.save()
                          print('Releasing laptop inventory')
                          queryset = models.InventoryValues.objects.filter(product_type='Laptop',status='Assigned',assignedTo=user).first()
                          print(queryset)
                          lapserializer = InventoryValueSerializer(queryset,  data=request.data, partial=True)
                          if lapserializer.is_valid():
                             lapserializer.save(status='Available', assignedTo= '')

                          if emp_id is not None:
                              role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
                              print(role)
                              if role == 'L1 Manager':
                                  users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                      supervisor_1=emp_id)
                                  queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                      status='Pending With L1')
                                  requests = RequestInventorySerializer(queryset, many=True)
                                  return Response(requests.data, status=status.HTTP_200_OK)

                              if role == 'L2 Manager':
                                  users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                      supervisor_2=emp_id)
                                  queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                      status='Pending With L2')
                                  requests = RequestInventorySerializer(queryset, many=True)
                                  return Response(requests.data, status=status.HTTP_200_OK)

                              if role == 'Inventory Manager':
                                  queryset = models.RequestInventory.objects.filter(
                                      status__in=['Pending With Admin', 'Surender Pending'])
                                  requests = RequestInventorySerializer(queryset, many=True)
                                  return Response(requests.data, status=status.HTTP_200_OK)
                          else:
                              return Response(
                                  serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    elif invType == 'DataCard':
                        serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            print('Assigned datacard inventory')
                            queryset = models.InventoryValues.objects.filter(product_type='DataCard',status='Assigned',assignedTo=user).first()
                            print(queryset)
                            dataserializer = InventoryValueSerializer(queryset, data=request.data, partial=True)
                            if dataserializer.is_valid():
                                dataserializer.save(status='Available', assignedTo= '')
                            if emp_id is not None:
                                role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
                                print(role)
                                if role == 'L1 Manager':
                                    users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                        supervisor_1=emp_id)
                                    queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                        status='Pending With L1')
                                    requests = RequestInventorySerializer(queryset, many=True)
                                    return Response(requests.data, status=status.HTTP_200_OK)

                                if role == 'L2 Manager':
                                    users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                                        supervisor_2=emp_id)
                                    queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                                        status='Pending With L2')
                                    requests = RequestInventorySerializer(queryset, many=True)
                                    return Response(requests.data, status=status.HTTP_200_OK)

                                if role == 'Inventory Manager':
                                    queryset = models.RequestInventory.objects.filter(
                                        status__in=['Pending With Admin', 'Surender Pending'])
                                    requests = RequestInventorySerializer(queryset, many=True)
                                    return Response(requests.data, status=status.HTTP_200_OK)
                            else:
                                return Response(
                                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            return Response(
                                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            else:
                print(request.data)
                serializer = RequestInventorySerializer(queryset, data=request.data, partial=True)
                if serializer.is_valid():
                   serializer.save()
                   if emp_id is not None:
                      role = models.CustomUser.objects.values_list('role', flat=True).get(employee_id=emp_id)
                      print(role)
                      if role == 'L1 Manager':
                         users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                           supervisor_1=emp_id)
                         queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                           status='Pending With L1')
                         requests = RequestInventorySerializer(queryset, many=True)
                         return Response(requests.data, status=status.HTTP_200_OK)

                      if role == 'L2 Manager':
                          users = models.UserHierarchy.objects.values_list('Employee_id', flat=True).filter(
                           supervisor_2=emp_id)
                          queryset = models.RequestInventory.objects.filter(employee_id__in=[users]).filter(
                           status='Pending With L2')
                          requests = RequestInventorySerializer(queryset, many=True)
                          return Response(requests.data, status=status.HTTP_200_OK)

                      if role == 'Inventory Manager':
                         queryset = models.RequestInventory.objects.filter(status__in=['Pending With Admin', 'Surender Pending'])
                         requests = RequestInventorySerializer(queryset, many=True)
                         return Response(requests.data, status=status.HTTP_200_OK)
                   else:
                      return Response(
                       serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                  return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'POST', 'GET', 'DELETE'])
@permission_classes((AllowAny,))
def sendEmail(request):


    if request.method == 'GET':
        send_mail('testing', 'Here is the message.', 'kalesha.sheik@aricent.com', ['kalesha.sheik@aricent.com'], fail_silently=False,)

        return Response('Email Sent', status=status.HTTP_200_OK)