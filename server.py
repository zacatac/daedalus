from flask import Flask, request, jsonify

from agent import Agent

app = Flask(__name__)

# Example curl request:
# curl -X POST http://localhost:5000/eval -H "Content-Type: application/json" -d '{"test_filepath": "path/to/test/file", "test_output": "expected output", "debug": true}'


@app.route("/eval", methods=["POST"])
def evaluate():
    data = request.json
    test_filepath = data.get("test_filepath")
    test_output = data.get("test_output", None)
    debug = data.get("debug", True)

    if not test_filepath:
        return jsonify({"error": "Missing required parameter: test_filepath"}), 400

    try:
        agent = Agent(test_filepath=test_filepath, test_output=test_output, debug=debug)
        agent.run()
        return jsonify({"message": "Evaluation completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=2666, debug=False)
