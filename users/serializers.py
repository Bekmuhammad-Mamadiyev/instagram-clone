from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utility import check_email_or_phone, send_email, check_user_type
from users.models import User, UserConfirmation, VIA_PHONE, VIA_EMAIL, NEW, CODE_VERIFIED, PHOTO_DONE, DONE
from rest_framework import serializers
from django.db.models import Q


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status'
        )
        extra_kwargs = {
            'auth_type': {'read_only': True, 'required': False},
            'auth_status': {'read_only': True, 'required': False}
        }

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
            # send_phone_code(user.phone_number, code)
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        print(data)
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input)
        if input_type == "email":
            data = {
                "email": user_input,
                "auth_type": VIA_EMAIL
            }
        elif input_type == "phone":
            data = {
                "phone_number": user_input,
                "auth_type": VIA_PHONE
            }
        else:
            data = {
                'success': False,
                'message': "You must send email or phone number"
            }
            raise ValidationError(data)

        return data

    def validate_phone_and_email(self, value):
        value = value.lower()
        if value and User.objects.filter(email=value).exists():
            raise ValidationError({"success": False,
                                   "message": "Email already exists"})
        elif value and User.objects.filter(phone_number=value).exists():
            raise ValidationError({"success": False,
                                   "message": "Phone number already exists"})
        return value

    def to_representation(self, instance):
        print("torepresentation:", instance)

        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())

        return data


class ChangeUserInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        password = data.get("password", None)
        confirm_password = data.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError(
                {
                    "message": "Parol va Tasdiqlash paroli mos emas"
                }
            )
        if password:
            validate_password(password)
            validate_password(confirm_password)
        return data

    def validate_username(self, username):
        if len(username) < 3 or len(username) > 30:
            raise ValidationError(
                {
                    "message": "Username 3 tadan uzun 30 tadan kam bo'lishi kerak"
                }
            )

        if username.isdigit():
            raise ValidationError({
                "message": "Username faqat raqamdan iborat bo'lishi mumkin emas"
            })
        return username

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE
        instance.save()
        return instance


class ChangeUserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(
        validators=[FileExtensionValidator
                    (allowed_extensions=
                     ["jpg", "jpeg", "heic", "png", "heif"])])

    def update(self, instance, validated_data):
        photo = validated_data.get("photo")
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_DONE
            instance.save()
        return instance



class LoginSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False,read_only=True)

    def auth_validate(self, data):
        user_input = data.get('userinput') #phone # username, #email
        if check_user_type(user_input) == "username":
            username = user_input
        elif check_user_type(user_input) == "email":
            user = User.objects.get(email__iexact = user_input)
            username = user.username
        elif check_user_type(user_input) == "phone":
            user = User.objects.get(phone__iexact = user_input)
            username = user.username
        else:
            data = {
                "success":False,
                "message":"Username, email yoki telefon raqam xato!"
            }
            raise ValidationError(data)

        authentication_kwargs = {
            self.username_field:username,
            "password":data["password"],
        }
        current_user = User.objects.filter(username__iexact = username).first()
        if current_user is not None and current_user.auth_status in [NEW, CODE_VERIFIED, DONE]:
            raise ValidationError(
                {
                    "success":False,
                    "message":"Siz hali to'liq ro'yhatdan o'tmagansiz!"
                }
            )
        user = authenticate(**authentication_kwargs)
        if user is not None:
            self.user = user
        else:
            raise ValidationError(
                {
                    "success":False,
                    "message":"Login va parolingiz topilmadi qayta urinib ko'ring"
                }
            )

    def validate(self,data):
        self.auth_validate(data)
        if self.user.auth_status not in [PHOTO_DONE]:
            raise PermissionDenied("siz hali login qiolmaysiz!")
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        return data


# class LoginRefreshSerializer(TokenRefreshSerializer):
#
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         access_token_instance = AccessToken(data['access_token'])
#         user_id = access_token_instance['user_id']
#         user = get_object_or_404(User, id=user_id)
#         update_last_login(None, user)
#         return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone', None)
        if email_or_phone is None:
            raise ValidationError({
                "success": False,
                "message":"Email yoki telefon raqam xato!"
            })
        user = User.objects.filter(Q(phone_number = email_or_phone) | Q(email = email_or_phone))
        print(user)
        if not user.exists():
            raise NotFound(detail="Email yoki telefon raqam xato!")
        attrs['user'] = user.first()
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'password', 'confirm_password')

    def validate(self, attrs):
        password = attrs.get('password', None)
        confirm_password = attrs.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError({
                "success": False,
                "message":"Parollaringiz bir biriga mos emas"
            })

        if password:
            validate_password(password)
        return attrs

    def update(self, instance, validated_data):
        password = self.validated_data.pop('password')
        instance.set_password(password)

        return super(ResetPasswordSerializer, self).update(instance, validated_data)