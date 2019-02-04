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
    employee_id = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    role = models.CharField(max_length=100, null=True)
    contact_number = models.CharField(max_length=13, null=False)
    created_on = models.DateTimeField(auto_now_add=True)
    is_first_login = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'Login'

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
      product_id = models.IntegerField(null=True)
      product_type = models.CharField(max_length=500)
      class Meta:
          db_table = 'Inventory_Types'


class InventoryValues(models.Model):
      product_type = models.CharField(max_length=500)
      model = models.CharField(max_length=100)
      serial_no = models.CharField(max_length=100)
      sim_no = models.CharField(max_length=100, null=True)
      status = models.CharField(max_length=100, default='Available')
      manufacturer = models.CharField(max_length=100, null=True)
      configuration = models.CharField(max_length=100, null=True)
      assignedTo = models.CharField(max_length=100, null=True)

      class Meta:
         db_table = 'Inventory_Values'


class Status(models.Model):
    id = models.IntegerField(primary_key=True)
    status_code = models.CharField(max_length=100)

    class Meta:
        db_table = 'Request_Status'

class RequestInventory(models.Model):

    request_id = models.CharField(max_length=100, null=True)
    employee_id = models.CharField(max_length=100)
    name = models.CharField(max_length=30)
    type = models.CharField(max_length=100)
    startDate = models.DateTimeField(auto_now_add=False)
    endDate = models.DateTimeField(auto_now_add=False)
    reason = models.CharField(max_length=30)
    status = models.CharField(max_length=30, default='Pending With L1')
    laptopNO = models.CharField(max_length=30, null=True)
    datacardNO = models.CharField(max_length=30, null=True)
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



