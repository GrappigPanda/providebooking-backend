import logging
import uuid

from flask.views import MethodView
from flask import current_app as app, jsonify, request

from marshmallow.fields import Boolean, Int, DateTime, String
from webargs.flaskparser import parser

from almanac.DAOs.schedule_dao import ScheduleDAO
from almanac.schemas.return_schemas import ScheduleMarshal


class Schedules(MethodView):
    """Houses CRUD operations for schedule management."""

    def get(self, user_id):
        arg_fields = {
            'time_period_offset': Int(missing=0)
        }
        args = parser.parse(arg_fields)

        schedule_info = ScheduleDAO().get(
            user_id,
            time_period_offset=args.get('time_period_offset', 0)
        )

        logging.info(
            'Succesfully retrieved all schedules for user {0}'.format(
                user_id
            )
        )

        return jsonify({
            'schedules': ScheduleMarshal(many=True).dump(schedule_info).data
            }
        )

    def post(self, user_id):
        arg_fields = {
            'start_time': DateTime(required=True),
            'end_time': DateTime(required=True),
            'title': String(required=True),
        }
        args = parser.parse(arg_fields)

        schedule_info = ScheduleDAO().post(
            args['start_time'],
            args['end_time'],
            user_id,
        )

        logging.info(
            'Succesfully created new schedule for user {0}'
            'with new times {1} to {2}'.format(
                user_id,
                args['start_time'],
                args['end_time']
            )
        )

        return jsonify(ScheduleMarshal().dump(schedule_info).data)


class GetSchedule(MethodView):
    def get(self, schedule_id):
        arg_fields = {
            'time_period_offset': Int(missing=0)
        }
        args = parser.parse(arg_fields)

        schedule_info = ScheduleDAO().get_by_schedule_id(
            schedule_id
        )

        logging.info(
            'Successfully retrieved schedule ({0}?).'.format(
                schedule_id,
            )
        )

        return jsonify(ScheduleMarshal().dump(schedule_info).data)


class ModifySchedule(MethodView):
    def get(self, user_id, schedule_id):
        arg_fields = {
            'time_period_offset': Int(missing=0)
        }
        args = parser.parse(arg_fields)

        schedule_info = ScheduleDAO().get_by_schedule_id(
            schedule_id
        )

        logging.info(
            'Successfully retrieved schedule ({0}?) for user {1}'.format(
                schedule_id,
                user_id
            )
        )

        return jsonify({
            'schedules': ScheduleMarshal().dump(schedule_info).data
        })

    def put(self, user_id, schedule_id):
        arg_fields = {
            'start_time': DateTime(required=True),
            'end_time': DateTime(required=True)
        }
        args = parser.parse(arg_fields)

        schedule_info = ScheduleDAO().put(
            schedule_id,
            args['start_time'],
            args['end_time'],
            user_id,
        )

        logging.info(
            'Successfully updated schedule schedule ({0}?) for user {1}'
            'with new times {2} to {3}'.format(
                schedule_id,
                user_id,
                args['start_time'],
                args['end_time']
            )
        )

        return jsonify(ScheduleMarshal().dump(schedule_info).data)

    def delete(self, user_id, schedule_id):
        schedule_info = ScheduleDAO().delete(
            user_id,
            schedule_id
        )

        logging.info(
            'Successfully deleted schedule schedule ({0}?) for user {1}'.format(
                schedule_id,
                user_id
            )
        )

        return jsonify(ScheduleMarshal().dump(schedule_info).data)


def export_routes(_app):
    _app.add_url_rule(
        '/schedules/<string:user_id>',
        view_func=Schedules.as_view('api_v1_schedules'),
    )

    _app.add_url_rule(
        '/schedule/<string:schedule_id>',
        view_func=GetSchedule.as_view('api_v1_get_schedule')
    )

    _app.add_url_rule(
        '/schedules/<string:user_id>/<string:schedule_id>',
        view_func=ModifySchedule.as_view('api_v1_modify_schedule')
    )

