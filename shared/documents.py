import base64
import re
from datetime import datetime
from enum import Enum

from hikari import Member
from lightbulb import Context
from mongoengine import Document, LongField, EnumField, DateTimeField, DynamicField, EmbeddedDocumentField, \
    EmbeddedDocument, StringField, ReferenceField, NULLIFY, DynamicDocument, ListField, URLField, LazyReferenceField, \
    BinaryField, CASCADE


class VerificationMethod(Enum):
    OAUTH = 'oauth'  # user verified by OAuth flow
    REVIEW = 'review'  # user verified by review
    ROLE_ASSIGNED = 'role'  # user verified manually by staff
    ROLE_ENFORCED = 'enforced'  # staff has run command
    MIGRATED = 'migrated'  # user added to the collection due to migration
    CONTEXT_PROVIDED = 'context'  # user added to the collection, while checking his permissions


class VerificationState(Enum):
    PENDING = 'pending'  # waiting for user to fill all required data
    IN_REVIEW = 'in review'  # waiting to be reviewed
    ID_REQUIRED = 'id required'  # waiting to be reviewed
    ACCEPTED = 'accepted'  # accepted by reviewer
    REJECTED = 'rejected'  # rejected by reviewer (missing data, typos)
    BANNED = 'banned'  # rejected by reviewer (fraud, fake id, annoying)


class UserIdentity(EmbeddedDocument):
    guild_id = LongField(required=True)
    guild_name = StringField(null=True)
    user_id = LongField(required=True)
    user_name = StringField(null=True)

    @staticmethod
    def from_context(ctx: Context):
        uid = UserIdentity()
        uid.guild_id = ctx.get_guild().id
        uid.user_id = ctx.user.id
        uid.guild_name = ctx.get_guild().name
        uid.user_name = str(ctx.user)
        return uid

    @staticmethod
    def from_member(mem: Member):
        uid = UserIdentity()
        uid.guild_id = mem.guild_id
        uid.user_id = mem.id,
        uid.user_name = str(mem.user)
        return uid


class TrustedUser(Document):
    identity = EmbeddedDocumentField(UserIdentity, unique=True, required=True)
    verification_method = EnumField(VerificationMethod, required=True)
    student_number = StringField(r'(s|pd)\d+')
    when = DateTimeField(default=lambda: datetime.now().astimezone())


class GuildConfiguration(DynamicDocument):
    guild_id = LongField(required=True)
    trusted_role_id = LongField(required=True)
    additional_staff = ListField(LongField())
    additional_staff_roles = ListField(LongField())


class VerificationPhoto(EmbeddedDocument):
    photo = BinaryField(required=True)
    content_type = StringField(required=True)
    content_name = StringField(required=True)
    uploaded = DateTimeField(default=lambda: datetime.now().astimezone())


class VerificationGoogle(EmbeddedDocument):
    email = StringField(required=True)
    name = StringField(required=True)
    raw = DynamicField(null=True)


class VerificationRejection(EmbeddedDocument):
    reason = StringField()
    when = DateTimeField(default=lambda: datetime.now().astimezone())


class Reviewer(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)


class VerificationRequest(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    code = StringField(required=True)
    photo_front = EmbeddedDocumentField(VerificationPhoto, null=True)
    photo_back = EmbeddedDocumentField(VerificationPhoto, null=True)
    google = EmbeddedDocumentField(VerificationGoogle, null=True)
    submitted = DateTimeField(default=lambda: datetime.now().astimezone())
    state = EnumField(VerificationState, default=VerificationState.PENDING)
    trust = ReferenceField(TrustedUser, null=True, reverse_delete_rule=CASCADE)
    reviewer = ReferenceField(Reviewer, null=True, reverse_delete_rule=NULLIFY)
    rejection = EmbeddedDocumentField(VerificationRejection, null=True)

    @property
    def photos_as_base64(self):
        return base64.b64encode(self.photo_front.photo).decode(), base64.b64encode(self.photo_back.photo).decode()

    @property
    def no(self):
        return re.match(r'(s|pd)\d+', self.google.email).group()

    def wait_time(self):
        td = datetime.now().astimezone() - self.submitted
        if td.seconds < 60:
            return 'Mniej niż minuta'
        if td.days > 1:
            return 'Ponad dzień'
        return f'{td.seconds // 3600}h {td.seconds % 60}m'


class CaptchaInvites(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    invite_alias = StringField(required=True, unique=True)


class ExecutedCommand(EmbeddedDocument):
    name = StringField()
    options = DynamicField()


class AuditLog(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    exec_cmd = EmbeddedDocumentField(ExecutedCommand, required=True)
    interaction = LongField(required=True)
    requested = DateTimeField(default=lambda: datetime.now().astimezone())
    completed = DateTimeField(null=True)


class CronHealthCheck(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    widget_channel_id = LongField(required=True)
    widget_message_id = LongField(required=True)
