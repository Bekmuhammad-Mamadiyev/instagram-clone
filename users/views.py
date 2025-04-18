from tokenize import TokenError

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from rest_framework import permissions
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from shared.utility import send_email, check_email_or_phone
from .models import User, NEW, CODE_VERIFIED, VIA_EMAIL, VIA_PHONE
from .serializers import SignUpSerializer, ChangeUserInfoSerializer, ChangeUserPhotoSerializer, LoginSerializer, \
    LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer


class UserCreateView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permissions = (permissions.AllowAny)


class VerifyAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')

        self.check_verify(user, code)
        return Response(
            data={
                "success": True,
                "auth_status": user.auth_status,
                'access': user.token()['access'],
                'refresh': user.token()['refresh_token']
            }
        )

    @staticmethod
    def check_verify(user, code):
        verifies = user.verify_codes.filter(expiration_time__gte=now(), code=code, is_confirmed=False)
        print(verifies)
        if not verifies.exists():
            data = {
                "message": "Tasdiqlash kodingiz xato yoki eskirgan"
            }
            raise ValidationError(data)
        else:
            verifies.update(is_confirmed=True)
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True


class GetNewVerifyView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        self.check_verification(user)

        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        else:
            data = {
                "message": "email yoki telefon number xato"
            }
            raise ValidationError(data)

        return Response(
            {
                "success": True,
                "message": "Kod qaytadan jo'natildi"
            }
        )

    @staticmethod
    def check_verification(user):
        verifies = user.verify_codes.filter(expiration_time__gte=now(), is_confirmed=False)
        if verifies.exists():
            data = {
                "message": "hali kodingizni muddati yaroqli"
            }
            raise ValidationError(data)


#
class ChangeInformationView(UpdateAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ChangeUserInfoSerializer
    http_method_names = ['patch', 'put']

    def get_object(self):
        print(self.request.user)
        return self.request.user

    def update(self, request, *args, **kwargs, ):
        super(ChangeInformationView, self).update(request, *args, **kwargs)
        data = {
            'success': True,
            "message": "User info updated",
            "auth_status": self.request.user.auth_status,
        }

        return Response(
            data, status=200
        )

    def partial_update(self, request, *args, **kwargs, ):
        super(ChangeInformationView, self).partial_update(request, *args, **kwargs)
        data = {
            'success': True,
            "message": "User info updated",
            "auth_status": self.request.user.auth_status,
        }

        return Response(
            data, status=200)


class ChangeUserPhotoView(APIView):
    permission_classes = [IsAuthenticated,]

    def put(self, request, *args, **kwargs):
        serializer = ChangeUserPhotoSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            serializer.update(user,serializer.validated_data)
            return Response(
                {
                    "message":"Rasm o'zgartirildi"
                }
            )
        return Response(
            serializer.errors, status=400
        )

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LogoutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated,]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                "success": True,
                "message":"Akkountdan chiqdingiz"
            }
            return Response(data)
        except TokenError:
            data = {
                "success": False,
                "message":"Tokenda xatolik bor",
            }
            raise ValidationError(data)



class ForgotPasswordView(APIView):
    permission_classes = [AllowAny,]
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')
        email_or_phone = serializer.validated_data.get('email_or_phone')
        if check_email_or_phone(email_or_phone) == 'phone':
            code = user.create_verify_code(VIA_PHONE)
            send_email(email_or_phone,code)
        elif check_email_or_phone(email_or_phone) == 'email':
            code = user.create_verify_code(VIA_EMAIL)
            send_email(email_or_phone,code)
        return Response(
            {
                "success": True,
                "message": "Parolingizni qayta tiklash uchun tasdiqlash kodi yuborili:",
                "auth_status": user.auth_status,
                "access":user.token()['access'],
                "refresh":user.token()['refresh_token'],

            },
            status=200
        )

class ResetPasswordView(UpdateAPIView):
    permission_classes = [AllowAny,]
    serializer_class = ResetPasswordSerializer
    http_method_names = ['patch', 'put']
    def get_object(self):
        return self.request.user
    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordView, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data['id'])
        except ObjectDoesNotExist as e:
            raise NotFound(detail="User not found")
        return Response(
            {
                "success": True,
                "message": "Parol o'zgartirildi",
                "access": user.token()['access'],
                "refresh": user.token()['refresh_token'],
            }
        )
