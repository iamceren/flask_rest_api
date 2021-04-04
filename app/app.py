import asyncio, os, threading, time, logging, dash
import pandas as pd
import flask
from flask import Flask, jsonify, request, g
from kafka import KafkaProducer, KafkaConsumer
from models import *
import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
from db import *

server = Flask(__name__)

server.config['JSON_SORT_KEYS'] = False
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with server.app_context():
    db.init_app(server)
    db.create_all()
    db.session.add(Book(title="Suskunlar", author="İhsan Oktay ANAR"))
    db.session.add(Book(title="İnce Memed", author="Yaşar KEMAL"))
    db.session.add(Book(title="Somehow I Manage", author="Michael SCOTT"))
    db.session.commit()


def is_bad(data):
    if not 'title' in data or not 'author' in data or not data['title'].strip() or not data['author'].strip():
        return jsonify({
            'error': 'Bad Request',
            'message': 'Title or Author not given!'
        }), 400
    return False


def does_exist(id):
    if not Book.query.filter_by(id=id).scalar():
        return {
                   'message': "Book with this id doesn't exist!"
               }, 404
    return True


@server.before_request
def before_request():
    g.start_time = time.time()


@server.after_request
def after_request(response):
    now = time.time()
    elapsed = int(round(1000 * (now - g.start_time)))

    logging.basicConfig(filename='demo.log', level=logging.DEBUG, format='%(message)s')
    logging.getLogger('werkzeug').disabled = True
    logging.getLogger("kafka").setLevel(logging.CRITICAL)

    if "/books/" in request.path:
        logging.info('%(request.method)s,%(elapsed)s,%(now)s', {'request.method': f'{request.method}',
                                                                'elapsed': f'{elapsed}', 'now': f'{int(now)}'})
    return response


@server.route('/')
def index():
    return flask.redirect('/dashapp/')


@server.route('/books/', methods=['GET'])
def get_books():
    try:
        id = request.args['id']
    except Exception as _:
        id = None
    if not id:
        books = Book.query.all()
        return jsonify(books_schema.dump(books))
    book = Book.query.first_or_404(id)
    if not book:
        return jsonify({
            'error': 'Not found',
            'message': 'Could not find book with that id'
        }), 404
    return jsonify(book_schema.dump(book))


@server.route('/books/', methods=['POST'])
def create_book():
    data = request.get_json(force=True)

    is_bad_request = is_bad(data=data)

    if is_bad_request is not False:
        return is_bad_request
    if Book.query.filter_by(title=data["title"]).scalar():
        return jsonify({
            'error': 'Already exist',
            'message': 'This book already exist!'
        }), 409

    book = Book(
        title=data['title'],
        author=data['author']
    )
    db.session.add(book)
    db.session.commit()

    return jsonify(book_schema.dump(book))


@server.route('/books/<id>', methods=['PUT'])
def update(id):
    does_book_exist = does_exist(id=id)
    if does_book_exist is not True:
        return does_book_exist

    data = request.get_json(force=True)

    is_bad_request = is_bad(data=data)
    if is_bad_request is not False:
        return is_bad_request

    book = Book.query.first_or_404(id)

    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']

    db.session.commit()
    return jsonify(book_schema.dump(book)), 200


@server.route('/books/<id>', methods=['DELETE'])
def delete_book(id):
    does_book_exist = does_exist(id=id)

    if does_book_exist is not True:
        return does_book_exist

    book = Book.query.first_or_404(id)

    db.session.delete(book)
    db.session.commit()

    return jsonify({
        'success': 'Book deleted successfully!'
    })


async def send_log():
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
    while not os.path.exists("demo.log"):
        time.sleep(1)
    file = open("demo.log", "r")
    while True:
        line = file.readline()
        if not line:
            await asyncio.sleep(0.1)
            continue
        line = line.rstrip("\n")
        producer.send('log', value=bytes(line, 'utf-8'))
        producer.flush()


async def get_log():
    consumer = KafkaConsumer('log',  # topic
                             group_id='log_group',
                             # consume earliest available messages, for latest 'latest'
                             auto_offset_reset='earliest',
                             # don't commit offsets
                             enable_auto_commit=False,
                             # stop iteration if no message after 10 secs
                             consumer_timeout_ms=1000,
                             # kafka servers and port
                             bootstrap_servers=['localhost:9092'])
    consumer.topics()
    consumer.subscribe(["log"])
    while True:
        for msg in consumer:
            message = msg.value.decode('utf-8')
            message = message.split(',')
            method, ms, tm = message
            with server.app_context():
                logData = LogData(method=method, ms=int(ms), timestamp=int(tm))
                db.session.add(logData)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()

        await asyncio.sleep(0.1)


def between_callback():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [
        loop.create_task(send_log()),
        loop.create_task(get_log()),
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()


_thread = threading.Thread(target=between_callback)
_thread.start()


def create_dashapp(server):
    app = dash.Dash(
        server=server,
        url_base_pathname='/dashapp/'
    )
    app.config['suppress_callback_exceptions'] = True
    app.title = 'Dash App'

    app.layout = html.Div(
        children=[
            html.Div(className='row',
                     children=[
                         html.Div(className='row',
                                  children=[
                                      html.Div(className='two columns div-user-controls',
                                               style={'place-content': 'center'},
                                               children=[
                                                   html.H1(),
                                                   html.H2('Dashboard'),
                                                   html.H2('Completion Intervals of Requests')
                                               ]
                                               ),
                                      html.Div(className='ten columns div-for-charts bg-grey',
                                               style={'place-content': 'center'},
                                               children=[
                                                   dcc.Graph(id='timestamp', config={'displayModeBar': False},
                                                             animate=True),
                                                   dcc.Interval(
                                                       id='interval-component',
                                                       interval=1 * 1000,  # in milliseconds
                                                       n_intervals=0
                                                   )
                                               ])
                                  ])
                     ])
        ])

    @app.callback(Output('timestamp', 'figure'),
                  Input('interval-component', 'n_intervals'))
    def update_graph_scatter(n):
        output = []
        with server.app_context():
            message = LogData.query.all()
            for m in message:
                data = {'method': m.method, 'ms': m.ms / 1000.0, 'timestamp': m.timestamp + 3 * 60 * 60}
                output.append(data)
            l_data = pd.DataFrame(output)
        while len(l_data) == 0:
            figure = {'layout': go.Layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                margin={'t': 50},
                height=300,
                hovermode='x',
                autosize=True,
                title={'text': 'Request Completion Time', 'font': {'color': 'white'}, 'x': 0.5},
            ),
            }

            return figure

        colors = ['yellow', 'purple', 'green', 'blue']
        filtered = l_data[l_data['timestamp'] >= time.time() - 60 * 60]
        grp_data = filtered.groupby('method')

        data = []
        for group, dataframe in grp_data:
            dataframe = dataframe.sort_values(by=['timestamp'])
            trace = go.Scatter(x=pd.to_datetime(filtered['timestamp'], unit='s').tolist(),
                               y=dataframe.ms.tolist(),
                               marker=dict(color=colors[len(data)]),
                               name=group)
            data.append(trace)
        figure = {'data': data,
                  'layout': go.Layout(
                      template='plotly_dark',
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      plot_bgcolor='rgba(0, 0, 0, 0)',
                      margin={'t': 50},
                      height=250,
                      hovermode='x',
                      autosize=True,
                      title={'text': 'Request Completion Time', 'font': {'color': 'white'}, 'x': 0.5},
                  ),
                  }

        return figure

    return app


create_dashapp(server)

if __name__ == '__main__':
    server.run(debug=True, use_reloader=False)
