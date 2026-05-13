from flask import Flask, request

app = Flask(__name__)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    # Har request ka method aur path return karega
    return f"Method: {request.method}, Path received: {path}", 200

def handler(request):
    return app(request.environ, start_response)
