class Error29Exception(Exception):
    def __init__(self, message="Аккаунт превысил дневной лимит на запросы к api."):
        self.message = message
        super().__init__(self.message)


class Error6Exception(Exception):
    def __init__(self, message="Слишком много запросов к api за единицу времени. Допустимо 3 запроса в сек."):
        self.message = message
        super().__init__(self.message)


class Error13Exception(Exception):
    def __init__(self, message="Превышен обьем ответа. Допустимо не более 5 мб. в execute"):
        self.message = message
        super().__init__(self.message)
