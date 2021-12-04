from datetime import datetime
from enum import Enum

from mongoengine import Document, LongField, EnumField, DateTimeField, DynamicField, EmbeddedDocumentField, \
    EmbeddedDocument, StringField, ReferenceField, NULLIFY, DynamicDocument


class VerificationMethod(Enum):
    OAUTH = 'oauth'  # user verified by OAuth flow
    ROLE_ASSIGNED = 'role'  # user verified manually by staff
    ROLE_ENFORCED = 'enforced'  # staff has run command
    MIGRATED = 'migrated'  # user added to the collection due to migration
    CONTEXT_PROVIDED = 'context'  # user added to the collection, while checking his permissions


class UserIdentity(EmbeddedDocument):
    guild_id = LongField(required=True)
    guild_name = StringField(null=True)
    user_id = LongField(required=True)
    user_name = StringField(null=True)


class TrustedUser(Document):
    identity = EmbeddedDocumentField(UserIdentity, unique=True, required=True)
    verification_method = EnumField(VerificationMethod, required=True)
    verification_context = DynamicField()
    student_number = StringField(r's\d{5}', required=True)
    when = DateTimeField(default=datetime.now)


class GuildConfiguration(DynamicDocument):
    managed_by = EmbeddedDocumentField(UserIdentity, required=True)
    trusted_role_id = LongField(required=True)


class VerificationLink(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    secret_code = StringField(required=True)
    trust = ReferenceField(TrustedUser, reverse_delete_rule=NULLIFY, null=True)


class CaptchaInvites(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    invite_alias = StringField(required=True, unique=True)
