from rest_framework.renderers import JSONRenderer
from rest_framework import status


class SLIMSJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):

        response = {}
        status_code = renderer_context['response'].status_code

        if status.is_success(status_code):
            response['status'] = 'success'
            response['data'] = data
            response['message'] = 'Request successful'
        else:
            response['status'] = 'error'
            response['errors'] = data
            response['message'] = 'Request failed'

        return super().render(response, accepted_media_type, renderer_context)

        # response = {}
        # check = ''
        # try:
        #     if 'errors' in data:
        #         check += '1'
        #         response['status'] = renderer_context['response'].status_code
        #         response['message'] = data['message']
        #         response['data'] = []
        #         response['errors'] = data['errors']
        #     else:
        #         check += '2'
        #         response['status'] = renderer_context['response'].status_code
        #         response['message'] = 'Request succeeded'
        #         response['data'] = data
        #         response['errors'] = []
        # except Exception as e:
        #     # if data is None and renderer_context['response'].status_code in [200, 201, 202, 203, 204]:
        #     if data is None:
        #         check += '3'
        #         response['status'] = renderer_context['response'].status_code
        #         response['message'] = 'Request succeeded'
        #         response['data'] = [data]
        #         response['errors'] = [e]
        #
        #     else:
        #         check += '4'
        #         response['status'] = 500
        #         response['message'] = 'Request failed'
        #         response['data'] = [data]
        #         response['errors'] = [e]
        # return super().render(response, accepted_media_type, renderer_context)
