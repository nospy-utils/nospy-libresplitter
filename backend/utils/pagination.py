def validate_pagination_request_params(request) -> Page:
    try:
        current_page = max(1, int(request.args.get("page", 1)))
        page_size = max(1, min(100, int(request.args.get("page_size", 20))))
        return Page(current_page, page_size)
    except ValueError:
        from services import UserInputValidationException
        raise UserInputValidationException("page and page_size must be integers.")

class Page(object):
    def __init__(self, current_page, page_size):
        self.current_page = current_page
        self.page_size = page_size