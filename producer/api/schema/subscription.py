from marshmallow import Schema, fields

class CreateSubscriptionSchema(Schema):
    user_id    = fields.Int(required=True)

class UpdateSubscriptionStatusSchema(Schema):
    subscription_id = fields.Number(required=True)
    canceled        = fields.Bool(required=False, default=False)
    restarted       = fields.Bool(required=False, default=False)