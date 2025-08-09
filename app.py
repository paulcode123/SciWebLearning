from flask import Flask, render_template


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/familiarity")
    def familiarity():
        return render_template("familiarity.html")

    @app.route("/inquiry")
    def inquiry():
        return render_template("inquiry.html")

    return app


app = create_app()


if __name__ == "__main__":
    # Dev server
    app.run(debug=True)


