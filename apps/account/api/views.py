import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
import jdatetime
from django.shortcuts import get_object_or_404
from rest_framework import parsers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken as ObtainAuthT
from rest_framework.compat import coreapi, coreschema
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.schemas import ManualSchema
from rest_framework.schemas import coreapi as coreapi_schema

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView, CreateAPIView, \
    UpdateAPIView, RetrieveUpdateAPIView, ListAPIView, get_object_or_404

from SLIMS import renderers
from apps.account.api.serializers import UserSerializer, UserRegistrationSerializer, EducationalFieldSerializer, \
    EducationalLevelSerializer, AccessLevelSerializer, RoleSerializer, GrantTransactionSerializer, \
    GrantRequestSerializer, GrantRequestApprovedSerializer, UserProfileSerializer, NotificationSerializer, \
    NotificationReadSerializer, GrantRecordSerializer, UPOAuthTokenSerializer, UserBusinessLinkedAccountsSerializer, \
    LansnetGrantSerializer, UserPasswordSerializer, GrantRecordFileSerializer, GrantRequestRevokeSerializer, \
    DepartmentSerializer, UserPersonalSerializer, UserBusinessSerializer, SummaryUserSerializer, UserSummerySerializer, \
    UserDetailSerializer
from apps.account.models import User, EducationalField, EducationalLevel, AccessLevel, Role, GrantTransaction, \
    GrantRequest, OTPserver, Notification, GrantRecord, Department, LabsnetCredit
from .filters import UserFilter, GrantRecordFilter, GrantRequestFilter
from ..permissions import AccessLevelPermission, query_set_filter_key
from ...core.functions import export_excel, process_excel_and_create_grant_records, safe_jalali_to_gregorian
from ...core.paginations import DefaultPagination
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
import jwt
User = get_user_model()
from rest_framework.authtoken.models import Token

TOKEN_ENDPOINT = "https://uac.meta.sharif.ir/connect/token"
CLIENT_ID = 'LabsClient'
CLIENT_SECRET = 'Gkg/&h7N92Z0'
REDIRECT_URI = "https://lims.labs.sharif.ir/auth/sso/verify"


