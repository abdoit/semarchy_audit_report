from flask import Flask
from audit_report import generate_audit_report
app = Flask(__name__)
@app.route('/')
def hello_report():
    return generate_audit_report()
if __name__ == '__main__':
    app.run()