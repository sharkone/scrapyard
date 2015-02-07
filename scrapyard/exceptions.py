class ScrapyardException(Exception):
    pass

class HTTPError(ScrapyardException):
    def __init__(self, status_code):
        super(ScrapyardException, self).__init__(str(status_code))
        self.status_code = status_code

class JSONError(ScrapyardException):
    def __init(self, url):
        super(ScrapyardException, self).__init__(url)
        self.url = url
