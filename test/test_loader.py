import os
import subprocess
from unittest import TestCase

from do_more.doit_loader import DoitLoader


# def task1():
#     print('task1')
#     with open('task1.txt', 'w') as ofile:
#         ofile.write('task1')


# def task2(param1):
#     print('task2, param1', param1)
#     action = 'wc -l task1.txt > task2.txt'
#     os.system(action)


# def task3():
#     print('task3')
#     action = 'bzip2 -k -f task1.txt'
#     os.system(action)


# def task4():
#     print('task4')
#     action = 'rm task1.txt'
#     os.system(action)


# def task_dependence_example():
#     # a task dependence example
#     DoitLoader.add_task_from_cmd(
#         targets=['task2.txt'],
#         file_dep=['task1.txt'],
#         actions=[[task2, {'param1': 123}], 'echo HELLO'],
#         name='task2')

#     DoitLoader.add_task_from_cmd(
#         targets=['task1.txt.bz2'],
#         file_dep=['task1.txt', 'task2.txt'],
#         actions=task3,
#         name='task3')

#     DoitLoader.add_task_from_cmd(
#         targets=[],
#         file_dep=['task1.txt.bz2'],
#         actions=[task4],
#         name='task4',
#         uptodate=[False])

#     DoitLoader.add_task_from_cmd(
#         targets=['task5.txt'],
#         file_dep=[],
#         actions=[
#             ['echo TASK5', {'stdout': 'task5.txt'}],
#             'echo TASK5_2'],
#         name='task5',
#         uptodate=[False])

#     DoitLoader.add_task_from_cmd(
#         targets=['task1.txt'],
#         file_dep=[],
#         actions=[task1],
#         name='task1')


# def pipe_task_example():
#     # a task built by a pipe of actions
#     actions = []
#     actions.append([
#         'cat',
#         {'stdin': 'file1.txt'}
#     ])
#     actions.append(['grep 12', {'stdout': 'file2.txt'}])
#     # actions.append(['ls -l'])
#     # actions.append('echo abc')
#     DoitLoader.add_task_from_cmd(
#         targets=['file2.txt'],
#         file_dep=['file1.txt'],
#         actions=actions,
#         pipe=True)


# def pipe_task_example2():
#     # a task built by a pipe of actions
#     actions = []
#     actions.append('ls')
#     actions.append([
#         'cat',
#         {
#             'stdin': 'file2.txt',
#             'stdout': subprocess.PIPE
#         }
#     ])
#     actions.append(['grep 12', {'stdout': 'file3.txt'}])
#     # actions.append(['ls -l'])
#     actions.append('echo abc')
#     DoitLoader.add_task_from_cmd(
#         targets=['file3.txt'],
#         file_dep=['file2.txt'],
#         actions=actions)


class MyClass():
    def __init__(self):
        pass

    def work(self, file_name_1, file_name_2):
        out_dir = os.path.dirname(file_name_2)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        os.system('cp %s %s' % (file_name_1, file_name_2))
        print('cp %s %s' % (file_name_1, file_name_2))


def my_func(content, file_name):
    out_dir = os.path.dirname(file_name)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(file_name, 'w') as ofile:
        ofile.write('%s\n' % (content))


class TestDoitLoader(TestCase):
    def test_action_as_a_function(self):
        DoitLoader.add_task_from_dict({
            'targets': ['test/tmp/file_1.txt'],
            'file_dep': [],
            'name': 'test_func',
            'actions': [(
                my_func, [],
                {'content': 'line_1', 'file_name': 'test/tmp/file_1.txt'})]
        })
        code = DoitLoader.run()
        self.assertEqual(code, 0)

    def test_action_as_a_class_method(self):
        myclass = MyClass()
        DoitLoader.add_task_from_dict(
            {
                'targets': ['test/tmp/file_2.txt'],
                'file_dep': ['test/__input__/file_1.txt'],
                'name': 'test',
                'actions': [(
                    myclass.work,
                    ['test/__input__/file_1.txt', 'test/tmp/file_2.txt'])]
            })
        code = DoitLoader.run()
        self.assertEqual(code, 0)
