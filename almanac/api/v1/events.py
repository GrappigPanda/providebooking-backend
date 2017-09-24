import logging
import pytz

from flask.views import MethodView
from flask import jsonify, current_app, g
from marshmallow import validate
from marshmallow.fields import Boolean, Int, String
from webargs.flaskparser import parser

from almanac.DAOs.event_dao import EventDAO
from almanac.exc.exceptions import EndpointException
from almanac.facades.paid_event_facade import EventFacade
from almanac.schemas.return_schemas import EventMarshal, UserMarshal, \
    UserSanitizedMarshal
from almanac.utils.security import authentication_required


class Events(MethodView):
    """Houses CRUD operations for event management."""

    @authentication_required
    def get(self, user_id):
        arg_fields = {
            'is_scheduling': Boolean(required=True),
            'time_period_offset': Int(missing=0)
        }
        args = parser.parse(arg_fields)

        if args['is_scheduling']:
            event_info = EventDAO().get_for_scheduling_user(
                user_id,
                args['time_period_offset']
            )
        else:
            event_info = EventDAO().get_for_scheduled_user(
                user_id,
                args['time_period_offset']
            )

        logging.info('Retrieved all events for user {0} as a {1}'.format(
            user_id,
            'scheduler.' if args['is_scheduling'] else 'scheduling user.'
        ))

        return jsonify({'events': EventMarshal(many=True).dump(event_info).data})


class EventCreate(MethodView):
    @staticmethod
    def post():
        arg_fields = {
            'scheduled_user_id': String(required=True),
            'localized_start_time': String(required=True),
            'localized_end_time': String(required=True),
            'local_tz': String(
                required=True,
                validate=validate.OneOf(pytz.all_timezones)
            ),
            'notes': String(
                required=False,
                validate=validate.Length(max=512),
                missing=None,
                default=None
            ),
            'is_paid': Boolean(default=True, missing=True),
            'nonce': String(
                required=False,
                default='',
                missing='',
            ),
            'address_id': String(
                required=False,
            )
        }
        args = parser.parse(arg_fields)
        args['scheduling_user_id'] = g.user_info['user_id']

        if args['is_paid']:
            if args.get('nonce') is None or args.get('nonce') == '':
                raise EndpointException(
                    'For paid scheduling, a payment nonce must be supplied.'
                )

            del args['is_paid']
            event_info = EventFacade().create_new_event(**args)
        else:
            if not current_app.config.get('TESTING'):
                logging.error(
                    'Attempted to create unpaid event in prod: {0}'.format(
                        args
                    )
                )
                raise EndpointException(
                    'Non-paid events are not allowed.'
                )

            del args['is_paid']
            del args['nonce']
            event_info = EventDAO().create_new_event(
                **args
            )

        logging.info(
            'Created event for user {0} with user {1} for time range: {2}->{3}'
            'at timezone {4}.',
            args['scheduling_user_id'],
            args['scheduling_user_id'],
            args['localized_start_time'],
            args['localized_end_time'],
            args['local_tz']
        )

        return jsonify(EventMarshal().dump(event_info).data)


class Event(MethodView):
    """Allows retrieval of a single event."""

    @authentication_required
    def get(self, user_id, event_id):
        event_info = EventDAO().get_by_event_id(user_id, event_id)

        logging.info('Retrieved event {0} for user {1}'.format(
            event_id,
            user_id
        ))

        scheduled = [x for x in event_info if x.public_id == event_info.EventTable.scheduled_user_id]
        scheduling = [x for x in event_info if x.public_id == event_info.EventTable.scheduling_user_id]

        return jsonify({
            'event': EventMarshal().dump(event_info.EventTable).data,
            'scheduled_user': UserSanitizedMarshal().dump(scheduled[0]).data,
            'scheduling_user': UserMarshal().dump(scheduling[0]).data,
        })


def export_routes(_app):
    _app.add_url_rule(
        '/events/<string:user_id>',
        view_func=Events.as_view('api_v1_events')
    )

    _app.add_url_rule(
        '/events/',
        view_func=EventCreate.as_view('api_v1_event_create')
    )

    _app.add_url_rule(
        '/event/<string:user_id>/<string:event_id>',
        view_func=Event.as_view('api_v1_event')
    )