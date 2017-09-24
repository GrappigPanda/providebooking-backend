from marshmallow import Schema, fields
from marshmallow import post_dump, pre_dump
from marshmallow import validate


class _BaseSchema(Schema):
    public_id = fields.String()

    @post_dump
    def replace_with_none(self, data):
        for k in self.fields.keys():
            if not data.get(k, False):
                data[k] = None

        if isinstance(self, UserMarshal) \
                and data['user_id'] is None:
            data['user_id'] = data.get('public_id', 'test!')

        return data


class UserSanitizedMarshal(_BaseSchema):
    is_premium = fields.Boolean()
    five_min_price = fields.Float()
    fifteen_min_price = fields.Float()
    thirty_min_price = fields.Float()
    sixty_min_price = fields.Float()
    local_tz = fields.String()
    user_id = fields.String()
    username = fields.String()


class UserMarshal(UserSanitizedMarshal):
    email = fields.String()
    has_deposit_account = fields.Bool(missing=False, default=False)
    is_approved = fields.Bool(missing=False, default=False)
    is_rejected = fields.Bool(missing=False, default=False)
    service_fee_percent = fields.Float()


class SubscriptionMarshal(_BaseSchema):
    plan_id = fields.String()
    date_started = fields.DateTime()
    date_ended = fields.DateTime()


class ScheduleMarshal(_BaseSchema):
    user_id = fields.String()
    utc_open = fields.DateTime()
    utc_end = fields.DateTime()
    local_tz = fields.String()
    local_tz_open = fields.DateTime()
    local_tz_end = fields.DateTime()
    day_number = fields.Int()


class EventMarshal(_BaseSchema):
    scheduling_user_id = fields.String()
    scheduled_user_id = fields.String()

    utc_start = fields.DateTime()
    scheduled_tz_start = fields.DateTime()
    scheduled_tz_end = fields.DateTime()
    scheduling_tz_start = fields.DateTime()
    scheduling_tz_end = fields.DateTime()
    utc_end = fields.DateTime()

    day_number = fields.Int()
    duration = fields.Int()
    total_price = fields.Float()

    notes = fields.String()


class AddressMarshal(_BaseSchema):
    first_name = fields.String()
    last_name = fields.String()
    street_address = fields.String()
    extended_address = fields.String()
    locality = fields.String()
    region = fields.String()
    postal_code = fields.String()
    country_code_alpha2 = fields.String()
    is_default = fields.Boolean()


class CustomerMarshal(_BaseSchema):
    first_name = fields.String()
    last_name = fields.String()
    is_default = fields.Boolean()
    credit_card_token = fields.String()