def exchange_token(auth_code, code_verifier):
    try:
        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "code_verifier": code_verifier,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        response = requests.post(TOKEN_ENDPOINT, data=payload)

        if response.status_code == 200:
            return response.json()

            sample = {
                "status": "success",
                "data": {
                    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjhDRDlERTQ2QzEyRTVEQ0MyOTE1QkVBNDY2MzNENDE2IiwidHlwIjoiSldUIn0.eyJuYmYiOjE3MzczMTgyNjksImV4cCI6MTczNzMxODU2OSwiaXNzIjoiaHR0cHM6Ly91YWMubWV0YS5zaGFyaWYuaXIiLCJhdWQiOiJMYWJzQ2xpZW50IiwiaWF0IjoxNzM3MzE4MjY5LCJhdF9oYXNoIjoiaVUzRWJSQk1NRjNRdzU1R1ZjSXFEZyIsInNpZCI6IkMzMERBRTZGQzI3NjkwMDE5NzNCOUJDNTg0MEFCN0YzIiwic3ViIjoiMGE4MTg3MTUtZTgyNS00MjBlLThkMGYtYWU1OGI3Mjk1MzViIiwiYXV0aF90aW1lIjoxNzM3MzE4MjQ5LCJpZHAiOiJsb2NhbCIsIkNsaWVudHMiOiIiLCJVc2VyVHlwZSI6IlJlYWwiLCJVc2VybmFtZSI6IjQ3MjM2ODY1MDkiLCJGaXJzdE5hbWUiOiLYp9iz2K_Yp9mE2YciLCJSb2xlcyI6IiIsIk5hdGlvbmFsQ29kZSI6IjQ3MjM2ODY1MDkiLCJTaGFyaWZJZCI6ImthbGFudGFyaWFuIiwiTGFzdE5hbWUiOiLaqdmE2KfZhtiq2LHbjNin2YYiLCJhbXIiOlsicHdkIl19.MhQj_ivI9ATIoqNusDxP4pee8trYjjKQC18TY5nQPJQsLIsCmMt4TvMeu0x3Bm_mqMoDcQnkV6j7vuFRqCgwMESA0K_fhgjt5oSzZVIprWqKlonG4u1TRT0o_eoHyQJKk4rMIOKyIbD0BIp9fwZoUs9j02es4rDuOSMFzSjxWhDLmqo9RusV08BF_RED8yhP4IWKUJ33aPbYapVyPoEWexfoW56z5lcTylqDKHkNCscxA5kghA8FJiJHws9KpZqkaPoF0BnD7xtAp8a5y7eqcGVdU3w2E4t0PMg7SbX28H6zSbwfu-niydKElXTZDOBj_fOZKb0SatxFc3MjR6wsZg",
                    "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjhDRDlERTQ2QzEyRTVEQ0MyOTE1QkVBNDY2MzNENDE2IiwidHlwIjoiYXQrand0In0.eyJuYmYiOjE3MzczMTgyNjksImV4cCI6MTczNzMyMTg2OSwiaXNzIjoiaHR0cHM6Ly91YWMubWV0YS5zaGFyaWYuaXIiLCJjbGllbnRfaWQiOiJMYWJzQ2xpZW50Iiwic3ViIjoiMGE4MTg3MTUtZTgyNS00MjBlLThkMGYtYWU1OGI3Mjk1MzViIiwiYXV0aF90aW1lIjoxNzM3MzE4MjQ5LCJpZHAiOiJsb2NhbCIsIkNsaWVudHMiOiIiLCJVc2VyVHlwZSI6IlJlYWwiLCJVc2VybmFtZSI6IjQ3MjM2ODY1MDkiLCJGaXJzdE5hbWUiOiLYp9iz2K_Yp9mE2YciLCJSb2xlcyI6IiIsIk5hdGlvbmFsQ29kZSI6IjQ3MjM2ODY1MDkiLCJTaGFyaWZJZCI6ImthbGFudGFyaWFuIiwiTGFzdE5hbWUiOiLaqdmE2KfZhtiq2LHbjNin2YYiLCJzaWQiOiJDMzBEQUU2RkMyNzY5MDAxOTczQjlCQzU4NDBBQjdGMyIsImlhdCI6MTczNzMxODI2OSwic2NvcGUiOlsib3BlbmlkIiwicHJvZmlsZSJdLCJhbXIiOlsicHdkIl19.k-_j8G7lfR2mfLVIhPHeqV_bBnO-HwIgV_TAer2hoSBnihLauXcdM7gg7URse-idVbV5nDv-gVcaYaZDyXM8GDcrwuqfu1Zz1b0JS0q9AK8USn7GqozE0e961530rR437aRuwsFhKF9ewYvHZObRl4X1SGDYauGrMATQr1fTMEVUyWDWB-JWFshUaW2EVqcavUCcuHeuj2nOEbfqi2McaB11boJiy0z2xQyL5DUClLZD-5s-Dbk6LQlrUrrVEBCWv87jKkl4U0r9bGvWwnBIGpykfYQctNYrtxBFISD1HmlyXalmrxhsyX2AQTaPa97oLsOSCkNO4z1jjPj0jMxQbw",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "openid profile"
                },
                "message": "Request successful"
            }

        else:
            return {"error": f"Failed to exchange token code: {auth_code}, verifier: {code_verifier}", "status_code": response.status_code, "response": response.text}

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


