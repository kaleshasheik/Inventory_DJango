from django.db import models
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, BaseUserManager
from rest_framework.authtoken.models import Token


class CustomAccountManager(BaseUserManager):
    def create_user(self, email,  password):
        user = self.model(email=email, password=password)
        user.set_password(password)
        user.is_staff = False
        user.is_superuser = False
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(email=email,  password=password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        Token.objects.create(user=user)

        return user

    def get_by_natural_key(self, email_):

        return self.get(email=email_)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(unique=True)
    employee_id = models.CharField(max_length=13, unique=True)
    name = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=13, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_first_login = models.BooleanField(default=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'User'

    objects = CustomAccountManager()

    def get_short_name(self):
        return self.email

    def get_role(self):
        return self.role

    def natural_key(self):
        return self.email

    def __str__(self):
        return self.email


class Roles(models.Model):
    id = models.IntegerField(primary_key=True)
    role_type = models.CharField(max_length=100)

    class Meta:
        db_table = 'Roles'






class Inventory(models.Model):

      product_type = models.CharField(max_length=500)
      class Meta:
          db_table = 'Inventory_Ref'


class InventoryValues(models.Model):

      product_type_id = models.IntegerField(null=False)
      model = models.CharField(max_length=100)
      serial_no = models.CharField(max_length=100, blank= True)
      sim_no = models.CharField(max_length=100, null=True, blank= True)
      status = models.CharField(max_length=100, default='Available')
      manufacturer = models.CharField(max_length=100, null=True, blank= True)
      configuration = models.CharField(max_length=100, null=True, blank= True)
      purchase_dt = models.DateTimeField(auto_now_add=False, null=True, blank= True)
      creation_dt = models.DateTimeField(auto_now_add=True, null=True, blank= True)

      class Meta:
         db_table = 'Inventory_Values'


class UserInventory(models.Model):

    employee_id = models.CharField(max_length=100, null=True, blank= True, default='0')
    product = models.ForeignKey(InventoryValues, on_delete=models.CASCADE)
    #start_date = models.DateTimeField(auto_now_add=True)
    #end_date = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'User_Inventory'


class Status(models.Model):
    id = models.IntegerField(primary_key=True)
    status_code = models.CharField(max_length=100)

    class Meta:
        db_table = 'Request_Status_Values'

class RequestInventory(models.Model):

    request_id = models.CharField(max_length=100, null=True)
    employee_id = models.CharField(max_length=100)
    name = models.CharField(max_length=30)
    product_type = models.CharField(max_length=100)
    startDate = models.DateTimeField(auto_now_add=False)
    endDate = models.DateTimeField(auto_now_add=False)
    reason = models.CharField(max_length=30)
    status = models.CharField(max_length=30, default='1')
    laptopNO = models.CharField(max_length=30, null=True)
    dataCardNO = models.CharField(max_length=30, null=True)
    comment = models.CharField(max_length=30, null=True)

    class Meta:
        db_table = 'Request'


class UserHierarchy(models.Model):
    id = models.IntegerField(primary_key=True)
    Employee_id = models.CharField(max_length=200)
    supervisor_1 = models.CharField(max_length=100)
    supervisor_2 = models.CharField(max_length=100)

    class Meta:
        db_table = 'User_Hierarchy'



class UserRole(models.Model):

   # employee_id = models.ForeignKey('CustomUser', db_column='employee_id',max_length=20, on_delete=models.CASCADE, )
    #employee_id = models.CharField(max_length=20)
    employee_id = models.CharField(max_length=13, unique=True)
    supervisor_id = models.CharField(max_length=20, null=True, blank= True)
    is_manager = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1)


    class Meta:
        db_table = 'User_Role'

