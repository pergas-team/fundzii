from math import ceil

from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from rest_framework.response import Response


class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_count', ceil(self.page.paginator.count / self.page.paginator.per_page)),
            ('page_size', self.page.paginator.per_page),
            ('results', data),
        ]))

class ProfilePagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_count', ceil(self.page.paginator.count / self.page.paginator.per_page)),
            ('page_size', self.page.paginator.per_page),
            ('results', data),
        ]))

class PublicPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_count', ceil(self.page.paginator.count / self.page.paginator.per_page)),
            ('page_size', self.page.paginator.per_page),
            ('results', data),
        ]))
