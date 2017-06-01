#!/usr/bin/python
# coding: utf-8
# lework

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: le_copy
version_added: "2.3"
short_description: Copy a C(file) to  remote host
description:
     - The C(le_copy) module copies a file to remote host from a given source to a provided destination.
options:
  src:
    description:
      - Path to a file on the source file to remote host
    required: true
  dest:
    description:
      - Path to the destination on the remote host for the copy
    required: true
  force:
    description:
      - the default is C(yes), which will replace the remote file when contents
        are different than the source. If C(no), the file will only be transferred
        if the destination does not exist.
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
  remote_src:
    description:
      - If False, it will search for src at originating/master machine, if True it will go to the remote/target machine for the src. Default is False.
      - Currently remote_src does not support recursive copying.
    choices: [ "True", "False" ]
    required: false
    default: "False"

author:
    - "Lework"
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- name: copy a config C(file)
  le_copy:
    src: /etc/herp/derp.conf
    dest: /root/herp-derp.conf
'''

RETURN = '''
src:
    description: source file used for the copy
    returned: success
    type: string
    sample: "/path/to/file.name"
dest:
    description: destination of the copy
    returned: success
    type: string
    sample: "/path/to/destination.file"
checksum:
    description: sha1 checksum of the file after running copy
    returned: success
    type: string
    sample: "6e642bb8dd5c2e027bf21dd923337cbb4214f827"
gid:
    description: group id of the file, after execution
    returned: success
    type: int
    sample: 100
group:
    description: group of the file, after execution
    returned: success
    type: string
    sample: "httpd"
owner:
    description: owner of the file, after execution
    returned: success
    type: string
    sample: "httpd"
uid:
    description: owner id of the file, after execution
    returned: success
    type: int
    sample: 100
mode:
    description: permissions of the target, after execution
    returned: success
    type: string
    sample: "0644"
size:
    description: size of the target, after execution
    returned: success
    type: int
    sample: 1220
state:
    description: C(state) of the target, after execution
    returned: success
    type: string
    sample: "file"
'''

import os
import shutil


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.pycompat24 import get_exception

def main():
    # 定义modules需要的参数
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(required=True, type='path'),
            dest=dict(required=True, type='path'),
            force=dict(default=True, type='bool'),
            original_basename=dict(required=False),
            remote_src=dict(required=False, type='bool')
        ),
        supports_check_mode=True,
    )

    # 获取modules的参数
    src = module.params['src']
    dest = module.params['dest']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    force = module.params['force']
    remote_src = module.params['remote_src']
    original_basename = module.params.get('original_basename', None)

    # 判断参数是否合规
    if not os.path.exists(b_src):
        module.fail_json(msg="Source %s not found" % (src))
    if not os.access(b_src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))
    if os.path.isdir(b_src):
        module.fail_json(msg="Remote copy does not support recursive copy of directory: %s" % (src))

    # 获取文件的sha1
    checksum_src = module.sha1(src)
    checksum_dest = None

    changed = False

    # 确定dest文件路径
    if original_basename and dest.endswith(os.sep):
        dest = os.path.join(dest, original_basename)
        b_dest = to_bytes(dest, errors='surrogate_or_strict')

    # 判断目标文件是否存在
    if os.path.exists(b_dest):
        if not force:
            module.exit_json(msg="file already exists", src=src, dest=dest, changed=False)
        if os.access(b_dest, os.R_OK):
            checksum_dest = module.sha1(dest)
    # 目录不存在，退出执行
    elif not os.path.exists(os.path.dirname(b_dest)):
        try:
            os.stat(os.path.dirname(b_dest))
        except OSError:
            e = get_exception()
            if "permission denied" in to_native(e).lower():
                module.fail_json(msg="Destination directory %s is not accessible" % (os.path.dirname(dest)))
        module.fail_json(msg="Destination directory %s does not exist" % (os.path.dirname(dest)))

    # 源文件与目标文件sha1值不一致时覆盖源文件
    if checksum_src != checksum_dest:
      if not module.check_mode:
        try:
            if remote_src:
                shutil.copy(b_src, b_dest)
            else:
                module.atomic_move(b_src, b_dest)
        except IOError:
            module.fail_json(msg="failed to copy: %s to %s" % (src, dest))
        changed = True

    else:
        changed = False
	
    # 返回值
    res_args = dict(
        dest=dest, src=src, checksum=checksum_src, changed=changed
    )

    module.exit_json(**res_args)


if __name__ == '__main__':
    main()
