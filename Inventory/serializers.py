from rest_framework import serializers
from . import models




class InventorySerializer(serializers.ModelSerializer):

    class Meta:
         fields = '__all__'
         model = models.Inventory


class RequestInventorySerializer(serializers.ModelSerializer):

    class Meta:
         fields = '__all__'
         model = models.RequestInventory


class UserHierarchySerializer(serializers.ModelSerializer):

    class Meta:
         fields = '__all__'
         model = models.UserHierarchy


class InventoryValueSerializer(serializers.ModelSerializer):

    class Meta:
         fields = '__all__'
         model = models.InventoryValues


class UserInventorySerializer(serializers.ModelSerializer):

    class Meta:
         fields = '__all__'
         model = models.UserInventory


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = models.CustomUser


class UserRoleSerializer(serializers.ModelSerializer):
    level = UserSerializer(read_only=True)

    class Meta:
         fields = '__all__'
         model = models.UserRole



