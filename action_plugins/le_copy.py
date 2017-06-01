#!/usr/bin/python
# coding: utf-8
# lework

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import stat
import tempfile

from ansible.constants import mk_boolean as boolean
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.action import ActionBase
from ansible.utils.hashing import checksum


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        ''' handler for file transfer operations '''
#	import pydevd; pydevd.settrace('192.168.77.1', port=9999, stdoutToServer=True, stderrToServer=True)
        if task_vars is None:
            task_vars = dict()
        # 执行父类的run方法
        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped'):
            return result

        # 获取参数
        source  = self._task.args.get('src', None)
        dest    = self._task.args.get('dest', None)
        force   = boolean(self._task.args.get('force', 'yes'))
        remote_src = boolean(self._task.args.get('remote_src', False))

        # 判定参数
        result['failed'] = True
        if source is None or dest is None:
            result['msg'] = "src and dest are required"
        elif source is not None and source.endswith("/"):
            result['msg'] = "src must be a file"
        else:
            del result['failed']

        if result.get('failed'):
            return result

        # 如果copy动作在远端执行，直接返回
        if remote_src:
            result.update(self._execute_module(task_vars=task_vars))
            return result

        # 找到source的路径地址
        try:
            source = self._find_needle('files', source)
        except AnsibleError as e:
            result['failed'] = True
            result['msg'] = to_text(e)
            return result

        # 判断是否是目录，如果是跳出返回
        if os.path.isdir(to_bytes(source, errors='surrogate_or_strict')):
            result['failed'] = True
            result['msg'] = 'src must be a file'
            return result

        changed = False
        module_return = dict(changed=False)

        # 创建临时目录
        if tmp is None or "-tmp-" not in tmp:
            tmp = self._make_tmp_path()

        # 5. 获取本地文件，不存在抛出异常
        try:
            source_full = self._loader.get_real_file(source)
            source_rel = os.path.basename(source)
        except AnsibleFileNotFound as e:
            result['failed'] = True
            result['msg'] = "could not find src=%s, %s" % (source_full, e)
            self._remove_tmp_path(tmp)
            return result


        # 获取远程文件信息
        if self._connection._shell.path_has_trailing_slash(dest):
            dest_file = self._connection._shell.join_path(dest, source_rel)
        else:
            dest_file = self._connection._shell.join_path(dest)

        dest_status = self._execute_remote_stat(dest_file, all_vars=task_vars, follow=False, tmp=tmp, checksum=force)

        # 如果是目录，则返回
        if dest_status['exists'] and dest_status['isdir']:
           self._remove_tmp_path(tmp)
           result['failed'] = True
           result['msg'] = "can not use content with a dir as dest"
           return result

        # 如果存在，但force为false。则返回
        if dest_status['exists'] and not force:
          return result

        # 定义拷贝到远程的文件路径
        tmp_src = self._connection._shell.join_path(tmp, 'source')

        # 传送文件

        remote_path = None
        remote_path = self._transfer_file(source_full, tmp_src)

        # 确保我们的文件具有执行权限
        if remote_path:
            self._fixup_perms2((tmp, remote_path))

        # 运行remote_copy 模块
        new_module_args = self._task.args.copy()
        new_module_args.update(
            dict(
                src=tmp_src,
                dest=dest,
                original_basename=source_rel,
            )
        )

        module_return = self._execute_module(module_name='le_copy',
            module_args=new_module_args, task_vars=task_vars,
            tmp=tmp)

        # 判断运行结果
        if module_return.get('failed'):
            result.update(module_return)
            return result
        if module_return.get('changed'):
            changed = True

        if module_return:
           result.update(module_return)
        else:
           result.update(dict(dest=dest, src=source, changed=changed))

        # 清理临时文件
        self._remove_tmp_path(tmp)
        
        # 返回结果
        return result
