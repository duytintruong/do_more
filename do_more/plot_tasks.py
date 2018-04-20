import argparse
import inspect
import importlib
from doit import loader
import networkx as nx
import graphviz

class PlottingTasks(object):
    '''
        Export the task graph to a dot file.
    '''
    def __init__(self):
        self._read_params()

    def _read_params(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--dodo_fn',
            required=False,
            default='dodo.py',
            type=str,
            help='The dodo file name.')
        parser.add_argument(
            '--dot_fn',
            required=False,
            default=None,
            type=str,
            help='The output dot file name.')
        parser.add_argument(
            '--draw_fn',
            default=None,
            required=False,
            type=str,
            help='The output drawing file name.')
        arguments = vars(parser.parse_args())
        for key in arguments:
            self.__dict__.update({'_' + key: arguments[key]})

    def _wrap_name(self, name):
        # graphviz consider anything after ":" as port
        name = name.replace(':', '#')
        step = 12
        num_steps = (len(name) - 1) // step + 1
        wrapped_names = [
            name[i * step: (i+1) * step] for i in range(num_steps)]
        return '\n'.join(wrapped_names)

    def _get_task_list(self):
        namespace = importlib.import_module(self._dodo_fn[:-3])
        if inspect.ismodule(namespace):
            members = dict(inspect.getmembers(namespace))
        else:
            members = namespace
        task_list = tuple(
            task for task in
            loader.load_tasks(members)
            if not task.has_subtask
        )
        for task in task_list:
            task.name = self._wrap_name(task.name)
            task.file_dep = {self._wrap_name(fn) for fn in task.file_dep}
            task.targets = tuple(self._wrap_name(fn) for fn in task.targets)
        return task_list

    def _build_graph(self, task_list):
        name_to_task = dict([(task.name, task) for task in task_list])
        graph = nx.DiGraph()
        dep_attributes = {
            'task_dep':     {'node_type': 'task'},
            'setup_tasks':  {'node_type': 'task'},
            'calc_dep':     {'node_type': 'task'},
            'file_dep':     {'node_type': 'file'},
            'wild_dep':     {'node_type': 'wildcard'},
            'targets':      {'node_type': 'file'},
        }

        def add_graph_node(node, node_type):
            if node in graph:
                return
            if node_type != 'task':
                graph.add_node(
                    node, type=node_type,
                    style='filled',
                    fillcolor='red',
                    shape='folder',
                    fontname='arial',
                )
            else:
                graph.add_node(
                    node,
                    type=node_type,
                    style='filled',
                    fillcolor='green',
                    shape='doubleoctagon',
                    fontname='arial',
                )
                task = name_to_task[node]
                for dep, dep_kws in dep_attributes.items():
                    for dname in getattr(task, dep):
                        add_graph_node(
                            dname, dep_kws['node_type'])
                        if dep == 'targets':
                            edge = (node, dname)
                        else:
                            edge = (dname, node)
                        graph.add_edge(*edge, type=dep)
        for task_name in name_to_task:
            add_graph_node(task_name, 'task')
        return graph

    def main(self):
        if not any((self._dot_fn, self._draw_fn)):
            print('Either --dot_fn or --draw_fn must be set!')
            return
        task_list = self._get_task_list()
        nx_graph = self._build_graph(task_list)
        gv_graph = nx.nx_agraph.to_agraph(nx_graph)
        if self._dot_fn:
            gv_graph.write(self._dot_fn)
        if self._draw_fn:
            gv_graph.draw(self._draw_fn, prog='dot')


if __name__ == '__main__':
    PlottingTasks().main()
