from flask import Flask, request, jsonify
from flask_cors import CORS
from backend import main




app = Flask(__name__)
CORS(app) 


@app.route('/nlpquery', methods=['POST'])
def generate_image():
    data = request.get_json()
    question = data.get('question', '')
    response = main(question)
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)