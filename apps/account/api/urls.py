from django.urls import path, include
import django_cas_ng.views as django_cas_ng
from apps.account.api.views import *


urlpatterns = [
    path('', include('rest_framework.urls'), name='api_auth'),
    path('token-auth/', obtain_auth_token, name='api_auth'),
    path('sso/verify/', SSOVerifyView.as_view(), name='sso_verify'),
    # path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('register/personal/', UserPersonalRegistrationAPIView.as_view(), name='register_personal'),
    path('register/business/', UserBusinessRegistrationAPIView.as_view(), name='register_business'),
    path("current-user/", GetCurrentUserView.as_view(), name='get-current-user'),
    # path("current-user/access-levels", GetCurrentUserAccessLevelView.as_view(), name='get-current-user-acess-levels'),
    path('current-user/labsnet/', LabsnetListView.as_view(), name='current-user-labsnet-list'),
    path('users/<int:user_id>/labsnet/', LabsnetListView.as_view(), name='user-labsnet-list'),

    path('request-otp/', OTPRequestView.as_view(), name='request_otp'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify_otp'),

    path('users/customer/pub/', CustomerUserPubListAPIView.as_view(), name='customer-users-pub-list'),
    path('users/staff/pub/', StaffUserPubListAPIView.as_view(), name='staff-users-pub-list'),

    path('users/staff/', UserStaffListAPIView.as_view(), name='staff-users-list'),
    path('users/customer/', UserCustomerListAPIView.as_view(), name='customer-users-list'),
    path('users/teacher/', UserTeacherListAPIView.as_view(), name='teacher-users-list'),

    path('users/', UserListAPIView.as_view(), name='users-list'),
    path('users/<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('users/<int:pk>/password/', UserDetailPasswordAPIView.as_view(), name='user-detail-password'),

    path('users/my-profile/', UserProfileAPIView.as_view(), name='user-profile-detail'),
    path('users/my-profile/password/', UserDetailPasswordAPIView.as_view(), name='user-profile-password'),

    path('educational-fields/', EducationalFieldListAPIView.as_view(), name='requests-list'),
    path('educational-fields/<int:pk>/', EducationalFieldDetailAPIView.as_view(), name='request-detail'),

    path('educational-level/', EducationalLevelListAPIView.as_view(), name='educational_level-list'),
    path('educational-level/<int:pk>/', EducationalLevelDetailAPIView.as_view(), name='educational_level-detail'),

    path('department/', DepartmentListAPIView.as_view(), name='department-list'),
    path('department/<int:pk>/', DepartmentDetailAPIView.as_view(), name='department-detail'),

    path('role/', RoleListAPIView.as_view(), name='role-list'),
    path('role/<int:pk>/', RoleDetailAPIView.as_view(), name='role-detail'),

    path('access-level/', AccessLevelListAPIView.as_view(), name='access-level-list'),
    path('access-level/<int:pk>/', AccessLevelDetailAPIView.as_view(), name='access-level-detail'),

    path('grant-transaction/', GrantTransactionListAPIView.as_view(), name='grant-transaction-list'),
    path('grant-transaction/<int:pk>/', GrantTransactionDetailAPIView.as_view(), name='grant-transaction-detail'),

    path('grant-record/', GrantRecordListAPIView.as_view(), name='grant-record-list'),
    path('grant-record/<int:pk>/', GrantRecordDetailAPIView.as_view(), name='grant-record-detail'),
    path('grant-record/file/', GrantRecordUploadAPIView.as_view(), name='grant-record-file'),

    # path('grant-labsnet/', CheckLabsnetGrantAPIView.as_view(), name='grant-labsnet-list'),
    path('grant-request/', GrantRequestListAPIView.as_view(), name='grant-request-list'),
    path('grant-request/<int:pk>/', GrantRequestDetailAPIView.as_view(), name='grant-request-detail'),
    path('grant-request/<int:pk>/approved/', GrantRequestApprovedAPIView.as_view(), name='grant-request-detail-approved'),
    path('grant-request/<int:pk>/revoke/', GrantRequestRevokedAPIView.as_view(), name='grant-request-detail-revoked'),

    path('grant-record/owned/', OwnedGrantRecordListAPIView.as_view(), name='grant-record-list'),
    path('grant-record/owned/<int:pk>/', GrantRecordDetailAPIView.as_view(), name='grant-record-detail'),
    path('grant-request/owned/', GrantRequestListAPIView.as_view(), name='grant-request-list'),
    path('grant-request/owned/<int:pk>/', GrantRequestDetailAPIView.as_view(), name='grant-request-detail'),
    path('grant-request/owned/<int:pk>/approved/', GrantRequestApprovedAPIView.as_view(),
         name='grant-request-detail-approved'),
    path('grant-request/owned/<int:pk>/revoke/', GrantRequestRevokedAPIView.as_view(), name='grant-request-detail-revoked'),

    path("notification/", NotificationList.as_view(), name='notification-list'),
    path("notification/create/", NotificationCreate.as_view(), name='notification-create'),
    path("notification/<int:pk>/", NotificationDetail.as_view(), name='notification-detail'),
    path("notification/<int:pk>/read/", NotificationReadDetail.as_view(), name='notification-detail'),
    path("notification/read-all", NotificationReadAllList.as_view(), name='notification-list'),

    path('sso/', django_cas_ng.LoginView.as_view(), name='cas_ng_login'),
    path('slo/', django_cas_ng.LogoutView.as_view(), name='cas_ng_logout'),

]
