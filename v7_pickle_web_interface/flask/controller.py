#!/usr/bin/env python3

# convention: every function and class includes a [trace] print
# reason: to help the developer understand functional dependencies and which state the program is in,
# a "trace" is printed to the terminal at the start of each function

# convention: every call to an external module is wrapped in a try/except, with the error message (err) sent to both logger and flash
# reason: any errors returned must be handled otherwise Flask errors and the website crashes

# convention: every call to flash must be either a string or the content must be wrapped in str()
# reason: when content is passed to flash() that cannot be serialized, the Flask error and the website crashes

# convention: every "raise Exception" should be proceeded by a corresponding "logger.error()"

# convention: the conditional "POST" operations should happen before the "GET" operations
# reason: sometimes the "POST" operation changes the data and the page content needs to be updated

# https://runnable.com/docker/python/docker-compose-with-flask-apps
# from redis import Redis
# https://pypi.org/project/rejson/
# from rejson import Client, Path

import os
import json
import shutil
import time

# https://docs.python.org/3/howto/logging.html
import logging

# https://hplgit.github.io/web4sciapps/doc/pub/._web4sa_flask004.html
from flask import Flask, redirect, render_template, request, url_for, flash, jsonify
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
from flask_wtf import FlaskForm
# https://pythonhosted.org/Flask-Bootstrap/basic-usage.html
from flask_bootstrap import Bootstrap

# https://flask-login.readthedocs.io/en/latest/_modules/flask_login/mixins.html
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
# https://en.wikipedia.org/wiki/Mixin
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
# https://gist.github.com/lost-theory/4521102
from flask import g
from werkzeug.utils import secure_filename
from wtforms import Form, StringField, validators, FieldList, FormField, IntegerField, RadioField, PasswordField, SubmitField, BooleanField  # type: ignore

# https://json-schema.org/
from jsonschema import validate  # type: ignore
from config import (
    Config,
)  # https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
from urllib.parse  import urlparse, urljoin

import common_lib as clib  # PDG common library
import json_schema  # PDG
import compute  # PDG
import validate_inference_rules_sympy as vir  # PDG

# global proc_timeout
proc_timeout = 30
path_to_db = "pdg.db"
# the following is done once upon program load
clib.json_to_sql("data.json", path_to_db)

# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
login_manager = LoginManager()

app = Flask(__name__, static_folder="static")
app.config.from_object(
    Config
)  # https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
app.config[
    "UPLOAD_FOLDER"
] = "/home/appuser/app/uploads"  # https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
app.config[
    "SEND_FILE_MAX_AGE_DEFAULT"
] = 0  # https://stackoverflow.com/questions/34066804/disabling-caching-in-flask
app.config["DEBUG"] = True

# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
login_manager.init_app(app)

# TODO: get rid of this!
Bootstrap(app)

import pdg_api

# https://runnable.com/docker/python/docker-compose-with-flask-apps
# rd = Redis(host='db', port=6379)
# clib.connect_redis()
# https://pypi.org/project/rejson/
# rj = Client(host='db', port=6379, decode_responses=True)


if __name__ == "__main__":
    # called from flask
    print("called from flask")

    # https://docs.python.org/3/howto/logging.html
    logging.basicConfig(  # filename='pdg.log',
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s|%(filename)-13s|%(levelname)-5s|%(lineno)-4d|%(funcName)-20s|%(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )
    logger = logging.getLogger(__name__)

# https://stackoverflow.com/questions/41087790/how-to-override-gunicorns-logging-config-to-use-a-custom-formatter
# https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
# if __name__ != "__main__":
else:
    print("called from gunicorn")

    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    logger = app.logger

# https://wtforms.readthedocs.io/en/stable/crash_course.html
# https://stackoverflow.com/questions/46092054/flask-login-documentation-loginform
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[validators.DataRequired()])
    # password = PasswordField("Password")
    submit = SubmitField('sign in')
    # https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
    remember_me = BooleanField("remember me")

# https://flask-login.readthedocs.io/en/latest/_modules/flask_login/mixins.html
class User(UserMixin):
    """
    https://realpython.com/using-flask-login-for-user-management-with-flask/
    and
    https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
    """
    id = 423
    username = "ben"
    email = "ben@gmail"


    def is_active(self):
        return True
    def get_id(self):
        return 'ben@gmail'
#    def is_authenticated(self):
#        return self.authenticated
    def __repr__(self):
        return '<User {}>'.format(self.username)

class EquationInputForm(Form):
    logger.info("[trace] class = EquationInputForm")
    #    r = FloatField(validators=[validators.InputRequired()])
    #    r = FloatField()
    latex = StringField("LaTeX", validators=[validators.InputRequired(),
                                             validators.Length(max=1000)])

class InferenceRuleForm(Form):
    logger.info("[trace] class = InferenceRuleForm")
    inf_rule_name = StringField(
        "inf rule name", validators=[validators.InputRequired(), validators.Length(max=1000)]
    )
    num_inputs = IntegerField(
        "number of inputs",
        validators=[validators.InputRequired(), validators.NumberRange(min=0, max=5)],
    )
    num_feeds = IntegerField(
        "number of feeds",
        validators=[validators.InputRequired(), validators.NumberRange(min=0, max=5)],
    )
    num_outputs = IntegerField(
        "number of outputs",
        validators=[validators.InputRequired(), validators.NumberRange(min=0, max=5)],
    )
    latex = StringField("LaTeX", validators=[validators.InputRequired()])

class RevisedTextForm(Form):
    logger.info("[trace] class = RevisedTextForm")
    revised_text = StringField("revised text", validators=[validators.InputRequired(),validators.Length(max=1000)])

class infRuleInputsAndOutputs(Form):
    logger.info("[trace] class = infRuleInputsAndOutputs")
    """
    a form with one or more latex entries
    source: https://stackoverflow.com/questions/28375565/add-input-fields-dynamically-with-wtforms
            https://stackoverflow.com/questions/30121763/how-to-use-a-wtforms-fieldlist-of-formfields
            https://gist.github.com/doobeh/5d0f965502b86fee80fe
            https://www.rmedgar.com/blog/dynamic_fields_flask_wtf

    docs: https://wtforms.readthedocs.io/en/latest/fields.html#field-enclosures
          https://wtforms.readthedocs.io/en/latest/fields.html#wtforms.fields.FieldList
          https://wtforms.readthedocs.io/en/latest/fields.html#wtforms.fields.FormField
    """
    inputs_and_outputs = FieldList(
        FormField(EquationInputForm, "late_x"), min_entries=1
    )


