from flask import Flask
from data import get_data
import json

app = Flask(__name__)

@app.route('/api/rsr/<text>', methods=['GET'])
def search_rsr(text):
    index = get_data.loadIndexRsr()
    res = get_data.searchIndex(index, text)
    return json.dumps(res)

@app.route('/api/prj/<text>', methods=['GET'])
def search_prj(text):
    index = get_data.loadIndexPrj()
    res = get_data.searchIndex(index, text)
    return json.dumps(res)

@app.route('/api/org/<text>', methods=['GET'])
def search_org(text):
    index = get_data.loadIndexOrg()
    res = get_data.searchIndex(index, text)
    return json.dumps(res)

# Main
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0',port=80)

