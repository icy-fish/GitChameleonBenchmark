import flask

app = flask.Flask('test')
@app.route('/data')
def data(num_set):
    return flask.jsonify({'numbers':num_set})

def eval(app, data_fn, num_set):
    with app.test_request_context():
        response = data_fn(num_set)
        return response.get_data(as_text=True)

def app_set_up(app: flask.Flask) -> None: 
    