#    inputs_and_outputs = FieldList(EquationInputForm, min_entries=1)

# https://stackoverflow.com/questions/37837682/python-class-input-argument/37837766
# https://wtforms.readthedocs.io/en/stable/validators.html
class LatexIO(Form):
    logger.info("[trace] class = LatexIO")
    feed1 = StringField("feed LaTeX 1", validators=[validators.InputRequired(),validators.Length(max=1000)])
    feed2 = StringField("feed LaTeX 2", validators=[validators.InputRequired(),validators.Length(max=1000)])
    feed3 = StringField("feed LaTeX 3", validators=[validators.InputRequired(),validators.Length(max=1000)])
    input1 = StringField("input LaTeX 1", validators=[validators.Length(max=1000)])
    input1_radio = RadioField(
        "Label",
        choices=[
            ("latex", "use Latex"),
            ("local", "use local ID"),
            ("global", "use global ID"),
        ],
        default="latex",
    )  # , validators=[validators.InputRequired()])
    input2 = StringField("input LaTeX 2", validators=[validators.Length(max=1000)])
    input2_radio = RadioField(
        "Label",
        choices=[
            ("latex", "use Latex"),
            ("local", "use local ID"),
            ("global", "use global ID"),
        ],
        default="latex",
    )  # , validators=[validators.InputRequired()])
    input3 = StringField("input LaTeX 3" , validators=[validators.Length(max=1000)])
    input3_radio = RadioField(
        "Label",
        choices=[
            ("latex", "use Latex"),
            ("local", "use local ID"),
            ("global", "use global ID"),
        ],
        default="latex",
    )  # , validators=[validators.InputRequired()])
    output1 = StringField(
        "output LaTeX 1" , validators=[validators.Length(max=1000)])
    output1_radio = RadioField(
        "Label",
        choices=[
            ("latex", "use Latex"),
            ("local", "use local ID"),
            ("global", "use global ID"),
        ],
        default="latex",
    )
    output2 = StringField(
        "output LaTeX 2" , validators=[validators.Length(max=1000)])
    output2_radio = RadioField(
        "Label",
        choices=[
            ("latex", "use Latex"),
            ("local", "use local ID"),
            ("global", "use global ID"),
        ],
        default="latex",
    )  # , validators=[validators.InputRequired()])
    output3 = StringField(
        "output LaTeX 3", validators=[validators.Length(max=1000)])
    output3_radio = RadioField(
        "Label",
        choices=[
            ("latex", "use Latex"),
            ("local", "use local ID"),
            ("global", "use global ID"),
        ],
        default="latex",
    )  # , validators=[validators.InputRequired()])


class NameOfDerivationInputForm(Form):
    logger.info("[trace] class = NameOfDerivationInputForm")
    name_of_derivation = StringField(validators=[validators.InputRequired(),validators.Length(max=1000)])


# goal is to prevent cached responses;
# see https://stackoverflow.com/questions/47376744/how-to-prevent-cached-response-flask-server-using-chrome
# The following doesn't work; instead use "F12 > Network > Disable cache"
# @app.after_request
# def add_header(r):
#    """
#    Add headers to both force latest IE rendering engine or Chrome Frame,
#    and also to cache the rendered page for 10 minutes.
#    """
#    logger.info('[trace] add_header')
#    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#    r.headers["Pragma"] = "no-cache"
#    r.headers["Expires"] = "0"
#    r.headers['Cache-Control'] = 'public, max-age=0'
#    return r


# @app.errorhandler(404)
# def page_not_found(e):
#    """
#    https://flask.palletsprojects.com/en/1.1.x/patterns/errorpages/
#    """
#    logger.info("[trace] page_not_found")
#    logger.debug(e)
#    return redirect(url_for("index"))

@login_manager.user_loader
def load_user(user_id):
    """
    https://flask-login.readthedocs.io/en/latest/
    also https://realpython.com/using-flask-login-for-user-management-with-flask/
    https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
    """
    user = User()
    return user #User.get_id(user_id)

def is_safe_url(target):
    """
    https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    https://github.com/allofphysicsgraph/proofofconcept/issues/110

    from https://flask-login.readthedocs.io/en/latest/
    and https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins

    Here we use a class of some kind to represent and validate our
    client-side form data. For example, WTForms is a library that will
    handle this for us, and we use a custom LoginForm to validate.
    """
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class

        # the following is what the person entered into the form
        logger.debug("username= %s", form.username.data)
#        user = User(form.username.data)
        user = User()
        if user is None: # or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        logger.debug('user is not none')
        logger.debug('user = %s', str(user))
        # https://flask-login.readthedocs.io/en/latest/#flask_login.login_user
        login_user(user, remember=form.remember_me.data)
        logger.debug('user logged in')
        flash('Logged in successfully.')

        next = request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return abort(400)

        return redirect(next or url_for('index'))
    return render_template('login.html', form=form)

@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    """
    https://flask-login.readthedocs.io/en/latest/#login-example
    >>>
    """
    logout_user()
    return redirect(url_for('index'))


@app.route("/user/<user_name>/", methods=['GET', 'POST'])
def user(user_name):
    """
    # TODO -- this is just a stub
    https://github.com/allofphysicsgraph/proofofconcept/issues/126
    >>>
    """
    # TODO
    sign_up_date = '2020-04-12'
    # TODO
    last_previous_contribution_date = '2020-04-10'
    # TODO
    list_of_derivs = ['fun deriv', 'another deriv']
    # TODO
    list_of_exprs = ['424252', '525252']

    return redirect(url_for('user'),
    user_name=user_name,
    sign_up_date=sign_up_date,
    last_previous_contribution_date=last_previous_contribution_date,
    list_of_derivs=list_of_derivs,
    list_of_exprs=list_of_exprs)

@app.before_request
def before_request():
    """
    https://stackoverflow.com/questions/12273889/calculate-execution-time-for-every-page-in-pythons-flask
    actually, https://gist.github.com/lost-theory/4521102
    >>> before_request():
    """
    g.start = time.time()
    g.request_start_time = time.time()
    elapsed_time = lambda: "%.5f seconds" % (time.time() - g.request_start_time)
    logger.info(elapsed_time)
    g.request_time = elapsed_time


