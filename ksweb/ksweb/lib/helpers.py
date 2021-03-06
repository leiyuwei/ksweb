# -*- coding: utf-8 -*-
"""Template Helpers used in ksweb."""
import logging

from bson import ObjectId
from kajiki import XMLTemplate
from ksweb.lib.utils import id_to_hash, entity_from_id
from ksweb.model.mapped_entity import MappedEntity
from markupsafe import Markup
from datetime import datetime

from ksweb import model
from tg.i18n import lazy_ugettext as l_

# Import commonly used helpers from WebHelpers2 and TG
from tg.util.html import script_json_encode
from ..controllers import partials
log = logging.getLogger(__name__)

try:
    from webhelpers2 import date, html, number, misc, text
except SyntaxError:
    log.error("WebHelpers2 helpers not available with this Python Version")


def material_icon(icon_name):
    icon_code = {
        'delete': '&#xE872;',
        'download': '&#xE2C4;',
        'upload': '&#xE2C6;',
        'print': '&#xE8AD',
        'list': '&#xE896;',
        'arrow_back': '&#xE5C4;',
        'help_outline': '&#xE8FD;',
        'account_circle': '&#xE853',
        'label_outline': '&#xE893;',
        'account_box': '&#xE851;',
        'notification_none': '&#xE7F5;',
        'exit_to_app': '&#xE879;',
        'add': '&#xE145;',
        'insert_drive_file': '&#xE24D;',
        'content_paste': '&#xE14F;',
        'view_day': '&#xE8ED;',
        'save': '&#xE161;',
        'create': '&#xE150;',
        'add_circle_outline': '&#xE148;',
        'add_circle_outline_rotate': '&#xE148;',
        'add_circle': '&#xE147;',
        'remove_circle_outline': '&#xE15D;',
        'clear': '&#xE14C;',
        'done': '&#xE876;',
        'more_horiz': '&#xE5D3;',
        'question_answer': '&#xE8AF',
        'low_priority': '&#xE16D',
        'launch': '&#xe895',
        }
    return Markup('<i class="material-icons media-middle material-icon-%s" '
                  'style="vertical-align: bottom;">%s</i>' % (
                   icon_name, icon_code[icon_name]))


def table_row_content(entity, fields):
    tags = []

    # name of field that you want customize
    css_class = {
        'title': 'type-table-item-title'
    }
    for field in fields:
        data = getattr(entity, field, '')
        if field != '_id':
            converted_value = data
            if type(data) in table_row_content.ROW_CONVERSIONS:
                converters_map = table_row_content.ROW_CONVERSIONS
                convert = converters_map.get(type(data), lambda o: o)
                converted_value = convert(data)

            elif hasattr(entity, '__ROW_TYPE_CONVERTERS__'):
                converters_map = entity.__ROW_TYPE_CONVERTERS__
                convert = converters_map.get(type(data), lambda o: o)
                converted_value = convert(data)

            elif hasattr(entity, '__ROW_COLUM_CONVERTERS__'):
                converters_map = entity.__ROW_COLUM_CONVERTERS__
                convert = converters_map.get(field, lambda o: getattr(o, field))
                converted_value = convert(entity)

        tags.append(html.HTML.td(converted_value, class_=css_class.get(field, 'type-table-item')))
    return html.HTML(*tags)


table_row_content.ROW_CONVERSIONS = {
    model.Workspace: lambda c: c.name,
    model.Precondition: lambda p: p.title,
    bool: lambda b: material_icon('done') if b else material_icon('clear'),
    model.User: lambda u: u.display_name
}


def bootstrap_pager(paginator):
    return html.HTML.ul(paginator.pager(
        page_link_template='<li class="page-item"><a class="page-link"%s>%s</a></li>',
        page_plain_template='<li class="page-item active"%s><span class="page-link">%s</span></li>',
        curpage_attr={'class': 'active'}
    ), class_="pagination justify-content-end")


def editor_widget_template_for_output(**kw):
    return u'@@{id_}'.format(**kw)


def editor_widget_template_for_qa(**kw):
    return u'%%{id_}'.format(**kw)


def underscore(text):
    return text.lower().replace(" ", "_")


def gravatar(email_address, size=200):
    from hashlib import md5
    from tg import url
    mhash = md5(email_address.encode('utf-8')).hexdigest()
    return url('https://www.gravatar.com/avatar/'+mhash, params=dict(s=size))


def get_workspace_name(workspace_id):
    ws = model.Workspace.query.get(_id=ObjectId(workspace_id))
    return ws.name.upper() if ws else l_('HOME')


def dependencies(entity):
    no_message = Markup('<p class="text-muted">No other entity uses this one</p>')
    if not isinstance(entity, MappedEntity):
        return no_message

    deps = entity.dependencies
    if not deps:
        return no_message

    t = XMLTemplate("""
    <div class="list-group list-group-flush">
      <a href='${_.url}' class="list-group-item" py:for="_ in deps">${_.title}</a>
    </div>
    """)
    return Markup(t(dict(deps=deps)).render())


def i2h(_id):
    e = entity_from_id(_id)
    return e.hash
