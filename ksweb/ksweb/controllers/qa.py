# -*- coding: utf-8 -*-
"""Qa controller module"""

from bson import ObjectId
from ksweb.lib.predicates import CanManageEntityOwner
from ksweb.lib.utils import to_object_id, hash_to_id
from tg import expose, validate, validation_errors_response, response, RestController, \
    decode_params, request, tmpl_context, session, flash, lurl, redirect
import tg
from tg.decorators import paginate, require
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg import predicates
from tw2.core import StringLengthValidator, OneOfValidator
from ksweb.model import Workspace, Precondition, Qa, DBSession
from ksweb.lib.validator import WorkspaceExistValidator, QAExistValidator, PreconditionExistValidator


class QaController(RestController):
    def _before(self, *args, **kw):
        tmpl_context.sidebar_section = "qas"

    allow_only = predicates.not_anonymous(msg=l_('Only for admin or lawyer'))

    @expose('ksweb.templates.qa.index')
    @paginate('entities', items_per_page=int(tg.config.get('pagination.items_per_page')))
    @validate({'workspace': WorkspaceExistValidator(required=True), },
              error_handler=validation_errors_response)
    def get_all(self, workspace, **kw):
        return dict(
            page='qa-index',
            fields={
                'columns_name': [_('Label'), _('Question'), _('Filter'), _('Id')],
                'fields_name': 'title question parent_precondition hash'.split()
            },
            entities=Qa.available_for_user(request.identity['user']._id, workspace),
            actions=False,
            workspace=workspace
        )

    @expose('json')
    @validate({
        'id': QAExistValidator(required=True),
    }, error_handler=validation_errors_response)
    def get_one(self, id,  **kw):
        id = hash_to_id(id, Qa)
        return dict(qa=Qa.by_id(id))

    @expose('json')
    @validate({'workspace': WorkspaceExistValidator(required=True)})
    def valid_options(self, workspace):
        questions = Qa.available_for_user(request.identity['user']._id, workspace)
        return dict(questions=[{'_id': qa._id, 'title': qa.title} for qa in questions])

    @expose('json')
    @expose('ksweb.templates.qa.new')
    @validate({'workspace': WorkspaceExistValidator(required=True), })
    def new(self, workspace, **kw):
        return dict(errors=None, workspace=workspace, referrer=kw.get('referrer'),
                    qa={'question': kw.get('question_content', None),
                        'title': kw.get('question_title', None),
                        '_parent_precondition': kw.get('precondition_id', None)})

    @decode_params('json')
    @expose('json')
    @validate({
        'title': StringLengthValidator(min=2),
        'workspace': WorkspaceExistValidator(required=True),
        'question': StringLengthValidator(min=2),
        'tooltip': StringLengthValidator(min=0, max=100),
        'link': StringLengthValidator(min=0, max=100),
        'answer_type': OneOfValidator(values=Qa.QA_TYPE, required=True),
        'precondition': PreconditionExistValidator(required=False),
    }, error_handler=validation_errors_response)
    def post(self, title, workspace, question, tooltip, link, answer_type, precondition=None, answers=None, **kw):
        if not self._are_answers_valid(answer_type, answers):
            response.status_code = 412
            return dict(errors={'answers': _('Please add at least one more answer')})

        user = request.identity['user']

        qa = Qa(
                _owner=user._id,
                _workspace=ObjectId(workspace),
                _parent_precondition=to_object_id(precondition),
                title=title,
                question=question,
                tooltip=tooltip,
                link=link,
                type=answer_type,
                answers=answers,
                auto_generated=False,
                public=True,
                visible=True
            )
        DBSession.flush(qa)
        qa.generate_output_from()

        return dict(errors=None, _id=ObjectId(qa._id))

    @decode_params('json')
    @expose('json')
    @validate({
        '_id': QAExistValidator(required=True),
        'title': StringLengthValidator(min=2),
        'workspace': WorkspaceExistValidator(required=True),
        'question': StringLengthValidator(min=2),
        'tooltip': StringLengthValidator(min=0, max=100),
        'link': StringLengthValidator(min=0, max=100),
        'answer_type': OneOfValidator(values=Qa.QA_TYPE, required=True),
        'precondition': PreconditionExistValidator(required=False),
    }, error_handler=validation_errors_response)
    def put(self, _id, title, workspace, question, tooltip, link, answer_type, precondition=None, answers=None, **kw):
        if not self._are_answers_valid(answer_type, answers):
            response.status_code = 412
            return dict(errors={'answers': _('Please add at least one more answer')})

        check = self.get_related_entities(_id)

        if check.get("entities"):
            entity = dict(
                _id=_id,
                _workspace=workspace,
                title=title,
                entity='qa',
                question=question,
                tooltip=tooltip,
                link=link,
                auto_generated=False,
                type=answer_type,
                _parent_precondition=precondition,
                answers=answers
            )

            session.data_serializer = 'pickle'
            session['entity'] = entity  # overwrite always same key for avoiding conflicts
            session.save()

            return dict(redirect_url=tg.url('/resolve', params=dict(workspace=workspace)))

        qa = Qa.upsert({'_id': ObjectId(_id)}, dict(
            _workspace=ObjectId(workspace),
            _parent_precondition=to_object_id(precondition),
            title=title,
            question=question,
            auto_generated=False,
            tooltip=tooltip,
            link=link,
            type=answer_type,
            answers=answers
        ))
        DBSession.flush(qa)
        qa.generate_output_from()
        return dict(errors=None)

    @expose('ksweb.templates.qa.new')
    @validate({
        '_id': QAExistValidator(model=True)
    }, error_handler=validation_errors_response)
    @require(CanManageEntityOwner(msg=l_(u'You can not edit this Q/A'), field='_id', entity_model=Qa))
    def edit(self, _id, workspace=None, **kw):
        ws = Workspace.query.find({'_id': ObjectId(workspace)}).first()
        if not ws:
            return tg.abort(404)
        qa = Qa.query.find({'_id': ObjectId(_id)}).first()
        return dict(qa=qa, workspace=ws._id, errors=None)

    @expose('json')
    @decode_params('json')
    @validate({
        '_id': QAExistValidator(required=True),
    }, error_handler=validation_errors_response)
    def human_readable_details(self, _id, **kw):
        qa = Qa.query.find({'_id': ObjectId(_id)}).first()
        return dict(qa=qa)

    @decode_params('json')
    @expose('json')
    def get_related_entities(self, _id):
        """
        This method return ALL entities (Precondition simple) that have inside the given _id
        :param _id:
        :return:
        """
        entities = Precondition.query.find({'type': Precondition.TYPES.SIMPLE, 'condition': ObjectId(_id)}).all()
        return {
            'entities': entities,
            'len': len(entities)
        }

    def _are_answers_valid(self, answer_type, answers):
        if (answer_type == Qa.TYPES.SINGLE and len(answers) < 2) or\
           (answer_type == Qa.TYPES.MULTI and len(answers) < 1):
            return False
        return True

    @expose('json')
    @validate({'workspace': WorkspaceExistValidator(required=True)})
    def mark_as_read(self, workspace):
        Qa.mark_as_read(request.identity['user']._id, workspace)
