# -*- coding: utf-8 -*-
from ksweb.model import Qa
from ksweb.tests import TestController
from ksweb import model
from nose.tools import ok_, eq_


class TestQaController(TestController):
    application_under_test = 'main'

    def setUp(self):
        TestController.setUp(self)
        self.workspace = self._get_workspace('Area 1')

    def test_access_permission_not_granted(self):
        self.app.get('/qa/get_all', status=302)

    def test_access_permission_admin(self):
        self._login_admin()
        resp_admin = self.app.get('/qa/get_all', params=dict(workspace=self.workspace._id))
        assert resp_admin.status_code == 200

    def test_access_permission_lawyer(self):
        self._login_lawyer()
        resp_lawyer = self.app.get('/qa/get_all', params=dict(workspace=self.workspace._id))
        assert resp_lawyer.status_code == 200

    def test_new_qua(self):
        self._login_admin()
        resp_admin = self.app.get('/qa/new', params=dict(workspace=self.workspace._id))
        assert resp_admin.status_code == 200

    def test_post_valid_qa_text(self):
        self._login_lawyer()

        workspace1 = self._get_workspace('Area 1')
        qa_text_params = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'text',
            'answers': ''
        }

        resp = self.app.post_json(
            '/qa/post', params=qa_text_params
        ).json
        qa_text = model.Qa.query.get(title=qa_text_params['title'])
        auto_precondition = model.Precondition.query.get(
            title=qa_text_params['title'] + u' \u21d2 was compiled')

        assert qa_text
        assert resp['errors'] is None
        assert auto_precondition

    def test_update_qa(self):
        self._login_lawyer()
        workspace = self._get_workspace('Area 1')
        qa_text_params = {
            'title': 'Title of QA',
            'workspace': str(workspace._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'text',
            'answers': ''
        }
        self.app.post_json('/qa/post', params=qa_text_params)

        qa = self._get_qa_by_title('Title of QA')
        fields = ['title', 'question', 'tooltip', 'link']
        params = {_: qa[_] + ' edited' for _ in fields}
        params['_id'] = str(qa._id)
        params['answer_type'] = qa.type
        params['workspace'] = str(qa.workspace._id)
        response = self.app.put_json('/qa/put', params=params).json

        assert response['redirect_url']
        self.app.get(response['redirect_url'])
        response = self.app.get('/resolve/original_edit', params=dict(workspace=params['workspace']))
        response.follow()

        qa_edited = model.Qa.query.get(title=params['title'])

        assert qa_edited
        assert qa_edited.title == params['title']
        assert qa_edited.workspace._id == qa.workspace._id
        assert qa_edited.question == params['question']
        assert qa_edited.tooltip == params['tooltip']
        assert qa_edited.link == params['link']

    def test_update_qa_with_no_related_entities(self):
        self._login_lawyer()
        workspace = self._get_workspace('Area 1')
        qa_text_params = {
            'title': 'Title of QA',
            'workspace': str(workspace._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'text',
            'answers': ''
        }
        self.app.post_json('/qa/post', params=qa_text_params)
        qa = self._get_qa_by_title(qa_text_params['title'])
        model.Precondition.query.remove({'type': 'simple', 'condition': qa._id})
        fields = ['title', 'question', 'tooltip', 'link']
        params = {_: qa[_] + ' edited' for _ in fields}
        params['_id'] = str(qa._id)
        params['answer_type'] = qa.type
        params['workspace'] = str(qa.workspace._id)
        self.app.put_json('/qa/put', params=params).json
        qa_edited = model.Qa.query.get(title=params['title'])

        assert qa_edited
        assert qa_edited.title == params['title']
        assert qa_edited.workspace._id == qa.workspace._id
        assert qa_edited.question == params['question']
        assert qa_edited.tooltip == params['tooltip']
        assert qa_edited.link == params['link']

    def test_update_removing_answer(self):
        self._login_lawyer()
        workspace = self._get_workspace('Area 1')
        qa_text_params = {
            'title': 'Title of QA',
            'workspace': str(workspace._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'multi',
            'answers': ['Some answer'],
        }
        self.app.post_json('/qa/post', params=qa_text_params)
        qa = self._get_qa_by_title('Title of QA')

        params = dict(
            _id = str(qa._id),
            title = qa.title,
            workspace = str(qa.workspace._id),
            question = qa.question,
            answer_type = qa.type,
            answers = []
        )

        resp = self.app.put_json('/qa/put', params=params, status=412).json
        assert resp['errors'] is not None
        assert resp['errors']['answers'] == "Please add at least one more Answer"

    def test_put_qa_with_not_valid_answers(self):
        self._login_lawyer()
        workspace = self._get_workspace('Area 1')
        qa_text_params = {
            'title': 'Title of QA',
            'workspace': str(workspace._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'single',
            'answers': ''
        }
        self.app.put_json('/qa/put', params=qa_text_params, status=412)
        qa_text_params['answer_type'] = 'multi'
        self.app.put_json('/qa/put', params=qa_text_params, status=412)

    def test_post_valid_qa_single_with_not_valid_answers(self):
        self._login_lawyer()

        workspace1 = self._get_workspace('Area 1')
        qa_text_single_missing_answers = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'single',
            'answers': ''
        }

        resp = self.app.post_json(
            '/qa/post', params=qa_text_single_missing_answers, status=412
        ).json
        assert resp['errors']['answers'] == "Please add at least one more Answer"

        qa_text_single_missing_one_answers = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'single',
            'answers': ['First']
        }
        resp = self.app.post_json(
            '/qa/post', params=qa_text_single_missing_one_answers, status=412
        ).json
        assert resp['errors']['answers'] == "Please add at least one more Answer"

    def test_post_valid_qa_single(self):
        self._login_lawyer()

        workspace1 = self._get_workspace('Area 1')

        qa_text_single = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'single',
            'answers': ['First', 'Second']
        }
        resp = self.app.post_json(
            '/qa/post', params=qa_text_single,
        ).json

        qa_single = model.Qa.query.get(title=qa_text_single['title'])
        assert qa_single
        assert resp['errors'] is None

    def test_post_valid_qa_multi_with_not_valid_answers(self):
        self._login_lawyer()
        workspace1 = self._get_workspace('Area 1')
        qa_text_multi_missing_answers = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'multi',
            'answers': ''
        }

        resp = self.app.post_json(
            '/qa/post', params=qa_text_multi_missing_answers, status=412
        )
        errors = resp.json['errors']
        assert errors['answers'] == "Please add at least one more Answer", errors

    def test_post_valid_qa_multi_with_one_answer(self):
        self._login_lawyer()
        workspace1 = self._get_workspace('Area 1')
        qa_text_multi_one_answers = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'multi',
            'answers': ['First']
        }
        resp = self.app.post_json(
            '/qa/post', params=qa_text_multi_one_answers
        )
        errors = resp.json['errors']
        qa_multi = model.Qa.query.get(title=qa_text_multi_one_answers['title'])
        assert qa_multi
        assert errors is None

    def test_post_valid_qa_multi(self):
        self._login_lawyer()

        workspace1 = self._get_workspace('Area 1')

        qa_text_multi = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': 'multi',
            'answers': ['First', 'Second']
        }

        resp = self.app.post_json(
            '/qa/post', params=qa_text_multi,
        )
        errors = resp.json['errors']

        qa_multi = model.Qa.query.get(title=qa_text_multi['title'])
        assert qa_multi
        assert errors is None

    def test_get_one(self):
        self._login_lawyer()

        workspace1 = self._get_workspace('Area 1')

        qa_text_multi = {
            'title': 'Title of QA',
            'workspace': str(workspace1._id),
            'question': 'Text of the question',
            'tooltip': 'Tooltip of QA1',
            'link': 'http://www.axant.it',
            'answer_type': "multi",
            'answers': ['First', 'Second']
        }

        self.app.post_json('/qa/post', params=qa_text_multi)

        qa = model.Qa.query.get(title=qa_text_multi['title'])

        resp = self.app.get('/qa/get_one', params={'id': str(qa._id)}).json
        assert resp['qa']['title'] == qa_text_multi['title']
        assert str(resp['qa']['_workspace']) == qa_text_multi['workspace']
        assert resp['qa']['question'] == qa_text_multi['question']
        assert resp['qa']['tooltip'] == qa_text_multi['tooltip']
        assert resp['qa']['link'] == qa_text_multi['link']
        assert resp['qa']['type'] == qa_text_multi['answer_type'], (resp, qa_text_multi)
        assert resp['qa']['answers'] == qa_text_multi['answers']

        assert resp['qa']['_id'] == str(qa._id), "%s - %s" % (resp['qa']['_id'], qa._id)

    def test_valid_options(self):
        self._login_lawyer()

        self.test_post_valid_qa_text()
        self.test_post_valid_qa_multi()
        self.test_post_valid_qa_single()

        resp = self.app.get('/qa/valid_options',
                            params=dict(workspace=self.workspace._id)).json
        assert len(resp['questions']) == 3

    def test_human_readable_details(self):
        self._login_lawyer()
        qa = self._create_fake_qa("fake_qa")
        resp = self.app.get('/qa/human_readable_details', params={'_id': qa._id})
        assert str(qa._id) in resp

    def test_qa_edit_no_workspace(self):
        self._login_lawyer()
        qa = self._create_fake_qa("fake_qa")
        non_existent_workspace_id = qa._id
        self.app.get('/qa/edit', params=dict(
            _id=qa._id,
            workspace=non_existent_workspace_id,
        ), status=404)

    def test_qa_edit(self):
        self._login_lawyer()
        qa = self._create_fake_qa("fake_qa")
        response = self.app.get('/qa/edit', params=dict(
            _id=qa._id,
            workspace=qa.workspace._id
        ), status=200)
        assert str(qa._id) in response

    def test_qa_export(self):
        self._login_lawyer()
        qa = self._create_fake_qa("fake_qa")
        items = qa.export_items()
        eq_(list(items)[0], qa)

    def test_qa_export_with_filter(self):
        self._login_lawyer()
        ws = self._get_workspace('Area 1')
        qa = self._create_fake_qa("a question", qa_type=Qa.TYPES.TEXT)
        _filter = self._create_simple_precondition('love boat title', str(ws._id), str(qa._id))
        qa.parent_precondition = _filter
        items = qa.export_items()
        eq_(len(items), 3)
        ok_(qa in items)
        ok_(_filter in items)
