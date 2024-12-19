from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def pagination_helper(data, page, page_size=100):
    paginator = Paginator(data, page_size)

    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    return data
