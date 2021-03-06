from __future__ import absolute_import
from ksweb import model
from ksweb.model import DBSession
from ksweb.tests import TestController
from ksweb.lib.validator import WorkspaceExistValidator, QAExistValidator, DocumentExistValidator, \
    PreconditionExistValidator, DocumentContentValidator, OutputExistValidator, OutputContentValidator, \
    QuestionaryExistValidator
from nose.tools import eq_
from tg.util.webtest import test_context
from tw2.core import ValidationError
from .test_document import TestDocument


class TestValidators(TestController):
    application_under_test = 'main'

    def test_qa_exist_validator(self):
        self._login_lawyer()
        workspace1 = self._get_workspace('Area 1')
        qa_params = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'single',
            'answers': ['Risposta1', 'Risposta2', 'Risposta3']
        }
        qa = self._create_qa(qa_params['title'], qa_params['workspace'], qa_params['question'], qa_params['tooltip'], qa_params['link'], qa_params['answer_type'], qa_params['answers'])

        validator = QAExistValidator()
        try:
            res = validator._validate_python(str(qa._id))
        except ValidationError:
            assert False
        else:
            assert True

    def test_qa_exist_validator_with_obj_not_valid(self):
        with test_context(self.app):
            validator = QAExistValidator()
            try:
                res = validator._validate_python('not_obj_id')
            except ValidationError:
                assert True
            else:
                assert False

    def test_qa_exist_validator_with_not_existing_qa(self):
        with test_context(self.app):
            validator = QAExistValidator()
            try:
                res = validator._validate_python('5757ce79c42d752bde919318')
            except ValidationError:
                assert True
            else:
                assert False

    def test_workspace_exist_validator(self):
        workspace1 = self._get_workspace('Area 1')
        validator = WorkspaceExistValidator()
        try:
            res = validator._validate_python(str(workspace1._id))
        except ValidationError:
            assert False
        else:
            assert True

    def test_workspace_exist_validator_with_obj_not_valid(self):
        with test_context(self.app):
            validator = WorkspaceExistValidator()
            try:
                res = validator._validate_python('not_obj_id')
            except ValidationError:
                assert True
            else:
                assert False

    def test_workspace_exist_validator_with_not_existing_workspace(self):
        with test_context(self.app):
            validator = WorkspaceExistValidator()
            try:
                res = validator._validate_python('5757ce79c42d752bde919318')
            except ValidationError:
                assert True
            else:
                assert False

    def test_document_exist_validator(self):
        model.Document(
            _owner=self._get_user('lawyer1@ks.axantweb.com')._id,
            _workspace=self._get_workspace('Area 1')._id,
            title="Titolone",
            html='',
            public=True,
            visible=True
        )
        DBSession.flush()
        document = model.Document.query.get(title="Titolone")
        validator = DocumentExistValidator()
        try:
            res = validator._validate_python(str(document._id))
        except ValidationError:
            assert False
        else:
            assert True

    def test_document_not_exist_validator(self):
        with test_context(self.app):
            validator = DocumentExistValidator()
            try:
                res = validator._validate_python("5757ce79c42d752bde919318")
            except ValidationError:
                assert True
            else:
                assert False

    def test_document_invalid_id_validator(self):
        with test_context(self.app):
            validator = DocumentExistValidator()
            try:
                res = validator._validate_python("Invalid")
            except ValidationError:
                assert True
            else:
                assert False

    def test_precondition_exist_invalid_id_validator(self):
        with test_context(self.app):
            validator = PreconditionExistValidator()
            try:
                res = validator._validate_python("Invalid")
            except ValidationError:
                assert True
            else:
                assert False

    def test_output_exist_validator(self):
        model.Output(
            title="Fake_output",
            html='',
            _owner=self._get_user('lawyer1@ks.axantweb.com')._id,
            _workspace=self._get_workspace('Area 1')._id,
            _precondition=None
        )
        DBSession.flush()
        output = model.Output.query.get(title="Fake_output")
        validator = OutputExistValidator()
        try:
            res = validator._validate_python(str(output._id))
        except ValidationError:
            assert False
        else:
            assert True

    def test_output_not_exist_validator(self):
        with test_context(self.app):
            validator = OutputExistValidator()
            try:
                res = validator._validate_python("5757ce79c42d752bde919318")
            except ValidationError as v:
                eq_(v.message, 'Output does not exists')
            else:
                assert False

    def test_output_invalid_id_validator(self):
        with test_context(self.app):
            validator = OutputExistValidator()
            try:
                res = validator._validate_python("Invalid")
            except ValidationError:
                assert True
            else:
                assert False

    def test_output_content_validator(self):
        self._login_lawyer()
        qa1 = self._create_qa('FakeQa1', self._get_workspace('Area 1')._id, 'Di che sesso sei', 'tooltip', 'link',
                              'text', '')

        with test_context(self.app):

            validator = OutputContentValidator()
            try:
                res = validator._validate_python("@{%s}" % str(qa1.hash))
            except ValidationError:
                assert False
            else:
                assert True

    def test_output_content_validator_invalid_output(self):
        with test_context(self.app):
            validator = OutputContentValidator()
            try:
                res = validator._validate_python("Buongiorno @{5757ce79c42d752bde919318}")
            except ValidationError as v:
                eq_(v.message, 'Question not found.')
            else:
                assert False

    def test_output_content_validator_invalid_type_output(self):
        with test_context(self.app):
            validator = OutputContentValidator()
            try:
                res = validator._validate_python("Buongiorno")
            except ValidationError:
                assert False
            else:
                assert True

    def test_document_content_validator(self):
        with test_context(self.app):
            model.Output(
                title="FakeOutput",
                html='',
                _owner=self._get_user('lawyer1@ks.axantweb.com')._id,
                _workspace=self._get_workspace('Area 1')._id,
                _precondition=None,
            )
            DBSession.flush()
            output = model.Output.query.get(title="FakeOutput")

            validator = DocumentContentValidator()
            try:
                res = validator._validate_python('#{%s}' % str(output.hash))
            except ValidationError:
                assert False
            else:
                assert True

    def test_output_content_validator_with_invalid_output(self):
        with test_context(self.app):
            validator = OutputContentValidator()
            try:
                res = validator._validate_python("Buongiorno #{5757ce79c42d752bde919318}")
            except ValidationError:
                assert True
            else:
                assert False

    def test_document_content_validator_invalid_output(self):
        with test_context(self.app):
            validator = DocumentContentValidator()
            try:
                res = validator._validate_python("Buongiorno #{5757ce79c42d752bde919318}")
            except ValidationError:
                assert True
            else:
                assert False

    def test_output_content_validator_invalid_answer(self):
        with test_context(self.app):
            validator = OutputContentValidator()
            try:
                res = validator._validate_python("Buongiorno @{5757ce79c42d752bde919318}")
            except ValidationError:
                assert True
            else:
                assert False

    def test_document_content_validator_without_output(self):
        with test_context(self.app):
            validator = DocumentContentValidator()
            try:
                res = validator._validate_python("Buongiorno")
            except ValidationError:
                assert False
            else:
                assert True

    def test_questionary_exist_validator(self):
        self._login_lawyer()
        fake_questionary = self._create_fake_questionary('Test_validator')
        validator = QuestionaryExistValidator()
        try:
            res = validator._validate_python(str(fake_questionary._id))
        except ValidationError:
            assert False
        else:
            assert True

    def test_questionary_not_exist_validator(self):
        with test_context(self.app):
            validator = QuestionaryExistValidator()
            try:
                res = validator._validate_python("5757ce79c42d752bde919318")
            except ValidationError:
                assert True
            else:
                assert False

    def test_questionary_invalid_id_validator(self):
        with test_context(self.app):
            validator = QuestionaryExistValidator()
            try:
                res = validator._validate_python("Invalid")
            except ValidationError:
                assert True
            else:
                assert False
