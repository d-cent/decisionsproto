import argparse
import sys
from flask import Flask, render_template, request, jsonify
import re

from data.indexing import import_decision_data
from data.es import find_decisions, configure
from emailing.mailgun import send_mail, _build_html_email
from storage.mongo import save_subscription, get_subscriptions


app = Flask(__name__)
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')


@app.route("/")
def home():
    return render_template('index.jade')


@app.route("/example/email")
def email_template():
    return _build_html_email({'results': find_decisions('Helsinki'), 'topic': 'Helsinki'})


@app.route("/search", methods=["GET"])
def search_decisions():
    criteria = request.args.get("q")
    if criteria:
        criteria_stripped = criteria.strip()
        results = find_decisions(criteria_stripped)
        return render_template('results.jade',
                                results=results,
                                searchTerm=criteria_stripped)
    return ""


@app.route("/decision")
def decision():
    return render_template('decision.jade')


def valid_subscription(form):
    valid = False
    if 'email' in form and 'topic' in form:
        address_ok = re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", form.get('email'))
        if address_ok and form.get('topic'):
            valid = True
    return valid


@app.route("/subscribers", methods=["POST"])
def subscribe():
    if not valid_subscription(request.form):
        return 'bad request', 400
    save_subscription(request.form.get('email'), request.form.get('topic'))
    return 'ok', 201


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mailshot", action="store_true")
    parser.add_argument("--reindex", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.mailshot:
        print "Sending mail..."
        for sub in get_subscriptions():
            topic = sub.get('topic').strip()
            data = {'results': find_decisions(topic),
                    'topic': topic}
            send_mail(sub.get('email'),
                      'Municipal Decisions for %s' % topic,
                      data)
        sys.exit(0)

    if args.reindex:
        print "Indexing API data..."
        configure()
        import_decision_data()

    app.debug = bool(args.debug)
    app.run()

