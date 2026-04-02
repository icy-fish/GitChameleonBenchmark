import flask
import json
import numpy as np
app = flask.Flask('test1')
@app.route('/data')
def data(num_arr):
    return flask.jsonify({'numbers': num_arr})

def eval(app, data_fn, num_arr):
    with app.test_request_context():
        response = data_fn(num_arr)
        return response.get_data(as_text=False)

class MyCustomJSONHandler(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, np.ndarray):