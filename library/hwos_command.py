#!/usr/bin/python

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = ''' 
---
module: hwos_command
version_added: "2.3"
short_description: Run arbitrary command on HUAWEI network devices.
description:
     - Run arbitrary command on HUAWEI network devices.
options:
  command:
    description:
      - HUAWEI network devices command
    required: true
  shost:
    description:
      - remote network devices ip address
    required: true
  sport:
    description:
      - remote network devices ssh port
    required: false
    default: 22
  suser:
    description:
      - remote network devices ssh user
    required: true
  spass:
    description:
      - remote network devices ssh user password
    required: true
  save:
    description:
      - save current configuration
    required: false
    default: no
author:
    - "Lework"
'''

EXAMPLES = """
- hosts: localhost
  gather_facts: no
  connection: local
  vars:
    sport: 22
    suser: "user1"
    spass: "test"
    shost: "192.168.77.140"

  tasks:
    - name: display version
      hwos_command:
        sport: "{{ sport }}"
        shost: "{{ shost }}"
        suser: "{{ suser }}"
        spass: "{{ spass }}"
        command: display version

    - name: add vlan 800 and int 0/0/11
      hwos_command:
        sport: "{{ sport }}"
        shost: "{{ shost }}"
        suser: "{{ suser }}"
        spass: "{{ spass }}"
        save: true
        command: |
          system-view
          vlan 800
          quit
          interface GigabitEthernet 0/0/12
          port link-type access
          vlan 800
          port GigabitEthernet 0/0/12
"""


RETUN = """
stdout:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]

command:
  description: rum command
  returned: always
  type: str
  sample: display version
"""


import time
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
from ansible.errors import AnsibleError, AnsibleConnectionFailure

try:
  import paramiko
except ImportError:
  raise AnsibleError("paramiko is not installed, please use pip install paramiko")
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


terminal_stdout_re = [
        re.compile(r'[\r\n]?<.+>(?:\s*)$'),
        re.compile(r'[\r\n]?\[.+\](?:\s*)$'),
    ]

terminal_stderr_re = [
        re.compile(r"% ?Error: "),
        re.compile(r"^% \w+", re.M),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
        re.compile(r"syntax error"),
        re.compile(r"unknown command"),
        re.compile(r"Error\[\d+\]: ", re.I),
        re.compile(r"Error:", re.I)
    ]


class Hwcon(object):
    shell = None
    client = None

    def __init__(self, address, username, password, port=22):
        display.vv("Connecting to network device on ip", str(address) + ".")
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.client.connect(address, port=port, username=username, password=password, look_for_keys=False,
                            allow_agent=False)

    def close(self):
        if self.client is not None:
            self.client.close()

    def openShell(self):
        self.shell = self.client.invoke_shell()

    def send_command(self, command=''):
        if self.shell:
            if command not in ('?',):
                command += "\n"
            self.shell.send(command)

        while True:
            if self.shell.recv_ready() or self.shell.recv_stderr_ready():
                break
            time.sleep(0.1)

    def get_command_result(self, cmd):
        buffersize = 4096
        self.send_command()
        self.shell.recv(buffersize)
        self.send_command(cmd)
        stdout = self.shell.recv(buffersize)
        b_data = stdout.split('\r\n')
        result_tmp = ''
        while '- More -' in b_data[-1]:
            self.shell.send("\n")
            time.sleep(0.1)
            tmp = self.shell.recv(buffersize)
            b_data = tmp.split('\r\n')
            result_tmp += tmp

        if self.shell.recv_stderr_ready():
            stderr = self.shell.recv_stderr(buffersize)
        else:
            stderr = ''
        stdout = '\r\n'.join(stdout.split('\r\n')[:-1]) + '\n' + result_tmp
        stdout = stdout.replace('  ---- More ----', '').replace(
            '\x1b[42D                                          \x1b[42D', '')
        return stdout, stderr

    def parse_result_data(self, data):
        b_data = data.split('\r\n')
        result = b_data[1:-1]
        return '\r\n'.join(result)

    def save_config(self):
        rc = 1
        buffersize = 4096
        self.send_command()
        stdout = self.shell.recv(buffersize)
        t1 = terminal_stdout_re[0].findall(stdout)
        while not t1:
           self.send_command('quit')
           stdout = self.shell.recv(buffersize)
           t1 = terminal_stdout_re[0].findall(stdout)
        self.send_command('save')
        time.sleep(0.1)
        self.send_command('y')
        time.sleep(3)
        stdout = self.shell.recv(buffersize)
        if stdout.find('successfully'):
            rc = 0
        return rc

    def run(self, cmd):
        rc = 1
        stdout, stderr = self.get_command_result(cmd)
        for regex in terminal_stderr_re:
            r1 = regex.findall(stdout)
        if not r1:
           stdout = self.parse_result_data(stdout)
           rc = 0
        return rc, stdout, stderr


def main():
    module = AnsibleModule(
	    argument_spec = dict(
	    command=dict(required=True, type='str'),
	    shost=dict(required=True, type='str'),
	    sport=dict(required=False, type='int', default=22),
	    suser=dict(required=True, type='str'),
	    spass=dict(required=True, type='str', no_log=True),
	    save=dict(required=False, type='bool')
	  )
    )

    b_command = to_bytes(module.params['command'], errors='surrogate_or_strict')
    b_host = to_bytes(module.params['shost'], errors='surrogate_or_strict')
    b_user = to_bytes(module.params['suser'], errors='surrogate_or_strict')
    b_password = to_bytes(module.params['spass'], errors='surrogate_or_strict')
    result = {'changed': False}

    try:
      connection = Hwcon(b_host, b_user, b_password, module.params['sport'])
    except Exception as e:
      raise AnsibleConnectionFailure(str(e))
    try:
      connection.openShell()
    except Exception as e:
      msg = "Failed to open session"
      if len(str(e)) > 0:
        msg += ": %s" % str(e)
      raise AnsibleConnectionFailure(msg)
    display.vvv("EXEC %s" % b_command, host=b_host)
    try:
      rc,stdout,stderr = connection.run(b_command)
    except Exception as e:
       raise AnsibleError('Exec command error.\n' + str(e) )

    if rc == 0 and b_command.find('display'):
        result['changed'] = True
    elif rc == 1:
	module.fail_json(msg=stdout+stderr)

    if module.params['save']:
        try:
            save_rc = connection.save_config()
        except Exception as e:
          raise AnsibleError('Save config error.\n' + str(e) )
        if save_rc != 0:
            msg= "not save config!"
            module.fail_json(msg=msg)

    connection.close()

    result.update({
	'command': b_command,
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr})

    module.exit_json(**result)

if __name__ == '__main__':
    main()
