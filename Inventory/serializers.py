from rest_framework import serializers
from . import models


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = models.CustomUser


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
