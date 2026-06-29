from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView, RetrieveAPIView, \
    RetrieveUpdateAPIView, get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.account.permissions import AccessLevelPermission, query_set_filter_key
from apps.core.functions import export_excel
from apps.core.paginations import DefaultPagination
from apps.lab.api.filters import ParameterFilter, FormResponseFilter, LaboratoryFilter, RequestFilter, DeviceFilter, \
    ExperimentFilter
from apps.lab.models import Experiment, Laboratory, Device, Parameter, Request, Department, FormResponse, LabType, \
    Status, Workflow, RequestResult, ISOVisibility, RequestCertificate
from apps.lab.api.serializers import ExperimentSerializer, LaboratorySerializer, DeviceSerializer, ParameterSerializer, \
    RequestListSerializer, RequestDetailSerializer, DepartmentSerializer, LaboratoryDetailSerializer, \
    ExperimentDetailSerializer, \
    FormResponseSerializer, LabTypeSerializer, RequestChangeStatusSerializer, WorkflowSerializer, \
    RequestResultSerializer, RequestButtonActionSerializer, RequestCertificateSerializer, UpdateLaboratoryISOSerializer, \
    RequestUpdateSerializer, ISOVisibilitySerializer, CertificateSerializer
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.utils import timezone

class ExperimentPubListAPIView(ListAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    filterset_class = ExperimentFilter


class ExperimentPubDetailAPIView(RetrieveAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentDetailSerializer


class ParameterPubListAPIView(ListCreateAPIView):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    filterset_class = ParameterFilter


class ParameterPubDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer


class ExperimentListAPIView(ListCreateAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    filterset_class = ExperimentFilter

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_experiment', 'view_owner_experiment', 'create_all_experiment']
    view_key = 'experiment'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = Experiment.objects.none()
        if filter_key == 'all':
            queryset = Experiment.objects.all()
        elif filter_key == 'owner':
            queryset = Experiment.objects.filter(laboratory__technical_manager=self.request.user) | Experiment.objects.filter(laboratory__operators=self.request.user)
        return queryset.distinct()


class ExperimentDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentDetailSerializer

    # permission and queryset
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_experiment', 'view_owner_experiment', 'update_all_experiment', 'update_owner_experiment', 'delete_all_experiment', 'delete_owner_experiment']
    view_key = 'experiment'


class LaboratoryListAPIView(ListCreateAPIView):
    queryset = Laboratory.objects.all()
    serializer_class = LaboratorySerializer
    filterset_class = LaboratoryFilter

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_laboratory', 'view_owner_laboratory', 'create_all_laboratory']
    view_key = 'laboratory'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = Laboratory.objects.none()
        if filter_key == 'all':
            queryset = Laboratory.objects.all()
        elif filter_key == 'owner':
            queryset = Laboratory.objects.filter(technical_manager=self.request.user) | Laboratory.objects.filter(operators=self.request.user)
        return queryset.distinct()


class LaboratoryDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Laboratory.objects.all()
    serializer_class = LaboratoryDetailSerializer

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_laboratory', 'view_owner_laboratory', 'update_all_laboratory', 'update_owner_laboratory', 'delete_all_laboratory']
    view_key = 'laboratory'


class LaboratoryPubListAPIView(ListAPIView):
    queryset = Laboratory.objects.all()
    serializer_class = LaboratorySerializer
    filterset_class = LaboratoryFilter


class LaboratoryPubDetailAPIView(RetrieveAPIView):
    queryset = Laboratory.objects.all()
    serializer_class = LaboratoryDetailSerializer


class DeviceListAPIView(ListCreateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    filterset_class = DeviceFilter

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_device', 'view_owner_device', 'create_all_device']
    view_key = 'device'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = Device.objects.none()
        if filter_key == 'all':
            queryset = Device.objects.all()
        elif filter_key == 'owner':
            queryset = Device.objects.filter(laboratory__technical_manager=self.request.user) | Device.objects.filter(laboratory__operators=self.request.user)
        return queryset.distinct()


class DeviceDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    
    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_device', 'view_owner_device', 'update_all_device', 'update_owner_device', 'delete_all_device', 'delete_owner_device']
    view_key = 'device'


class ParameterListAPIView(ListCreateAPIView):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    filterset_class = ParameterFilter

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_parameter', 'view_owner_parameter', 'create_all_parameter']
    view_key = 'parameter'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(), self.required_access_levels, self.request.method)
        queryset = Parameter.objects.none()
        if filter_key == 'all':
            queryset = Parameter.objects.all()
        elif filter_key == 'owner':
            queryset = Parameter.objects.filter(experiment__laboratory__technical_manager=self.request.user) | Parameter.objects.filter(experiment__laboratory__operators=self.request.user)
        return queryset.distinct()
    

class ParameterDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_parameter', 'view_owner_parameter', 'update_all_parameter', 'update_owner_parameter',
                              'delete_all_parameter', 'delete_owner_parameter']
    view_key = 'parameter'


class RequestListAPIView(ListCreateAPIView):
    queryset = Request.objects.all().order_by('-created_at')
    serializer_class = RequestListSerializer
    search_fields = ['username', 'email', 'national_id', 'company_national_id', 'company_name',
                     'company_economic_number', 'first_name', 'last_name']
    filterset_class = RequestFilter
    pagination_class = DefaultPagination
    ordering = ('created_at',)

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_request', 'view_owner_request', 'create_all_request',
                              # 'view_receptor_request', 'view_operator_request'
                              ]
    view_key = 'request'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(),
                                          self.required_access_levels, self.request.method)
        queryset = []
        if filter_key == 'all':
            queryset = Request.objects.filter(is_completed=True, has_parent_request=False, has_prepayment=False)
        elif filter_key == 'owner':
            queryset = Request.objects.filter(is_completed=True, has_parent_request=False, has_prepayment=False, experiment__laboratory__technical_manager=self.request.user) | Request.objects.filter(is_completed=True, has_parent_request=False, experiment__laboratory__operators=self.request.user)
        # elif filter_key == 'receptor':
        #     queryset = Request.objects.filter(is_completed=True)
        #         # .exclude(request_status__step__name__in=['در حال انجام', 'تکمیل شده', 'رد شده'])
        # elif filter_key == 'operator':
        #     queryset = Request.objects.filter(is_completed=True, experiment__laboratory__technical_manager=self.request.user) | Request.objects.filter(is_completed=True, experiment__laboratory__operator=self.request.user)
        #         # .exclude(request_status__step__name__in=['در انتظار بررسی', 'در انتظار پرداخت', 'در ‌انتظار نمونه'])
        return queryset.distinct()

    # def get(self, request, *args, **kwargs):
    #     get_list = self.list(request, *args, **kwargs)
    #     if self.request.query_params.get('export_excel', 'False').lower() == 'true':
    #         ids = [r.id for r in get_list.data['results'].serializer.instance]
    #         qs = Request.objects.filter(id__in=ids)
    #         file_url = export_excel(qs)
    #         if file_url:
    #             full_url = self.request.build_absolute_uri(file_url)
    #             return Response({'file_url': full_url})
    #         return Response({'error': 'Export failed'}, status=500)
    #     elif self.request.query_params.get('step_counter', 'False').lower() == 'true':
    #         ids = [r.id for r in get_list.data['results'].serializer.instance]
    #         qs = Request.objects.filter(id__in=ids)
    #         # qs = get_list.data['results'].serializer.instance
    #         try:
    #             step_list = []
    #             for step in qs[0].request_status.all().first().step.workflow.steps.all():
    #                 step_dict = {
    #                     'id': step.id,
    #                     'name': step.name,
    #                     'step_color': step.next_button_color,
    #                     # 'request_counter': qs.filter(request_status__id=step.id, request_status__accept=False, request_status__reject=False).count()
    #                     'request_counter': qs.filter(request_status__step__id=step.id, request_status__accept=False,
    #                                                  request_status__reject=False).count()
    #                 }
    #                 step_list.append(step_dict)
    #             return Response(step_list)
    #         except:
    #             return Response({'error': 'request failed'}, status=500)
    #     else:
    #         return get_list

    def handle_export_excel(self, queryset):
        file_url = export_excel(queryset)
        if file_url:
            full_url = self.request.build_absolute_uri(file_url)
            return Response({'file_url': full_url})  # full_url.replace('http://', 'https://')})
        return Response({'error': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_step_counter(self, queryset):
        try:
            step_list = []
            if queryset.exists():
                workflow_steps = queryset[0].request_status.all().first().step.workflow.steps.all()
                for step in workflow_steps:
                    step_list.append({
                        'id': step.id,
                        'name': step.name,
                        'step_color': step.step_color,
                        'request_counter': queryset.filter(
                            request_status__step__id=step.id,
                            request_status__accept=False,
                            request_status__reject=False
                        ).count()
                    })
            return Response(step_list)
        except Exception as e:
            return Response({'error': f'Step counter calculation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.query_params.get('export_excel', 'False').lower() == 'true':
            return self.handle_export_excel(queryset)

        if request.query_params.get('step_counter', 'False').lower() == 'true':
            return self.handle_step_counter(queryset)

        return super().get(request, *args, **kwargs)

class RequestDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestDetailSerializer

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_request', 'view_owner_request', 'update_all_request', 'update_owner_request',
                              'delete_all_request', 'delete_owner_request']
         # 'update_receptor_request', 'view_receptor_request', 'update_operator_request', 'view_operator_request'
    view_key = 'request'


class UpdateRequestLabsnetView(UpdateAPIView):
    """
    API endpoint to update labsnet1 and labsnet2 fields of a Request object.
    """
    permission_classes = [IsAuthenticated]
    queryset = Request.objects.all()
    serializer_class = RequestUpdateSerializer

    def get_object(self):
        """
        Get the request object based on the provided pk in the URL.
        """
        request_obj = get_object_or_404(Request, pk=self.kwargs["pk"])
        return request_obj


class UpdateRequestRecalculateView(APIView):

    def patch(self, request, *args, **kwargs):
        request_id = kwargs.get('pk')
        req_obj = get_object_or_404(Request, id=request_id)

        try:
            req_obj.set_price()
            return Response({"message": "محاسبه مجدد قیمت با موفقیت انجام شد."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"خطا در محاسبه قیمت: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateRequestResendLabsnetView(APIView):

    def patch(self, request, *args, **kwargs):
        request_id = kwargs.get('pk')
        req_obj = get_object_or_404(Request, id=request_id)

        try:
            if req_obj.lastest_status().step.name == 'در ‌انتظار نمونه':
                if not req_obj.parent_request and not req_obj.labsnet:
                    req_obj.labsnet_create()
                    req_obj.save()
            if req_obj.lastest_status().step.name == 'در انتظار پرداخت' and (req_obj.labsnet):
                if not req_obj.parent_request:
                    req_obj.labsnet_create_grant()
                    req_obj.save()
            return Response({"message": "ارسال مجدد انجام شد."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"خطا در ارسال: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)



class RequestCertificateAPIView(RetrieveAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestCertificateSerializer

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_request', 'view_owner_request']
    view_key = 'request'


class URequestCertificateAPIView(UpdateAPIView):
    queryset = RequestCertificate.objects.all()
    serializer_class = CertificateSerializer

    def get_object(self):
        request_obj = get_object_or_404(Request, pk=self.kwargs["pk"])
        return request_obj.certificate


class RequestChangeStatusAPIView(UpdateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestButtonActionSerializer
    # serializer_class = RequestChangeStatusSerializer

    # def get_queryset(self):
    #     return self.request.user.requests.all()

class OwnedRequestListAPIView(ListCreateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestListSerializer
    pagination_class = DefaultPagination


    def get_queryset(self):
        limited = timezone.now() - timedelta(days=2)
        user_requests = self.request.user.requests.filter(is_completed=True, has_parent_request=False) | self.request.user.requests.filter(is_completed=False, has_parent_request=False, child_requests__isnull=False, created_at__gte=limited)
        return user_requests.distinct().order_by('-created_at')

class OwnedRequestDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestDetailSerializer

    def get_queryset(self):
        limited = timezone.now() - timedelta(days=2)
        user_requests = self.request.user.requests.filter(is_completed=True, has_parent_request=False) | self.request.user.requests.filter(is_completed=False, has_parent_request=False, child_requests__isnull=False, created_at__gte=limited)
        return user_requests.distinct().order_by('-created_at')


class DepartmentListAPIView(ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class LabTypeListAPIView(ListCreateAPIView):
    queryset = LabType.objects.all()
    serializer_class = LabTypeSerializer


class LabTypeDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = LabType.objects.all()
    serializer_class = LabTypeSerializer


class FormResponseListAPIView(ListCreateAPIView):
    queryset = FormResponse.objects.all()
    serializer_class = FormResponseSerializer
    filterset_class = FormResponseFilter

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.request:
            instance.request.set_price()


class FormResponseDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = FormResponse.objects.all()
    serializer_class = FormResponseSerializer


    def perform_destroy(self, instance):
        request = instance.request
        instance.delete()
        if request:
            request.set_price()

    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     self.perform_destroy(instance)
    #     if instance.request:
    #         instance.request.set_price()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class WorkflowListAPIView(ListCreateAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer


class WorkflowDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer


class RequestResultAPIView(ListCreateAPIView):
    serializer_class = RequestResultSerializer
    queryset = RequestResult.objects.all()
    # permission_classes = [IsOwnerOfRequest]
    #
    # def get_queryset(self):
    #     return RequestResult.objects.filter(request__owner=self.request.user)

    # def perform_create(self, serializer):
    #     request_id = self.request.data.get('request')
    #     request_obj = Request.objects.get(id=request_id)
    #     if request_obj.owner != self.request.user:
    #         raise PermissionDenied("You do not have permission to add results to this request.")
    #     serializer.save()


class RequestResultDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = RequestResultSerializer
    queryset = RequestResult.objects.all()
    # permission_classes = [IsOwnerOfRequest]

    # def get_queryset(self):
    #     return RequestResult.objects.filter(request__owner=self.request.user)


class UpdateLaboratoryISOVisibilityAPIView(RetrieveUpdateAPIView):
    queryset = Laboratory.objects.all()
    serializer_class = UpdateLaboratoryISOSerializer


    def get(self, request, *args, **kwargs):
        laboratories = self.get_queryset()
        total_count = laboratories.count()
        true_count = laboratories.filter(is_visible_iso=True).count()
        majority_status = "True" if true_count > total_count / 2 else "False"

        return Response(
            {
                "majority_is_visible_iso": majority_status,
                "total_laboratories": total_count,
                "visible_iso_count": true_count,
                "hidden_iso_count": total_count - true_count,
            },
            status=status.HTTP_200_OK
        )

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_visible_iso = serializer.validated_data['is_visible_iso']
        self.get_queryset().update(is_visible_iso=is_visible_iso)
        return Response(
            {"message": f"is_visible_iso updated to {is_visible_iso} for all laboratories."},
            status=status.HTTP_200_OK
        )


class ISOVisibilityAPIView(RetrieveUpdateAPIView):
    serializer_class = ISOVisibilitySerializer

    def get_object(self):
        return ISOVisibility.get_instance()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)