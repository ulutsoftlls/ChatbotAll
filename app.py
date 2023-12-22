from check_mistral2 import AnswerGenerater
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/api/receive_data', methods=['POST'])
def receive_data():
    received_data = request.json  # Assuming the data is sent as JSON
    # eval_prompt = "Майкл Джексон ким?"
    generated_text = text_generator.generate_text(received_data['in_text'])
    print(generated_text)
    response_data = {"out_text": generated_text}
    return jsonify(response_data)


if __name__ == '__main__':
    text_generator = AnswerGenerater()

    app.run(host='127.0.0.1', port=3050, debug=False)



