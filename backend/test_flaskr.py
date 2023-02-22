import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}/{}".format(
            'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

        self.new_question = {
            "question_text": "Where was Julius Caesar born?",
            "answer": "Rome",
            "category": 4,
            "difficulty": 2
        }

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["categories"])

    def test_405_sent_using_delete_method(self):
        res = self.client().delete("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "method not allowed")

    def test_get_paginated_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["currentCategory"])
        self.assertTrue(data["categories"])
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(data["questions"])

    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get("/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_get_questions_for_category(self):
        res = self.client().get("/categories/2/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["currentCategory"])
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(data["questions"])

    def test_404_sent_getting_questions_for_category(self):
        res = self.client().get("/categories/1000/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_delete_question(self):
        new_question = Question(question=self.new_question["question_text"],
                                answer=self.new_question["answer"],
                                category=self.new_question["category"],
                                difficulty=self.new_question["difficulty"])
        new_question.insert()
        question_id = new_question.id

        res = self.client().delete(f"/questions/{question_id}")
        data = json.loads(res.data)

        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["deletedQuestionId"], question_id)
        self.assertEqual(question, None)

    def test_422_sent_deleting_non_existing_question(self):
        question_id = 1000
        res = self.client().delete(f"/questions/{question_id}")
        data = json.loads(res.data)

        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")

    def test_get_next_question_with_result(self):
        input = {"previous_questions": [1, 2],
                 "quiz_category": {"type": "Art", "id": 2}}
        res = self.client().post("/quizzes", json=input)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["question"])

    def test_get_next_question_for_all_categories(self):
        input = {"previous_questions": [1, 2],
                 "quiz_category": {"type": "click", "id": 0}}
        res = self.client().post("/quizzes", json=input)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["question"])

    def test_404_get_next_question_without_result(self):
        input = {"previous_questions": [1, 2],
                 "quiz_category": {"type": "Applejack", "id": 500}}
        res = self.client().post("/quizzes", json=input)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_create_new_question(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["createdQuestionId"])

    def test_405_trying_to_create_question_with_id(self):
        res = self.client().post("/questions/1", json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "method not allowed")

    def test_get_question_search_with_results(self):
        search_term = {"searchTerm": "name"}
        res = self.client().post("/questions", json=search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["questions"])
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(data["currentCategory"])

    def test_get_question_search_without_results(self):
        search_term = {"searchTerm": "muhahahahaha"}
        res = self.client().post("/questions", json=search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["questions"]), 0)
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(data["currentCategory"])



# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
