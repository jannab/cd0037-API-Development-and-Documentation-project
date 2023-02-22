import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page -1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def get_categories_dictionary(selection):
    categories = {}

    for category in selection:
        categories.update({category.id: category.type})

    return categories


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,DELETE,POST,OPTIONS"
        )
        return response

    @app.route("/categories", methods=["GET"])
    @cross_origin()
    def retrieve_categories():
        selection = Category.query.order_by(Category.id).all()
        categories = get_categories_dictionary(selection)

        if len(categories) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "categories": categories,
            }
        )

    @app.route("/questions", methods=["GET"])
    @cross_origin()
    def retrieve_questions():
        question_selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, question_selection)
        category_selection = Category.query.order_by(Category.id).all()
        categories = get_categories_dictionary(category_selection)
        current_category = "ALL"

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "totalQuestions": len(Question.query.all()),
                "categories": categories,
                "currentCategory": current_category,
            }
        )

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    @cross_origin()
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            question.delete()

            return jsonify(
                    {
                        "success": True,
                        "deletedQuestionId": question_id,
                    }
                )
        except:
            abort(422)

    @app.route("/questions", methods=["POST"])
    @cross_origin()
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_category = body.get("category", None)
        new_difficulty = body.get("difficulty", None)
        search = body.get("searchTerm", None)

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search)))
                current_questions = paginate_questions(request, selection)

                current_category = "ALL"

                return jsonify(
                        {
                            "success": True,
                            "questions": current_questions,
                            "totalQuestions": len(Question.query.all()),
                            "currentCategory": current_category,
                        }
                    )
            else:
                question = Question(question=new_question,
                                    answer=new_answer,
                                    category=new_category,
                                    difficulty=new_difficulty)
                question.insert()

                return jsonify(
                        {
                            "success": True,
                            "createdQuestionId": question.id,
                        }
                    )

        except:
            abort(422)

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    @cross_origin()
    def retrieve_questions_for_category(category_id):
        question_selection = Question.query.order_by(Question.id).filter(
                                Question.category == category_id)
        current_questions = paginate_questions(request, question_selection)
        current_category = Category.query.filter(
            Category.id == category_id).one_or_none()

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "totalQuestions": len(Question.query.all()),
                "currentCategory": current_category.type,
            }
        )

    @app.route("/quizzes", methods=["POST"])
    @cross_origin()
    def get_next_question():
        body = request.get_json()

        previous_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)

        question_selection = Question.query.order_by(Question.id).all()

        # use category if given
        if quiz_category and "id" in quiz_category:
            # check if category is ALL
            if quiz_category["id"] != 0:
                question_selection = Question.query.order_by(
                    Question.id).filter(
                    Question.category == quiz_category["id"])

        available_questions = [question.id for question in question_selection]

        # make sure previous questions are not available
        if previous_questions:
            available_questions = [
                question for question in available_questions
                if question not in previous_questions
                ]

        if len(available_questions) == 0:
            abort(404)

        next_question_id = random.choice(available_questions)
        next_question = Question.query.filter(
            Question.id == next_question_id).one_or_none()

        return jsonify(
            {
                "question": next_question.format(),
                "success": True
            }
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                "success": False,
                "error": 404,
                "message": "resource not found",
            }), 404
        )

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({
                "success": False,
                "error": 405,
                "message": "method not allowed",
            }), 405
        )

    @app.errorhandler(422)
    def not_found(error):
        return (
            jsonify({
                "success": False,
                "error": 422,
                "message": "unprocessable",
            }), 422
        )

    @app.errorhandler(500)
    def not_found(error):
        return (
            jsonify({
                "success": False,
                "error": 500,
                "message": "internal server error",
            }), 500
        )

    return app
