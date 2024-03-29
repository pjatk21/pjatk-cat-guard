import logging
import re
from datetime import datetime
from enum import Enum
from pathlib import Path

from hikari import Member
from lightbulb import Context
from mongoengine import Document, LongField, EnumField, DateTimeField, DynamicField, EmbeddedDocumentField, \
    EmbeddedDocument, StringField, ReferenceField, NULLIFY, DynamicDocument, ListField, CASCADE


logger = logging.getLogger('mongomodels')


class VerificationMethod(Enum):
    OAUTH = 'oauth'  # user verified by OAuth flow
    REVIEW = 'review'  # user verified by review
    ROLE_ASSIGNED = 'role'  # user verified manually by staff
    ROLE_ENFORCED = 'enforced'  # staff has run command
    MIGRATED = 'migrated'  # user added to the collection due to migration
    CONTEXT_PROVIDED = 'context'  # user added to the collection, while checking his permissions


class VerificationState(Enum):
    PENDING = 'pending'  # waiting for user to fill all required data
    BYPASSED = 'bypassed'  # admin created link
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

    def __str__(self):
        return self.user_name


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


class VerificationGoogle(EmbeddedDocument):
    email = StringField(required=True)
    name = StringField(required=True)
    raw = DynamicField(null=True)


class VerificationRejection(EmbeddedDocument):
    reason = StringField()
    when = DateTimeField(default=lambda: datetime.now().astimezone())

    def __str__(self):
        return self.reason or 'Nie podano przyczyny'


class Reviewer(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)

    def __str__(self):
        return self.identity.user_name


class VerificationChange(EmbeddedDocument):
    state_before = EnumField(VerificationState, required=True)
    state_after = EnumField(VerificationState, required=True)
    when = DateTimeField(default=lambda: datetime.now().astimezone())
    reviewer = ReferenceField(Reviewer, required=True)

    def __str__(self):
        return f'{self.reviewer} zmienił stan {self.state_before.value} na {self.state_after.value} o {self.when}'


class VerificationPhotos(EmbeddedDocument):
    front = StringField(null=True)
    back = StringField(null=True)

    @property
    def ready(self):
        return bool(self.front and self.back)

    @property
    def read(self):
        with open(self.front, 'rb') as ff:
            front = ff.read()

        with open(self.back, 'rb') as bf:
            back = bf.read()

        return front, back

    def __str__(self):
        return f'front: {self.front} | back: {self.back} | ready: {self.ready}'


class VerificationRequest(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    code = StringField(required=True)
    photos = EmbeddedDocumentField(VerificationPhotos, default=VerificationPhotos())
    google = EmbeddedDocumentField(VerificationGoogle, null=True)
    submitted = DateTimeField(default=lambda: datetime.now().astimezone())
    accepted = DateTimeField(null=True)
    state = EnumField(VerificationState, default=VerificationState.PENDING)
    trust = ReferenceField(TrustedUser, null=True, reverse_delete_rule=CASCADE)
    reviewer = ReferenceField(Reviewer, null=True, reverse_delete_rule=NULLIFY)
    rejection = EmbeddedDocumentField(VerificationRejection, null=True)
    changes = ListField(EmbeddedDocumentField(VerificationChange))

    def update_state(self, state: VerificationState, rev: Reviewer):
        change = VerificationChange()
        change.state_before = self.state
        change.state_after = state
        change.reviewer = rev
        self.state = state
        self.changes.append(change)
        self.save()

    @property
    def no(self):
        return re.match(r'(s|pd)\d+', self.google.email).group()

    @property
    def wait_time(self):
        return datetime.now().astimezone() - self.submitted

    def remove_trust(self):
        trust = self.trust
        self.accepted = None
        self.trust = None
        self.save()
        trust.delete()


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


class AltapiConfiguration(Document):
    identity = EmbeddedDocumentField(UserIdentity, required=True)
    groups = ListField(StringField(), default=[])
