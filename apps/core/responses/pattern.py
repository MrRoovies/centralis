# responses/response_pattern.py

class ResponsePattern:
    @staticmethod
    def success(field, messages):
        return {
            'success': True,
            'messages': {
               field: {f'success': messages}
            }
        }

    @staticmethod
    def error(field, messages):
        return {
            'success': False,
            'messages': {
                field: {'__all__': messages}
            }
        }

    @staticmethod
    def success_data(data):
        return {
            'success': True,
            'data': data
        }

    @staticmethod
    def sucess_update(action, field, messages):
        return {
            'success': True,
            'action': action,
            'messages': {
                field: {'success': messages }
            }
        }