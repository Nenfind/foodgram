from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """
    Modified PageNumberPagination with word "limit"
    as a limiter for number of shown objects.
    """

    page_size_query_param = "limit"
