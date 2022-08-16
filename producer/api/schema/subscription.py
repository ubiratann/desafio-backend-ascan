from marshmallow import Schema, fields

class CreateSubscriptionSchema(Schema):
    user_id    = fields.Int(required=True)

class UpdateSubscriptionSchema(Schema):
    id = fields.Number(required=True)