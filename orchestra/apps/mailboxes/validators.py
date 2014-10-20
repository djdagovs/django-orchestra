import hashlib
import os
import re

from django.core.management.base import CommandError
from django.core.validators import ValidationError, EmailValidator
from django.utils.translation import ugettext_lazy as _

from orchestra.utils import paths
from orchestra.utils.system import run

from . import settings


def validate_emailname(value):
    msg = _("'%s' is not a correct email name" % value)
    if '@' in value:
        raise ValidationError(msg)
    value += '@localhost'
    try:
        EmailValidator(value)
    except ValidationError:
        raise ValidationError(msg)


def validate_forward(value):
    """ space separated mailboxes or emails """
    from .models import Mailbox
    for destination in value.split():
        msg = _("'%s' is not an existent mailbox" % destination)
        if '@' in destination:
            if not destination[-1].isalpha():
                raise ValidationError(msg)
            EmailValidator(destination)
        else:
            if not Mailbox.objects.filter(user__username=destination).exists():
                raise ValidationError(msg)
            validate_emailname(destination)


def validate_sieve(value):
    sieve_name = '%s.sieve' % hashlib.md5(value).hexdigest()
    path = os.path.join(settings.MAILBOXES_SIEVETEST_PATH, sieve_name)
    with open(path, 'wb') as f:
        f.write(value)
    context = {
        'orchestra_root': paths.get_orchestra_root()
    }
    sievetest = settings.MAILBOXES_SIEVETEST_BIN_PATH % context
    try:
        test = run(' '.join([sievetest, path, '/dev/null']), display=False)
    except CommandError:
        errors = []
        for line in test.stderr.splitlines():
            error = re.match(r'^.*(line\s+[0-9]+:.*)', line)
            if error:
                errors += error.groups()
        raise ValidationError(' '.join(errors))