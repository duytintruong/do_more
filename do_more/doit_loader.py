#!/usr/bin/env python

import sys
import subprocess
import copy
import logging
from collections import namedtuple

from doit.task import dict_to_task
from doit.cmd_base import TaskLoader
from doit.doit_cmd import DoitMain
from doit.task import clean_targets

logging.basicConfig(
    level=logging.DEBUG, stream=sys.stderr,
    format=(
        '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(lineno)d | '
        '%(message)s')
)
logger = logging.getLogger(sys.argv[0])


class DoitLoader(TaskLoader):
    task_list = []
    config = {'verbosity': 2}
    task_id_counter = 0

    @staticmethod
    def load_tasks(action, opt_values, pos_args):
        return DoitLoader.task_list, DoitLoader.config

    @staticmethod
    def add_task_from_cmd(
            targets,
            file_dep,
            actions,
            name=None,
            pipe=False,
            **kwargs):
        if type(targets) not in (list, tuple):
            targets = [targets]
        if type(actions) not in (list, tuple):
            actions = [actions]
        if type(file_dep) not in (list, tuple):
            file_dep = [file_dep]
        if name is None:
            DoitLoader.task_id_counter += 1
            name = 'task_%d' % (DoitLoader.task_id_counter)
        actions = DoitLoader.format_actions(actions)
        if pipe:
            for i in range(len(actions)-1):
                actions[i][1]['stdout'] = subprocess.PIPE
        params = [{'name': 'actions', 'default': copy.deepcopy(actions)},
                  {'name': 'pipe', 'default': pipe}]

        def run_cmds(actions):
            for i in range(len(actions)):
                for k in ['stdin', 'stdout', 'stderr']:
                    if (k in actions[i][1] and
                            isinstance(actions[i][1][k], str)):
                        mode = 'r' if k == 'stdin' else 'w'
                        actions[i][1][k] = open(actions[i][1][k], mode)

            finished = True
            for i in range(len(actions)):
                if actions[i][0].__class__.__name__ in (
                        'function', 'instancemethod'):
                    returncode = actions[i][0](**actions[i][1])
                    finished = finished and returncode
                else:
                    p = subprocess.Popen(
                        actions[i][0],
                        **actions[i][1]
                    )
                    connect = False
                    if 'stdout' in actions[i][1]:
                        if (actions[i][1]['stdout'] == subprocess.PIPE and
                                i < len(actions) - 1):
                            connect = True
                    if connect:
                        actions[i+1][1]['stdin'] = p.stdout
                    else:
                        p.communicate()
                        finished = finished and p.returncode is not None

            for i in range(len(actions)):
                for k in ['stdin', 'stdout', 'stderr']:
                    if k in actions[i][1] and isinstance(
                            actions[i][1][k], file):
                        actions[i][1][k].close()
            return finished

        task = {
            'name': name,
            'actions': [(run_cmds, [actions])],
            'targets': targets,
            'file_dep': file_dep,
            'params': params,
            'clean': [clean_targets],
            'title': DoitLoader.print_action
        }
        for k, v in kwargs.items():
            task[k] = v
        DoitLoader.task_list.append(dict_to_task(task))

    @staticmethod
    def add_task_from_dict(task):
        DoitLoader.task_list.append(dict_to_task(task))

    @staticmethod
    def format_actions(actions):
        if (len(actions) == 2 and
                actions[0].__class__.__name__ in (
                    'list', 'tuple', 'str', 'function', 'instancemethod') and
                actions[1].__class__.__name__ == 'dict'):
            actions = [actions]
        actions = [
            action for action in actions if (
                action.__class__.__name__ in [
                    'function', 'instancemethod']) or len(action)]
        for i in range(len(actions)):
            if isinstance(actions[i], str):
                actions[i] = [actions[i].split(), {}]
            elif actions[i].__class__.__name__ in (
                    'function', 'instancemethod'):
                actions[i] = [actions[i], {}]
            elif isinstance(actions[i], (list, tuple)):
                if len(actions[i]) == 1 or not isinstance(actions[i][1], dict):
                    if isinstance(actions[i][0], str):
                        actions[i] = [actions[i][0].split(), {}]
                    else:
                        actions[i] = [actions[i], {}]
                elif isinstance(actions[i][0], str):
                    actions[i][0] = actions[i][0].split()
        return actions

    @staticmethod
    def params2struct(params):
        result = {}
        for param in params:
            result[param['name']] = param['default']
        result = namedtuple('NamedTuple', result.keys())(**result)
        return result

    @staticmethod
    def print_action(task):
        action = 'Task %s: ' % task.name
        if task.actions[0].__class__.__name__ == 'PythonAction':
            params = DoitLoader.params2struct(task.params)
            actions = params.actions
            for i in range(len(actions)):
                connect = False
                if actions[i][0].__class__.__name__ in (
                        'function', 'instancemethod'):
                    action += str(actions[i][0])
                else:
                    if 'stdin' in actions[i][1]:
                        action += '%s > ' % actions[i][1]['stdin']
                    action += ' '.join(actions[i][0])
                    if 'stdout' in actions[i][1]:
                        if actions[i][1]['stdout'] == subprocess.PIPE:
                            connect = True
                        else:
                            action += ' > %s' % actions[i][1]['stdout']
                if len(actions[i][1]):
                    action += ', ' + str(actions[i][1])

                if connect:
                    action += ' | '
                else:
                    action += ' ; '
            action = action[:-3]
        else:
            action += str(task.actions)
        return action

    @staticmethod
    def run(clean=False, number_of_processes=None, db_file_name=None):
        doit_args = []
        if clean:
            doit_args.append('clean')
        if number_of_processes:
            doit_args += ['-n', str(number_of_processes)]
        if db_file_name:
            doit_args += ['--db-file', db_file_name]

        code = DoitMain(DoitLoader()).run(doit_args)
        if code == 0:
            logger.debug('Doit: all tasks were executed.')
        elif code == 1:
            logger.debug('Doit: some tasks were failed.')
        elif code == 2:
            logger.debug('Doit: error when executing tasks.')
        elif code == 3:
            logger.debub('Doit: error before task execution starts.')
        return code
