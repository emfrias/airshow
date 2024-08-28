from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/signup', methods=['POST'])
def signup():
    # logic for user signup
    pass

@app.route('/login', methods=['POST'])
def login():
    # logic for user login
    pass

@app.route('/logout', methods=['POST'])
def logout():
    # logic for user logout
    pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7878)

