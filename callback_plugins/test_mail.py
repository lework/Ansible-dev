from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import smtplib
import json

from ansible.plugins.callback import CallbackBase
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

def _format_addr(s):
name, addr = parseaddr(s)
return formataddr(( \
    Header(name, 'utf-8').encode(), \
    addr.encode('utf-8') if isinstance(addr, unicode) else addr))

def mail(subject='Ansible error mail', sender=None, to=None, body=None):

if sender is None:
    sender='<root>'
if to is None:
    to='to@test.com'
if body is None:
    body = subject

from_addr = 'from@test.com'

msg = MIMEText(body, 'plain', 'utf-8')
msg['From'] = _format_addr(u'%s <%s>' % sender,from_addr)
msg['To'] = _format_addr(u'π‹¿Ì‘± <%s>' % to)
msg['Subject'] = Header(subject, 'utf-8').encode()

smtp = smtplib.SMTP('smtp.test.com', 25) 
smtp.login('user@test.com','test')
smtp.sendmail(from_addr, [to], msg.as_string())
smtp.quit()

class CallbackModule(CallbackBase):
"""
This Ansible callback plugin mails errors to interested parties.
"""
CALLBACK_VERSION = 2.0
CALLBACK_TYPE = 'notification'
CALLBACK_NAME = 'test_mail'
CALLBACK_NEEDS_WHITELIST = False

def v2_runner_on_failed(self, res, ignore_errors=False):

    host = res._host.get_name()

    if ignore_errors:
        return
    sender = '"Ansible: %s"' % host
    attach = res._task.action
    if 'invocation' in res._result:
        attach = "%s:  %s" % (res._result['invocation']['module_name'], json.dumps(res._result['invocation']['module_args']))

    subject = 'Failed: %s' % attach
    body = 'The following task failed for host ' + host + ':\n\n%s\n\n' % attach

    if 'stdout' in res._result.keys() and res._result['stdout']:
        subject = res._result['stdout'].strip('\r\n').split('\n')[-1]
        body += 'with the following output in standard output:\n\n' + res._result['stdout'] + '\n\n'
    if 'stderr' in res._result.keys() and res._result['stderr']:
        subject = res._result['stderr'].strip('\r\n').split('\n')[-1]
        body += 'with the following output in standard error:\n\n' + res._result['stderr'] + '\n\n'
    if 'msg' in res._result.keys() and res._result['msg']:
        subject = res._result['msg'].strip('\r\n').split('\n')[0]
        body += 'with the following message:\n\n' + res._result['msg'] + '\n\n'
    body += 'A complete dump of the error:\n\n' + self._dump_results(res._result)
    mail(sender=sender, subject=subject, body=body)

def v2_runner_on_unreachable(self, result):

    host = result._host.get_name()
    res = result._result

    sender = '"Ansible: %s" <root>' % host
    if isinstance(res, string_types):
        subject = 'Unreachable: %s' % res.strip('\r\n').split('\n')[-1]
        body = 'An error occurred for host ' + host + ' with the following message:\n\n' + res
    else:
        subject = 'Unreachable: %s' % res['msg'].strip('\r\n').split('\n')[0]
        body = 'An error occurred for host ' + host + ' with the following message:\n\n' + \
               res['msg'] + '\n\nA complete dump of the error:\n\n' + str(res)
    mail(sender=sender, subject=subject, body=body)

def v2_runner_on_async_failed(self, result):

    host = result._host.get_name()
    res = result._result

    sender = '"Ansible: %s" <root>' % host
    if isinstance(res, string_types):
        subject = 'Async failure: %s' % res.strip('\r\n').split('\n')[-1]
        body = 'An error occurred for host ' + host + ' with the following message:\n\n' + res
    else:
        subject = 'Async failure: %s' % res['msg'].strip('\r\n').split('\n')[0]
        body = 'An error occurred for host ' + host + ' with the following message:\n\n' + \
               res['msg'] + '\n\nA complete dump of the error:\n\n' + str(res)
    mail(sender=sender, subject=subject, body=body)