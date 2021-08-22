from werkzeug.routing import Rule, Map
import views

url_patterns = Map([
    Rule("/", endpoint=''),
    Rule("/get_next_debit_view", endpoint=views.get_next_debit_view)
])