@app.after_request
def after_request(response):
    """
    https://stackoverflow.com/questions/12273889/calculate-execution-time-for-every-page-in-pythons-flask

    I don't know how to access this measure

    >>> after_request()
    """
    diff = time.time() - g.start
    if (
        (response.response)
        and (200 <= response.status_code < 300)
        and (response.content_type.startswith("text/html"))
    ):
        response.set_data(
            response.get_data().replace(
                b"__EXECUTION_TIME__", bytes(str(diff), "utf-8")
            )
        )
    return response




@app.route("/index", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    """
    the index is a static page intended to be the landing page for new users
    >>> index()
    """
    logger.info("[trace] index")
    return render_template("index.html")


@app.route("/faq", methods=["GET", "POST"])
def faq():
    """
    "frequently asked questions" is a static page
    >>> faq()
    """
    logger.info("[trace] faq")
    return render_template("faq.html")


@app.route("/user_documentation", methods=["GET", "POST"])
def user_documentation():
    """
    a static page with documentation aimed at users (not developers)
    >>> user_documentation()
    """
    logger.info("[trace] user_documentation")
    return render_template("user_documentation.html")


@app.route("/developer_documentation", methods=["GET", "POST"])
def developer_documentation():
    """
    a static page aimed at people interested in contributed code changes
    >>> developer_documentation()
    """
    logger.info("[trace] developer_documentation")
    return render_template("developer_documentation.html")


@app.route("/example_T_f_d3js", methods=["GET", "POST"])
def example_T_f_d3js():
    """
    >>> example_T_f_d3js()
    """
    logger.info("[trace] example_T_f_d3js")
    return render_template("example_T_f_d3js.html")


@app.route("/how_to_build_the_physics_derivation_graph", methods=["GET", "POST"])
def how_to_build_the_physics_derivation_graph():
    """
    >>> how_to_build_the_physics_derivation_graph()
    """
    logger.info("[trace] how_to_build_the_physics_derivation_graph")
    return render_template("how_to_build_the_physics_derivation_graph.html")


@app.route("/editor", methods=["GET", "POST"])
def editor():
    """
    editor.html contains hyperlinks to pages like:
    * start new derivation
    * edit existing derivation
    * edit inference rule
    * view existing derivations

    file upload: see https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
    """
    logger.info("[trace] editor")

    # this takes too long; removed on 20200408
    #    try:
    #        compute.generate_all_expr_and_infrule_pngs(False, path_to_db)
    #    except Exception as err:
    #        logger.error(str(err))
    #        flash(str(err))

    try:
        logger.debug("session id = %s", session_id)
    except NameError:
        logger.warning("session id does not appear to exist")
        try:
            session_id = compute.create_session_id()
        except Exception as err:
            logger.error(str(err))
            flash(str(err))
            session_id = "0"
        logger.debug("now the session id = %s", session_id)

    [
        json_file,
        all_df,
        df_pkl_file,
        sql_file,
        rdf_file,
        neo4j_file,
    ] = compute.create_files_of_db_content(path_to_db)

    if request.method == "POST":
        logger.debug("request.form = %s", request.form)
        # ImmutableMultiDict([('file', <FileStorage: 'prospector_output.json' ('application/json')>)])

        # check if the post request has the file part
        if "file" not in request.files:
            logger.debug("file not in request files")
            flash("No file part")
            return redirect(request.url)
        file_obj = request.files["file"]

        logger.debug(request.files)
        # if user does not select file, browser also
        # submit an empty part without filename
        if file_obj.filename == "":
            logger.debug("no selected file")
            flash("No selected file")
            return redirect(request.url)
        try:
            allowed_bool = compute.allowed_file(file_obj.filename)
        except Exception as err:
            logger.error(str(err))
            flash(str(err))
            allowed_bool = False
        if file_obj and allowed_bool:
            filename = secure_filename(file_obj.filename)
            logger.debug("filename = %s", filename)
            path_to_uploaded_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file_obj.save(path_to_uploaded_file)

            # TODO: just because a file is JSON and passes the schema does not make it valid for the PDG
            # for example, the inference rule names need to be consistent (in "derivations" and "inference rules")
            # also, the expr_local_id need to have a corresponding entry in local-to-global
            # also, every expr_global_id in local-to-global must have a corresponding entry in "inference rules"
            valid_json_bool = True
            try:
                compute.validate_json_file(path_to_uploaded_file)
            except Exception as err:
                logger.error(str(err))
                flash(str(err))
                valid_json_bool = False
            if not valid_json_bool:
                flash("uploaded file does not match PDG schema")
            else:  # file exists, has .json extension, is JSON, and complies with schema
                shutil.copy(path_to_uploaded_file, "/home/appuser/app/" + path_to_db)
            return redirect(url_for("index", filename=filename))

    logger.debug("reading from json")
    dat = clib.read_db(path_to_db)
    return render_template(
        "editor.html",
        number_of_derivations=len(dat["derivations"].keys()),
        number_of_infrules=len(dat["inference rules"].keys()),
        number_of_expressions=len(dat["expressions"].keys()),
        number_of_symbols=len(dat["symbols"].keys()),
        number_of_operators=len(dat["operators"].keys()),
        database_json=json_file,
        database_df_pkl=df_pkl_file,
        database_sql=sql_file,
        database_neo4j=neo4j_file,
        database_rdf=rdf_file,
    )


@app.route("/start_new_derivation/", methods=["GET", "POST"])
@login_required # https://flask-login.readthedocs.io/en/latest/
def start_new_derivation():
    logger.info("[trace] start_new_derivation")
    web_form = NameOfDerivationInputForm(request.form)
    if request.method == "POST" and web_form.validate():
        name_of_derivation = str(web_form.name_of_derivation.data)
        logger.debug(
            "start_new_derivation: name of derivation = %s", name_of_derivation,
        )
        return redirect(
            url_for("new_step_select_inf_rule", name_of_derivation=name_of_derivation)
        )
    return render_template(
        "start_new_derivation.html", form=web_form, title="start new derivation"
    )


@app.route("/show_all_derivations", methods=["GET", "POST"])
def show_all_derivations():
    """
    >>>
    """
    logger.info("[trace] show_all_derivations")
    if request.method == "POST":
        logger.debug("request.form = %s", request.form)

    try:
        map_of_derivations = compute.generate_map_of_derivations(path_to_db)
    except Exception as err:
        flash(str(err))
        logger.error(str(err))
        map_of_derivations = "error.png"

    try:
        derivations_popularity_dict = compute.popularity_of_derivations(path_to_db)
    except Exception as err:
        flash(str(err))
        logger.error(str(err))
        derivations_popularity_dict = {}

    return render_template(
        "show_all_derivations.html",
        map_of_derivations=map_of_derivations,
        derivations_popularity_dict=derivations_popularity_dict,
    )


@app.route("/list_all_operators", methods=["GET", "POST"])
def list_all_operators():
    """
    >>>
    """
    logger.info("[trace] list_all_operators")

    if request.method == "POST":
        logger.debug("request.form = %s", request.form)
        # request.form = ImmutableMultiDict([('delete_operator', 'indefinite intergral')])
        if "delete_operator" in request.form.keys():
            compute.delete_operator(request.form["delete_operator"], path_to_db)
        elif "edit_operator_latex" in request.form.keys():
            compute.edit_operator_latex(
                request.form["edit_operator_latex"],
                request.form["revised_text"],
                path_to_db,
            )
        else:
            logger.error("unrecognized option")
            flash("unrecognized option")

    dat = clib.read_db(path_to_db)
    try:
        operator_popularity_dict = compute.popularity_of_operators(path_to_db)
    except Exception as err:
        flash(str(err))
        logger.error(str(err))
        operator_popularity_dict = {}

    sorted_list_operators = list(dat["operators"].keys())
    sorted_list_operators.sort()
    sorted_list_operators_not_in_use = compute.get_sorted_list_of_operators_not_in_use(
        path_to_db
    )

    return render_template(
        "list_all_operators.html",
        operators_dict=dat["operators"],
        sorted_list_operators=sorted_list_operators,
        sorted_list_operators_not_in_use=sorted_list_operators_not_in_use,
        edit_latex_webform=RevisedTextForm(request.form),
        operator_popularity_dict=operator_popularity_dict,
    )


@app.route("/list_all_symbols", methods=["GET", "POST"])
def list_all_symbols():
    logger.info("[trace] list_all_symbols")

    if request.method == "POST":
        logger.debug("request.form = %s", request.form)
        if "delete_symbol" in request.form.keys():
            compute.delete_symbol(request.form["delete_symbol"], path_to_db)
        elif "edit_symbol_latex" in request.form.keys():
            # request.form = ImmutableMultiDict([('edit_symbol_latex', '1245'), ('revised_text', 'asfgasg')])
            compute.edit_symbol_latex(
                request.form["edit_symbol_latex"],
                request.form["revised_text"],
                path_to_db,
            )
        else:
            logger.error("unrecognized option")
            flash("unrecognized option")

    dat = clib.read_db(path_to_db)
    try:
        symbol_popularity_dict = compute.popularity_of_symbols(path_to_db)
    except Exception as err:
        flash(str(err))
        logger.error(str(err))
        symbol_popularity_dict = {}

    sorted_list_symbols = list(dat["symbols"].keys())
    sorted_list_symbols.sort()
    sorted_list_symbols_not_in_use = compute.get_sorted_list_of_symbols_not_in_use(
        path_to_db
    )

    return render_template(
        "list_all_symbols.html",
        symbols_dict=dat["symbols"],
        sorted_list_symbols=sorted_list_symbols,
        sorted_list_symbols_not_in_use=sorted_list_symbols_not_in_use,
        edit_latex_webform=RevisedTextForm(request.form),
        symbol_popularity_dict=symbol_popularity_dict,
    )


@app.route("/list_all_expressions", methods=["GET", "POST"])
def list_all_expressions():
    logger.info("[trace] list_all_expressions")
    dat = clib.read_db(path_to_db)
    try:
        expression_popularity_dict = compute.popularity_of_expressions(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        expression_popularity_dict = {}
    if request.method == "POST":
        logger.debug("list_all_expressions; request.form = %s", request.form)
        if "edit_expr_latex" in request.form.keys():
            # request.form = ImmutableMultiDict([('edit_expr_latex', '4928923942'), ('revised_text', 'asdfingasinsf')])
            try:
                status_message = compute.edit_expr_latex(
                    request.form["edit_expr_latex"],
                    request.form["revised_text"],
                    path_to_db,
                )
            except Exception as err:
                logger.error(str(err))
                flash(str(err))
                status_message = "error"
            flash(str(status_message))
            logger.debug("list_all_expressions; status = %s", status_message)
            return redirect(url_for("list_all_expressions"))
        elif "delete_expr" in request.form.keys():
            # request.form = ImmutableMultiDict([('delete_expr', '4928923942')])
            try:
                status_message = compute.delete_expr(
                    request.form["delete_expr"], path_to_db
                )
            except Exception as err:
                logger.error(str(err))
                flash(str(err))
                status_message = "error"
            flash(str(status_message))
            logger.debug("list_all_expressions; status = %s", status_message)
            return redirect(url_for("list_all_expressions"))
    try:
        list_of_expr = compute.get_sorted_list_of_expr(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        list_of_expr = []
    try:
        list_of_expr_not_appearing_in_any_derivations = compute.get_sorted_list_of_inf_rules_not_in_use(
            path_to_db
        )
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        list_of_expr_not_appearing_in_any_derivations = []
    return render_template(
        "list_all_expressions.html",
        expressions_dict=dat["expressions"],
        sorted_list_exprs=list_of_expr,
        list_of_expr_not_appearing_in_any_derivations=list_of_expr_not_appearing_in_any_derivations,
        edit_expr_latex_webform=RevisedTextForm(request.form),
        expression_popularity_dict=expression_popularity_dict,
    )


@app.route("/list_all_inference_rules", methods=["GET", "POST"])
def list_all_inference_rules():
    logger.info("[trace] list_all_inference_rules")
    dat = clib.read_db(path_to_db)
    try:
        infrule_popularity_dict = compute.popularity_of_infrules(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        infrule_popularity_dict = {}
    if request.method == "POST":
        logger.debug(
            "list_all_inference_rules; request.form = %s", request.form,
        )
        if "inf_rule_name" in request.form.keys():
            # request.form = ImmutableMultiDict([('inf_rule_name', 'testola'), ('num_inputs', '1'), ('num_feeds', '0'), ('num_outputs', '0'), ('latex', 'adsfmiangasd')])
            try:
                status_message = compute.add_inf_rule(
                    request.form.to_dict(), path_to_db
                )
            except Exception as err:
                flash(str(err))
                logging.warning(err)
                status_message = "error"
            flash(str(status_message))
            # https://stackoverflow.com/a/31945712/1164295
            return redirect(url_for("list_all_inference_rules"))
        elif "delete_inf_rule" in request.form.keys():
            # request.form = ImmutableMultiDict([('delete_inf_rule', 'asdf')])
            try:
                status_message = compute.delete_inf_rule(
                    request.form["delete_inf_rule"], path_to_db
                )
            except Exception as err:
                flash(str(err))
                logging.warning(err)
                status_message = "error"
            flash(str(status_message))
            logger.debug(
                "list_all_inference_rules; status = %s", status_message,
            )
            return redirect(url_for("list_all_inference_rules"))
        elif "rename_inf_rule_from" in request.form.keys():
            # request.form = ImmutableMultiDict([('rename_inf_rule_from', 'asdf'), ('revised_text', 'anotehr')])
            try:
                status_message = compute.rename_inf_rule(
                    request.form["rename_inf_rule_from"],
                    request.form["revised_text"],
                    path_to_db,
                )
            except Exception as err:
                flash(str(err))
                logging.warning(err)
                status_message = "error"
            flash(str(status_message))
            logger.debug(
                "list_all_inference_rules; status = %s", status_message,
            )
            return redirect(url_for("list_all_inference_rules"))
        elif "edit_inf_rule_latex" in request.form.keys():
            # request.form = ImmutableMultiDict([('edit_inf_rule_latex', 'asdf'), ('revised_text', 'great works')])
            try:
                status_message = compute.edit_inf_rule_latex(
                    request.form["edit_inf_rule_latex"],
                    request.form["revised_text"],
                    path_to_db,
                )
            except Exception as err:
                flash(str(err))
                logging.warning(err)
                status_message = "error"
            flash(str(status_message))
            logger.debug(
                "list_all_inference_rules; status = %s", status_message,
            )
            return redirect(url_for("list_all_inference_rules"))
        else:
            flash("unrecognized form result")
            logger.warning("ERROR: unrecognized form result")

    infrules_modified_latex_dict = {}
    for infrule_name, infrule_dict in dat["inference rules"].items():
        infrule_dict["latex"] = infrule_dict["latex"].replace("\\ref", "ref")
        infrules_modified_latex_dict[infrule_name] = infrule_dict

    try:
        sorted_list_infrules = compute.get_sorted_list_of_inf_rules_not_in_use(
            path_to_db
        )
    except Exception as err:
        flash(str(err))
        logging.warning(err)
        sorted_list_infrules = []

    return render_template(
        "list_all_inference_rules.html",
        infrules_dict=infrules_modified_latex_dict,
        sorted_list_infrules=sorted_list_infrules,
        add_infrule_webform=InferenceRuleForm(request.form),
        rename_infrule_webform=RevisedTextForm(request.form),
        edit_infrule_latex_webform=RevisedTextForm(request.form),
        infrule_popularity_dict=infrule_popularity_dict,
    )


@app.route("/select_derivation_to_edit", methods=["GET", "POST"])
def select_derivation_to_edit():
    logger.info("[trace] select_derivation_to_edit")
    if request.method == "POST":
        logger.debug(
            "select_derivation_to_edit; request.form = %s", request.form,
        )

    try:
        derivations_list = (compute.get_sorted_list_of_derivations(path_to_db),)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        derivations_list = []

    return render_template(
        "select_derivation_to_edit.html", derivations_list=derivations_list,
    )


@app.route(
    "/select_derivation_step_to_edit/<name_of_derivation>/", methods=["GET", "POST"]
)
def select_derivation_step_to_edit(name_of_derivation: str):
    """
    >>> select_derivation_step_to_edit('fun deriv')
    """
    logger.info("[trace] select_derivation_step_to_edit")
    try:
        step_dict = compute.get_derivation_steps(name_of_derivation, path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        step_dict = {}
    if request.method == "POST":
        logger.debug("request.form = %s", request.form)
        # request.form = ImmutableMultiDict([('step_to_delete', '0491182')])
        if "step_to_delete" in request.form.keys():
            step_to_delete = request.form["step_to_delete"]
            try:
                compute.delete_step_from_derivation(
                    name_of_derivation, step_to_delete, path_to_db
                )
                return redirect(
                    url_for("review_derivation", name_of_derivation=name_of_derivation)
                )
            except Exception as err:
                logger.error(str(err))
                flash(str(err))

    dat = clib.read_db(path_to_db)

    if name_of_derivation in dat["derivations"].keys():
        # step_dict = dat["derivations"][name_of_derivation]
        try:
            derivation_validity_dict = compute.determine_derivation_validity(
                name_of_derivation, path_to_db
            )
        except Exception as err:
            logger.error(str(err))
            flash(str(err))
            derivation_validity_dict = {}
    else:
        # step_dict = {}
        derivation_validity_dict = {}

    sorted_step_ids = list(step_dict.keys())
    sorted_step_ids.sort()

    return render_template(
        "select_derivation_step_to_edit.html",
        name_of_derivation=name_of_derivation,
        expr_local_to_gobal=dat["expr local to global"],
        expressions_dict=dat["expressions"],
        step_dict=step_dict,
        derivation_validity_dict=derivation_validity_dict,
        list_of_step_ids=sorted_step_ids,
    )


@app.route("/select_from_existing_derivations", methods=["GET", "POST"])
def select_from_existing_derivations():
    logger.info("[trace] select_from_existing_derivations")
    try:
        list_of_deriv = compute.get_sorted_list_of_derivations(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        list_of_deriv = []
    if request.method == "POST":
        logger.debug(
            "select_from_existing_derivations; request.form = %s", request.form
        )

        # dropdown menu provides a derivation selected
        if "derivation_selected" in request.form.keys():
            name_of_derivation = request.form["derivation_selected"]
        else:  # no derivations exist
            return redirect(url_for("index"))

        if request.form["submit_button"] == "generate_pdf":
            # request.form = ImmutableMultiDict([('derivation_selected', 'another deriv'), ('submit_button', 'generate_pdf')])
            try:
                pdf_filename = compute.generate_pdf_for_derivation(
                    name_of_derivation, path_to_db
                )
            except Exception as err:
                logger.error(str(err))
                flash(str(err))
                return render_template(
                    "select_from_existing_derivations.html",
                    list_of_derivations=list_of_deriv,
                )

            return redirect(url_for("static", filename=pdf_filename))

        if request.form["submit_button"] == "generate_tex":
            # request.form = ImmutableMultiDict([('derivation_selected', 'another deriv'), ('submit_button', 'generate_tex')])
            try:
                tex_filename = compute.generate_tex_for_derivation(
                    name_of_derivation, path_to_db
                )
            except Exception as err:
                logger.error(str(err))
                flash(str(err))
                return render_template(
                    "select_from_existing_derivations.html",
                    list_of_derivations=list_of_deriv,
                )

            return redirect(url_for("static", filename=tex_filename))

        elif request.form["submit_button"] == "display_graphviz":
            # request.form = ImmutableMultiDict([('derivation_selected', 'another deriv'), ('submit_button', 'display_graphviz')])
            return redirect(
                url_for("review_derivation", name_of_derivation=name_of_derivation,)
            )
        else:
            flash("unrecongized button in" + str(request.form))

    return render_template(
        "select_from_existing_derivations.html", list_of_derivations=list_of_deriv
    )


@app.route("/new_step_select_inf_rule/<name_of_derivation>/", methods=["GET", "POST"])
@login_required # https://flask-login.readthedocs.io/en/latest/
def new_step_select_inf_rule(name_of_derivation: str):
    logger.info("[trace] new_step_select_inf_rule")
    try:
        list_of_inf_rules = compute.get_sorted_list_of_inf_rules(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        list_of_inf_rules = []

    if (
        request.method == "POST"
    ):  # and request.form.validate(): no validation because the form was defined on the web page
        logger.debug("request form %s", request.form)
        selected_inf_rule = request.form.get("inf_rul_select")
        logger.debug(
            "selected_inf_rule = %s", selected_inf_rule,
        )
        return redirect(
            url_for(
                "provide_expr_for_inf_rule",
                name_of_derivation=name_of_derivation,
                inf_rule=selected_inf_rule,
            )
        )

    return render_template(
        "new_step_select_inf_rule.html",
        title=name_of_derivation,
        inf_rule_list=list_of_inf_rules,
        name_of_derivation=name_of_derivation,
    )


@app.route(
    "/provide_expr_for_inf_rule/<name_of_derivation>/<inf_rule>",
    methods=["GET", "POST"],
)
def provide_expr_for_inf_rule(name_of_derivation: str, inf_rule: str):
    """
    https://stackoverflow.com/questions/28375565/add-input-fields-dynamically-with-wtforms

    >>> provide_expr_for_inf_rule()
    """

    logger.info("[trace] provide_expr_for_inf_rule")
    # num_feeds, num_inputs, num_outputs = compute.input_output_count_for_infrule(inf_rule, path_to_db)
    # logger.debug('provide_expr_for_inf_rule;',num_feeds,'feeds,',num_inputs,'inputs, and',num_outputs,'outputs')

    dat = clib.read_db(path_to_db)

    webform=LatexIO(request.form)

#    if request.method == "POST" and not webform.validate():
#        if len(str(webform.input1.data))>10:
#            flash(str(webform.input1.data) + " is more than 10 characters"

    if  request.method == "POST": #  and webform.validate():
        latex_for_step_dict = request.form

        logger.debug("latex_for_step_dict = request.form = %s", request.form)
        # request.form = ImmutableMultiDict([('input1', 'a = b'), ('submit_button', 'Submit')])

        # request.form = ImmutableMultiDict([('input1', 'asfd'), ('use_ID_for_in1', 'on'), ('submit_button', 'Submit')])

        # request.form = ImmutableMultiDict([('input1', '1492842000'), ('use_ID_for_in1', 'on'), ('feed1', 'a'), ('feed2', 'b'), ('feed3', 'c'), ('output1', 'asdf = asf'), ('submit_button', 'Submit')])

        # request.form = ImmutableMultiDict([('input1', ''), ('input1_radio', 'global'), ('input1_global_id', '5530148480'), ('feed1', 'asgasgag'), ('output1', ''), ('output1_radio', 'global'), ('output1_glob_id', '9999999951'), ('submit_button', 'Submit')])

        try:
            local_step_id = compute.create_step(
                latex_for_step_dict, inf_rule, name_of_derivation, path_to_db
            )
        except Exception as err:
            flash(str(err))
            logger.error(str(err))
            local_step_id = "0"
        logger.debug(
            "local_step_id = %s", local_step_id,
        )

        try:
            step_validity_msg = vir.validate_step(
                name_of_derivation, local_step_id, path_to_db
            )
        except Exception as err:
            flash(str(err))
            logger.warning(str(err))
            step_validity_msg = "error in validation"

        return redirect(
            url_for(
                "step_review",
                name_of_derivation=name_of_derivation,
                local_step_id=local_step_id,
            )
        )

    # the following is needed to handle the case where the derivation is new and no steps exist yet
    if name_of_derivation in dat["derivations"].keys():
        step_dict = dat["derivations"][name_of_derivation]
        try:
            derivation_validity_dict = compute.determine_derivation_validity(
                name_of_derivation, path_to_db
            )
        except Exception as err:
            logger.error(str(err))
            flash(str(err))
            derivation_validity_dict = {}
    else:
        step_dict = {}
        derivation_validity_dict = {}

    # logger.debug('step validity = %s', str(step_validity_dict))

    try:
        expression_popularity_dict = compute.popularity_of_expressions(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        expression_popularity_dict = {}

    try:
        list_of_local_id = compute.list_local_id_for_derivation(
            name_of_derivation, path_to_db
        )
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        list_of_local_id = []

    try:
        list_of_global_id_not_in_derivation = compute.list_global_id_not_in_derivation(
            name_of_derivation, path_to_db
        )
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        list_of_global_id_not_in_derivation = []

    infrules_modified_latex_dict = {}
    for infrule_name, infrule_dict in dat["inference rules"].items():
        # logger.debug(infrule_name + ' has ' + str(infrule_dict))
        # logger.debug(str(list(infrule_dict.keys())))
        infrule_dict["latex"] = infrule_dict["latex"].replace("\\ref", "ref")
        infrules_modified_latex_dict[infrule_name] = infrule_dict
    # logger.debug('infrules_modified_latex_dict =' + str(infrules_modified_latex_dict))

    return render_template(
        "provide_expr_for_inf_rule.html",
        name_of_derivation=name_of_derivation,
        expression_popularity_dict=expression_popularity_dict,
        expressions_dict=dat["expressions"],
        inf_rule_dict=infrules_modified_latex_dict[inf_rule],
        list_of_local_id=list_of_local_id,
        list_of_global_id_not_in_derivation=list_of_global_id_not_in_derivation,
        step_dict=step_dict,
        inf_rule=inf_rule,
        derivation_validity_dict=derivation_validity_dict,
        expr_local_to_gobal=dat["expr local to global"],
        webform=webform,
    )


@app.route(
    "/step_review/<name_of_derivation>/<local_step_id>/", methods=["GET", "POST"],
)
def step_review(name_of_derivation: str, local_step_id: str):
    """
    https://teamtreehouse.com/community/getting-data-from-wtforms-formfield

    >>> step_review
    """
    logger.info("[trace] step_review")

    try:
        step_graphviz_png = compute.create_step_graphviz_png(
            name_of_derivation, local_step_id, path_to_db
        )
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        step_graphviz_png = "error.png"
    dat = clib.read_db(path_to_db)

    if request.method == "POST":
        reslt = request.form
        logger.debug("step_review: reslt = %s", reslt)
        if request.form["submit_button"] == "accept this step; add another step":
            return redirect(
                url_for(
                    "new_step_select_inf_rule", name_of_derivation=name_of_derivation
                )
            )
        if request.form["submit_button"] == "accept this step; review derivation":
            return redirect(
                url_for("review_derivation", name_of_derivation=name_of_derivation,)
            )
        elif request.form["submit_button"] == "modify this step":
            return redirect(
                url_for(
                    "modify_step",
                    name_of_derivation=name_of_derivation,
                    step_id=local_step_id,
                )
            )
        else:
            logger.error('unrecognized button in "step_review":', request.form)
            raise Exception('unrecognized button in "step_review":', request.form)

    if name_of_derivation in dat["derivations"].keys():
        try:
            derivation_validity_dict = compute.determine_derivation_validity(
                name_of_derivation, path_to_db
            )
        except Exception as err:
            logger.error(str(err))
            flash(str(err))
            derivation_validity_dict = {}
        try:
            step_dict = dat["derivations"][name_of_derivation]
        except Exception as err:
            logger.error(str(err))
            flash(str(err))
            step_dict = {}
    else:
        logger.debug(name_of_derivation + "does not exist in derivations")
        derivation_validity_dict = {}
        step_dict = {}

    try:
        expression_popularity_dict = compute.popularity_of_expressions(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        expression_popularity_dict = {}

    # logger.debug('step validity = %s', str(step_validity_dict))

    return render_template(
        "step_review.html",
        name_of_graphviz_png=step_graphviz_png,
        name_of_derivation=name_of_derivation,
        expression_popularity_dict=expression_popularity_dict,
        step_dict=step_dict,
        expr_dict=dat["expressions"],
        expressions_dict=dat["expressions"],
        derivation_validity_dict=derivation_validity_dict,
        expr_local_to_gobal=dat["expr local to global"],
    )


@app.route("/rename_derivation/<name_of_derivation>/", methods=["GET", "POST"])
@login_required
def rename_derivation(name_of_derivation: str):
    """
    >>>
    """
    logger.info("[trace] rename_derivation")
    if request.method == "POST":
        # logger.debug(request.form)
        # ImmutableMultiDict([('revised_text', 'test case 1')])
        if "revised_text" in request.form.keys():
            status_msg = compute.rename_derivation(
                name_of_derivation, request.form["revised_text"], path_to_db
            )
            flash(status_msg)
            return redirect(
                url_for(
                    "review_derivation", name_of_derivation=request.form["revised_text"]
                )
            )
        else:
            logger.error(str(request.form))
            flash("unrecognized option: " + str(request.form))

    return render_template(
        "rename_derivation.html",
        name_of_derivation=name_of_derivation,
        edit_name_webform=RevisedTextForm(request.form),
    )


@app.route("/review_derivation/<name_of_derivation>/", methods=["GET", "POST"])
def review_derivation(name_of_derivation: str):
    """
    >>> review_derivation
    """
    logger.info("[trace] review_derivation")
    pdf_filename = "NONE"
    # caveat: the review_derivation HTML relies on the filename to be "NONE" if there is no PDF
    # TODO: there should be a default PDF in case the generation step fails

    if request.method == "POST":
        if request.form["submit_button"] == "add another step":
            return redirect(
                url_for(
                    "new_step_select_inf_rule", name_of_derivation=name_of_derivation
                )
            )
        elif request.form["submit_button"] == "rename derivation":
            return redirect(
                url_for("rename_derivation", name_of_derivation=name_of_derivation)
            )
        elif request.form["submit_button"] == "edit existing step":
            return redirect(
                url_for(
                    "select_derivation_step_to_edit",
                    name_of_derivation=name_of_derivation,
                )
            )
        elif request.form["submit_button"] == "return to main menu":
            return redirect(url_for("index"))
        elif request.form["submit_button"] == "generate pdf":
            try:
                pdf_filename = compute.generate_pdf_for_derivation(
                    name_of_derivation, path_to_db
                )
            except Exception as err:
                logger.error(str(err))
                flash(str(err))
            return redirect(url_for("static", filename=pdf_filename))
        elif request.form["submit_button"] == "generate tex":
            try:
                tex_filename = compute.generate_tex_for_derivation(
                    name_of_derivation, path_to_db
                )
            except Exception as err:
                logger.error(str(err))
                flash(str(err))
            return redirect(url_for("static", filename=tex_filename))
        elif request.form["submit_button"] == "delete derivation":
            msg = "no action taken"
            try:
                msg = compute.delete_derivation(name_of_derivation, path_to_db)
            except Exception as err:
                flash(str(err))
                logger.error(str(err))
            flash(str(msg))
            return redirect(url_for("index"))
        else:
            flash("[ERROR]  unrecognized button:" + str(request.form))
            logger.error("unrecognized button")

    try:
        derivation_png = compute.create_derivation_png(name_of_derivation, path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        derivation_png = "error.png"

    try:
        d3js_json_filename = compute.create_d3js_json(name_of_derivation, path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        d3js_json_filename = ""
    dat = clib.read_db(path_to_db)

    try:
        derivation_validity_dict = compute.determine_derivation_validity(
            name_of_derivation, path_to_db
        )
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        derivation_validity_dict = {}

    try:
        expression_popularity_dict = compute.popularity_of_expressions(path_to_db)
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        expression_popularity_dict = {}

    return render_template(
        "review_derivation.html",
        pdf_filename=pdf_filename,
        name_of_derivation=name_of_derivation,
        name_of_graphviz_png=derivation_png,
        json_for_d3js=d3js_json_filename,
        step_dict=dat["derivations"][name_of_derivation],
        derivation_validity_dict=derivation_validity_dict,
        expressions_dict=dat["expressions"],
        expression_popularity_dict=expression_popularity_dict,
        expr_local_to_gobal=dat["expr local to global"],
    )


@app.route("/modify_step/<name_of_derivation>/<step_id>/", methods=["GET", "POST"])
@login_required
def modify_step(name_of_derivation: str, step_id: str):
    """
    >>> modify_step('fun deriv', '958242')
    """
    logger.info("[trace] modify_step")

    if request.method == "POST":
        logger.debug("modify_step; request form = %s", request.form)
        if "submit_button" in request.form.keys():
            if request.form["submit_button"] == "change inference rule":
                return redirect(
                    url_for(
                    "new_step_select_inf_rule", name_of_derivation=name_of_derivation
                )
            )

            # https://github.com/allofphysicsgraph/proofofconcept/issues/108
            elif request.form["submit_button"] == "view exploded graph":
                # ImmutableMultiDict([('submit_button', 'view exploded graph')])
                return redirect(url_for("exploded_step", name_of_derivation, step_id))

        # https://github.com/allofphysicsgraph/proofofconcept/issues/116
        elif 'linear_index_to_modify' in request.form.keys():
            # ImmutableMultiDict([('linear_index_to_modify', '0.5')])
            try:
                compute.update_linear_index(name_of_derivation, step_id,
                      request.form['expr_local_id_of_latex_to_modify'], path_to_db)
            except Exception as err:
                flash(str(err))
                logger.error(str(err))

        elif "expr_local_id_of_latex_to_modify" in request.form.keys():
            # request form = ImmutableMultiDict([('edit_expr_latex', '2244'), ('revised_text', 'a = b')])
            try:
                compute.modify_latex_in_step(
                    request.form["expr_local_id_of_latex_to_modify"],
                    request.form["revised_text"],
                    path_to_db,
                )
            except Exception as err:
                flash(str(err))
                logger.error(str(err))

            try:
                step_validity_msg = vir.validate_step(
                    name_of_derivation, step_id, path_to_db
                )
            except Exception as err:
                flash(str(err))
                logger.error(str(err))
                step_validity_msg = ""
            return redirect(
                url_for(
                    "step_review",
                    name_of_derivation=name_of_derivation,
                    local_step_id=step_id,
                )
            )

        else:
            flash("[ERROR] unrecognized button:" + str(request.form))
            logger.error("unrecognized button")


    try:
        derivation_validity_dict = compute.determine_derivation_validity(
            name_of_derivation, path_to_db
        )
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        derivation_validity_dict = {}

    try:
        step_graphviz_png = compute.create_step_graphviz_png(
            name_of_derivation, step_id, path_to_db
        )
    except Exception as err:
        logger.error(str(err))
        flash(str(err))
        step_graphviz_png = "error.png"

    dat = clib.read_db(path_to_db)

    try:
        list_of_new_linear_indices = compute.list_new_linear_indices(
            name_of_derivation, path_to_db
        )
    except Exception as err:
        flash(str(err))
        logger.error(str(err))
        list_of_new_linear_indices = ["none"]

    return render_template(
        "modify_step.html",
        name_of_derivation=name_of_derivation,
        name_of_graphviz_png=step_graphviz_png,
        current_linear_index=dat["derivations"][name_of_derivation][step_id]['linear index'],
        step_dict=dat["derivations"][name_of_derivation],
        local_to_global=dat["expr local to global"],
        derivation_validity_dict=derivation_validity_dict,
        expressions_dict=dat["expressions"],
        list_of_new_linear_indices=list_of_new_linear_indices,
        edit_expr_latex_webform=RevisedTextForm(request.form),
        edit_step_note_webform=RevisedTextForm(request.form),
        expr_local_to_gobal=dat["expr local to global"],
    )

@app.route("/exploded_step/<name_of_derivation>/<step_id>/", methods=["GET", "POST"])
def exploded_step(name_of_derivation: str, step_id:str):
    """
    https://github.com/allofphysicsgraph/proofofconcept/issues/108
    >>> exploded_step()
    """
    try:
        name_of_graphviz_file = compute.generate_graphviz_of_exploded_step(name_of_derivation, step_id, path_to_db)
    except Exception as err:
        flash(str(err))
        logger.error(str(err))
        name_of_graphviz_file = "error.png"

    return render_template("exploded_step.html",
           name_of_derivation=name_of_derivation,
           name_of_graphviz_file=name_of_graphviz_file,
           step_id=step_id)

@app.route("/create_new_inf_rule/", methods=["GET", "POST"])
def create_new_inf_rule():
    """
    >>>
    """
    logger.info("[trace] create_new_inf_rule")
    if request.method == "POST":
        logger.debug("create_new_inf_rule; request.form = %s", request.form)
    return render_template("create_new_inf_rule.html")


if __name__ == "__main__":
    try:
        session_id = compute.create_session_id()
    except Exception as err:
        flash(str(err))
        logger.error(str(err))
        session_id = "0"
    app.run(debug=True, host="0.0.0.0")

# EOF