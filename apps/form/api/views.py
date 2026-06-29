from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from apps.account.permissions import AccessLevelPermission, query_set_filter_key
from apps.form.api.filters import FormFilter
from apps.form.api.serializers import FormSerializer
from apps.form.models import Form


class FormListAPIView(ListCreateAPIView):
    queryset = Form.objects.all()
    serializer_class = FormSerializer
    filterset_class = FormFilter

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_form', 'view_owner_form', 'create_all_form']
    view_key = 'form'

    def get_queryset(self):
        filter_key = query_set_filter_key(self.view_key, self.request.user.get_access_levels(),
                                          self.required_access_levels, self.request.method)

        if filter_key == 'all':
            return Form.objects.all()
        elif filter_key == 'owner':
            queryset = Form.objects.filter(experiments__laboratory__technical_manager=self.request.user) |\
                       Form.objects.filter(experiments__laboratory__operators=self.request.user) |\
                       Form.objects.filter(owner=self.request.user)
            return queryset.distinct()
        return Form.objects.none()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class FormDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Form.objects.all()
    serializer_class = FormSerializer

    # permission and filter param
    permission_classes = [AccessLevelPermission]
    required_access_levels = ['view_all_form', 'view_owner_form', 'update_all_form', 'update_owner_form',
                              'delete_all_form', 'delete_owner_form']
    view_key = 'form'