def decode_jwt(token):
    """
    دیکد کردن `JWT Token` بدون نیاز به کلید عمومی
    """
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        return decoded_token
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.DecodeError:
        return {"error": "Failed to decode token"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


class SSOVerifyView(APIView):

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        code = request.GET.get("code")
        # scope = request.GET.get("scope")
        code_verifier = request.GET.get("code_verifier")
        if not code or not code_verifier:
            return Response(
                {"error": "Missing required parameter. (code is required)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        token_response = exchange_token(code, code_verifier)

        if "access_token" in token_response:
            access_token = token_response["access_token"]
            id_token = token_response.get("id_token")

            decoded_access_token = decode_jwt(access_token)
            decoded_id_token = decode_jwt(id_token) if id_token else None

            national_code = decoded_id_token.get("NationalCode") if decoded_id_token else None
            username = decoded_id_token.get("Username") if decoded_id_token else None

            user_auth_token = None

            if username or national_code:
                user = User.objects.filter(national_id=username).first()
                # user = User.objects.filter(national_id=national_code).first()
                # user2 = User.objects.filter(national_id=username).first()
                if user:
                    token, _ = Token.objects.get_or_create(user=user)
                    user_auth_token = token.key
                # elif user2:
                #     token, _ = Token.objects.get_or_create(user=user)
                #     user_auth_token = token.key

            response_data = {
                "sso_access_token": access_token,
                "sso_id_token": id_token,
                "decoded_access_token": decoded_access_token,
                "decoded_id_token": decoded_id_token,
                "national_code": national_code,
                "username": username,
                "user_auth_token": user_auth_token
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(token_response, status=status.HTTP_400_BAD_REQUEST)


class CustomerUserPubListAPIView(ListAPIView):
    queryset = User.objects.filter(user_type='customer')
    serializer_class = SummaryUserSerializer
    search_fields = ['username', 'email', 'national_id', 'company_national_id', 'company_name', 'company_economic_number', 'first_name', 'last_name']
    filterset_class = UserFilter

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_user']
    view_key = 'user'


class StaffUserPubListAPIView(ListAPIView):
    queryset = User.objects.filter(user_type='staff')
    serializer_class = SummaryUserSerializer
    search_fields = ['username', 'email', 'national_id', 'company_national_id', 'company_name', 'company_economic_number', 'first_name', 'last_name']
    filterset_class = UserFilter

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_user']
    view_key = 'user'


class UserTeacherListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSummerySerializer
    search_fields = ['username', 'email', 'national_id', 'company_national_id', 'company_name', 'company_economic_number', 'first_name', 'last_name']
    filterset_class = UserFilter

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.filter(role__role_key='teacher')
        return queryset


class UserStaffListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'national_id', 'company_national_id', 'company_name', 'company_economic_number', 'first_name', 'last_name']
    filterset_class = UserFilter
    pagination_class = DefaultPagination

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_user']
    view_key = 'user'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = User.objects.filter(user_type='staff')
        return queryset

    def handle_export_excel(self, queryset):
        file_url = export_excel(queryset)
        if file_url:
            full_url = self.request.build_absolute_uri(file_url)
            return Response({'file_url': full_url})  # full_url.replace('http://', 'https://')})
        return Response({'error': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.query_params.get('export_excel', 'False').lower() == 'true':
            return self.handle_export_excel(queryset)

        return super().get(request, *args, **kwargs)


class UserCustomerListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'national_id', 'company_national_id', 'company_name', 'company_economic_number', 'first_name', 'last_name']
    filterset_class = UserFilter
    pagination_class = DefaultPagination

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_user']
    view_key = 'user'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = User.objects.filter(user_type='customer')
        return queryset

    def handle_export_excel(self, queryset):
        file_url = export_excel(queryset)
        if file_url:
            full_url = self.request.build_absolute_uri(file_url)
            return Response({'file_url': full_url})  # full_url.replace('http://', 'https://')})
        return Response({'error': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.query_params.get('export_excel', 'False').lower() == 'true':
            return self.handle_export_excel(queryset)

        return super().get(request, *args, **kwargs)


class UserListAPIView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'national_id', 'company_national_id', 'company_name', 'company_economic_number', 'first_name', 'last_name']
    filterset_class = UserFilter
    pagination_class = DefaultPagination

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_user', 'view_owner_user', 'create_all_user']
    view_key = 'user'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = User.objects.all()
        elif filter_key == 'owner':
            # queryset = User.objects.filter(user_type='staff')
            queryset = User.objects.filter(role__id__in=[10])
        return queryset

    # def get(self, request, *args, **kwargs):
    #     get_list = self.list(request, *args, **kwargs)
    #     if self.request.query_params.get('export_excel', 'False').lower() == 'true':
    #         file_url = export_excel(get_list.data.serializer.instance)
    #         if file_url:
    #             full_url = self.request.build_absolute_uri(file_url)
    #             return Response({'file_url': full_url})
    #         return Response({'error': 'Export failed'}, status=500)
    #     else:
    #         return get_list
    #

    def handle_export_excel(self, queryset):
        file_url = export_excel(queryset)
        if file_url:
            full_url = self.request.build_absolute_uri(file_url)
            return Response({'file_url': full_url})  # full_url.replace('http://', 'https://')})
        return Response({'error': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.query_params.get('export_excel', 'False').lower() == 'true':
            return self.handle_export_excel(queryset)

        return super().get(request, *args, **kwargs)


class UserDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_user', 'view_owner_user', 'update_all_user', 'update_owner_user', 'delete_all_user', 'delete_owner_user']
    view_key = 'user'


class UserDetailPasswordAPIView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserPasswordSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_user', 'view_owner_user', 'update_all_user', 'update_owner_user', 'delete_all_user', 'delete_owner_user']
    view_key = 'user'


class UserProfileAPIView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class UserProfilePasswordAPIView(UpdateAPIView):
    serializer_class = UserPasswordSerializer

    def get_object(self):
        return self.request.user


# class UserRegistrationAPIView(CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserRegistrationSerializer


class UserPersonalRegistrationAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserPersonalSerializer


class UserBusinessRegistrationAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserBusinessSerializer


class ObtainAuthToken(ObtainAuthT):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    # serializer_class = AuthTokenSerializer
    serializer_class = UPOAuthTokenSerializer

    if coreapi_schema.is_enabled():
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="username",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Username",
                        description="Valid username for authentication",
                    ),
                ),

                coreapi.Field(
                    name="password",
                    required=False,
                    location='form',
                    schema=coreschema.String(
                        title="Password",
                        description="Valid password for authentication",
                    ),
                ),

                coreapi.Field(
                    name="otp",
                    required=False,
                    location='form',
                    schema=coreschema.String(
                        title="OTP",
                        description="Valid otp for authentication",
                    ),
                ),
            ],
            encoding="application/json",
        )

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        user.last_login = datetime.datetime.now()
        user.save()

        linked_business_accounts = UserBusinessLinkedAccountsSerializer(instance=user.linked_to_users.all().first())

        return Response({'token': token.key,
                         'name': user.get_full_name(),
                         'user_type': user.user_type,
                         'user_id': user.id,
                         'role': self.role(user),
                         'business_accounts': linked_business_accounts.data,
                         })

        # return Response({'token': token.key})

    # def post(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     user = serializer.validated_data['user']
    #     token, created = Token.objects.get_or_create(user=user)
    #         # return Response({'token': token.key})
    #     # except:
    #         # username = serializer.initial_data['username']
    #         # user = User.objects.create(username=username)
    #         # user.set_password('A12345678a')
    #         # user.save()
    #         # serializer = self.get_serializer(data=request.data)
    #         # serializer.is_valid(raise_exception=True)
    #         # user = serializer.validated_data['user']
    #         # token, created = Token.objects.get_or_create(user=user)
    #     if user.profile.pic:
    #         pic = request.build_absolute_uri(user.profile.pic.url)
    #     else:
    #         pic = ""
    #     return Response({'token': token.key,
    #                      'name': user.get_full_name(),
    #                      'user_id': user.id,
    #                      'profile_id': user.profile.id,
    #                      'profile_code': user.profile.code,
    #                      'pic': pic,
    #                      'role': self.role(user),
    #                      })
    #
    # def put(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #
    #     username = serializer.initial_data['username']
    #     user, created = User.objects.get_or_create(username=username)
    #     code = str(random.randint(10000, 99999))
    #     user.set_password(code)
    #     user.save()
    #
    #     url = self.sms_url(user, code)
    #     response = requests.get(url)
    #
    #     return Response({'status': response.content})
    #
    # def sms_url(self, user, code):
    #     form = '50001259'
    #     to = str(user.username)
    #     # to = '09381029915'
    #     username = 'armandavari'
    #     password = 'A12345678a'
    #     text = f'کد ورود شما: {code} \n\nبانک اطلاعات مجردین'
    #     return f'http://tsms.ir/url/tsmshttp.php?from={form}&to={to}&username={username}&password={password}&message={text}'

    def role(self, user):
        try:
            return user.groups.all().first().name
        except AttributeError:
            return 'user'


obtain_auth_token = ObtainAuthToken.as_view()


class GetCurrentUserView(RetrieveAPIView):
    """
    Gives the basic info of the current user.
    """
    # permission_classes = [HasViewAccess, Authenticated]
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LabsnetListView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs.get('user_id')) if 'user_id' in kwargs else request.user

        if not user.national_id:
            raise PermissionDenied("User does not have a valid national ID.")

        labsnet_result = user.labsnet_list()

        user.sync_labsnet_credits(labsnet_result)

        return Response({"labsnet_result": labsnet_result})

class EducationalFieldListAPIView(ListCreateAPIView):
    queryset = EducationalField.objects.all()
    serializer_class = EducationalFieldSerializer


class EducationalFieldDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = EducationalField.objects.all()
    serializer_class = EducationalFieldSerializer


class EducationalLevelListAPIView(ListCreateAPIView):
    queryset = EducationalLevel.objects.all()
    serializer_class = EducationalLevelSerializer


class EducationalLevelDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = EducationalLevel.objects.all()
    serializer_class = EducationalLevelSerializer


class DepartmentListAPIView(ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class RoleListAPIView(ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class RoleDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class AccessLevelListAPIView(ListCreateAPIView):
    queryset = AccessLevel.objects.all()
    serializer_class = AccessLevelSerializer


class AccessLevelDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = AccessLevel.objects.all()
    serializer_class = AccessLevelSerializer


class GrantTransactionListAPIView(ListCreateAPIView):
    queryset = GrantTransaction.objects.all()
    serializer_class = GrantTransactionSerializer


    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_granttransaction', 'view_owner_granttransaction', 'create_all_granttransaction']
    view_key = 'granttransaction'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = GrantTransaction.objects.all()
        elif filter_key == 'owner':
            queryset = GrantTransaction.objects.filter(sender=self.request.user) | GrantTransaction.objects.filter(receiver=self.request.user)
        return queryset.distinct()


class GrantTransactionDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = GrantTransaction.objects.all()
    serializer_class = GrantTransactionSerializer


    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_granttransaction', 'view_owner_granttransaction', 'update_all_granttransaction', 'update_owner_granttransaction', 'delete_all_granttransaction', 'delete_owner_granttransaction']
    view_key = 'granttransaction'


class GrantRecordUploadAPIView(CreateAPIView):
    serializer_class = GrantRecordFileSerializer

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file', None)
        if not file or not isinstance(file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            return Response({"error": "No file provided or file is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            created_records = process_excel_and_create_grant_records(file)
            return Response({"detail": f"{len(created_records)} records created successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GrantRecordListAPIView(ListCreateAPIView):
    queryset = GrantRecord.objects.all()
    serializer_class = GrantRecordSerializer
    filterset_class = GrantRecordFilter

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_grantrecord', 'view_owner_grantrecord', 'create_all_grantrecord']
    view_key = 'grantrecord'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = GrantRecord.objects.all()
        elif filter_key == 'owner':
            queryset = GrantRecord.objects.filter(receiver=self.request.user)
        return queryset.distinct()

    def post(self, request, *args, **kwargs):
        serializer = GrantRecordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            created_records = serializer.save()
            if isinstance(created_records, list):
                return Response({"detail": f"{len(created_records)} records created successfully."},
                                status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GrantRecordDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = GrantRecord.objects.all()
    serializer_class = GrantRecordSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_grantrecord', 'view_owner_grantrecord', 'update_all_grantrecord', 'update_owner_grantrecord', 'delete_all_grantrecord', 'delete_owner_grantrecord']
    view_key = 'grantrecord'

class GrantRequestListAPIView(ListCreateAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestSerializer
    filterset_class = GrantRequestFilter

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_grantrequest', 'view_owner_grantrequest', 'create_all_grantrequest']
    view_key = 'grantrequest'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = GrantRequest.objects.all()
        elif filter_key == 'owner':
            queryset = GrantRequest.objects.filter(sender=self.request.user) | GrantRequest.objects.filter(receiver=self.request.user)
        return queryset.distinct()
    #
    # def get(self, request, *args, **kwargs):
    #     get_list = self.list(request, *args, **kwargs)
    #     if self.request.query_params.get('export_excel', 'False').lower() == 'true':
    #         file_url = export_excel(get_list.data.serializer.instance)
    #         if file_url:
    #             full_url = self.request.build_absolute_uri(file_url)
    #             return Response({'file_url': full_url})
    #         return Response({'error': 'Export failed'}, status=500)
    #     else:
    #         return get_list

    def handle_export_excel(self, queryset):
        file_url = export_excel(queryset)
        if file_url:
            full_url = self.request.build_absolute_uri(file_url)
            return Response({'file_url': full_url})  # full_url.replace('http://', 'https://')})
        return Response({'error': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.query_params.get('export_excel', 'False').lower() == 'true':
            return self.handle_export_excel(queryset)

        return super().get(request, *args, **kwargs)


class GrantRequestDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestSerializer


    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_grantrequest', 'view_owner_grantrequest', 'update_all_grantrequest', 'update_owner_grantrequest', 'delete_all_grantrequest', 'delete_owner_grantrequest']
    view_key = 'grantrequest'


class GrantRequestApprovedAPIView(UpdateAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestApprovedSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['update_all_grantrequest', 'update_owner_grantrequest']
    view_key = 'grantrequest'


class GrantRequestRevokedAPIView(UpdateAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestRevokeSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['update_all_grantrequest', 'update_owner_grantrequest']
    view_key = 'grantrequest'


# class CheckLabsnetGrantAPIView(CreateAPIView):
#     serializer_class = LansnetGrantSerializer
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         sdata = serializer.validated_data
#         response = labsnet(sdata['national_id'], sdata['type'], sdata['services'])
#         return response


class OwnedGrantRecordListAPIView(ListCreateAPIView):
    queryset = GrantRecord.objects.all()
    serializer_class = GrantRecordSerializer
    filterset_class = GrantRecordFilter

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_owner_grantrecord', 'create_all_grantrecord']
    view_key = 'grantrecord'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = GrantRecord.objects.all()
        elif filter_key == 'owner':
            queryset = GrantRecord.objects.filter(receiver=self.request.user)
        return queryset.distinct()

    def post(self, request, *args, **kwargs):
        serializer = GrantRecordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            created_records = serializer.save()
            if isinstance(created_records, list):
                return Response({"detail": f"{len(created_records)} records created successfully."},
                                status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OwnedGrantRecordDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = GrantRecord.objects.all()
    serializer_class = GrantRecordSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_owner_grantrecord', 'update_owner_grantrecord', 'delete_owner_grantrecord']
    view_key = 'grantrecord'


class OwnedGrantRequestListAPIView(ListCreateAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestSerializer
    filterset_class = GrantRequestFilter

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_owner_grantrequest', 'create_all_grantrequest']
    view_key = 'grantrequest'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        today = datetime.date.today()
        if filter_key == 'all':
            queryset = GrantRequest.objects.all()
        elif filter_key == 'owner':
            qs = GrantRequest.objects.filter(expiration_date__gte=today)
            queryset = qs.filter(sender=self.request.user) | qs.filter(receiver=self.request.user)
        return queryset.distinct()


class OwnedGrantRequestDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_owner_grantrequest', 'update_owner_grantrequest', 'delete_owner_grantrequest']
    view_key = 'grantrequest'


class OwnedGrantRequestApprovedAPIView(UpdateAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestApprovedSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['update_owner_grantrequest']
    view_key = 'grantrequest'


class OwnedGrantRequestRevokedAPIView(UpdateAPIView):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestRevokeSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['update_owner_grantrequest']
    view_key = 'grantrequest'


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import OTPRequestSerializer, OTPVerificationSerializer
from django.utils.crypto import get_random_string
from django.conf import settings
import requests


class OTPRequestView(APIView):
    serializer_class = OTPRequestSerializer

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            user = User.objects.get(username=phone_number)
            otp_code = get_random_string(length=6, allowed_chars='0123456789')
            message = f"کد یکبار مصرف: {otp_code}"
            user.OTP = otp_code
            user.save()
            otp_server = OTPserver.objects.all().first()
            result = otp_server.send_quick_message([phone_number], message)

            if 0 <= result['statusCode'] <= 4:
                return Response({"detail": f"کد ارسال شد.", "message": result['message']}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "خطا در ارسال کد یکبارمصرف.", "message": result['message']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    serializer_class = OTPVerificationSerializer

    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']

            # Check if OTP code exists in the database
            try:
                user = User.objects.get(username=phone_number)
                if user.OTP == otp_code:
                    user.set_password(new_password)
                    user.save()
                    return Response({"detail": "اعتبارسنجی با موفقیت انجام شد. پسورد تغییر کرد."}, status=status.HTTP_200_OK)
                else:
                    return Response({"detail": "کد اشتباه بود."}, status=status.HTTP_400_BAD_REQUEST)

            except User.DoesNotExist:
                return Response({"detail": "تلفن همراه در سامانه وجود ندارد."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# class SMSService():
#     def __init__(self):
#         self.username = ''
#         self.password = ''
#         self.base_url = ''
#
#     def send_sms(self, phone_number, message):
#         payload = {
#             'from': settings.SMS_SENDER_ID,
#             'to': phone_number,
#             'text': message,
#         }
#         response = requests.post(settings.SMS_API_URL, data=payload,
#                                  auth=(settings.SMS_USERNAME, settings.SMS_PASSWORD))
#         if response.status_code == 200:
#             return True
#         else:
#             return False
#
#     def auth_login(self):
#         response = requests.post(settings.SMS_API_URL, data=payload,
#                                  auth=(settings.SMS_USERNAME, settings.SMS_PASSWORD))


class NotificationList(ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    # permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    filterset_fields = {
                        'user': ['exact', 'in'],
                        'title': ['contains'],
                        'content': ['contains'],
                        'type': ['exact', 'in'],
                        'is_read': ['exact'],
                        'created_at': ['gt', 'lt', 'gte', 'lte'],
    }

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_owner_notification']
    view_key = 'notification'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = Notification.objects.all().order_by('-created_at')
        elif filter_key == 'owner':
            queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at')
        return queryset


class NotificationCreate(CreateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    # permission_classes = [IsAuthenticated, IsExpertOrAdminOrManager]

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['create_all_notification']
    view_key = 'notification'


class NotificationReadDetail(UpdateAPIView):
    serializer_class = NotificationReadSerializer
    # permission_classes = [IsAuthenticated, IsOwnerProfileOnly]

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['update_owner_notification']
    view_key = 'notification'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = Notification.objects.all()
        elif filter_key == 'owner':
            queryset = Notification.objects.filter(user=self.request.user)
        return queryset


class NotificationReadAllList(ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    # permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    filterset_fields = {
                        'user': ['exact', 'in'],
                        'title': ['contains'],
                        'content': ['contains'],
                        'type': ['exact', 'in'],
                        'is_read': ['exact'],
                        'created_at': ['gt', 'lt', 'gte', 'lte'],
    }
    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_owner_notification']
    view_key = 'notification'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = Notification.objects.all().order_by('-created_at')
        elif filter_key == 'owner':
            queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at')

        # read all
        queryset.update(is_read=True)

        return queryset


class NotificationDetail(RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    # permission_classes = [IsAuthenticated, IsOwnerProfile]


    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_owner_notification', 'update_owner_notification', 'delete_owner_notification']
    view_key = 'notification'

