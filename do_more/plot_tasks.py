import argparse
import inspect
import importlib
from doit import loader
import networkx as nx
from networkx.drawing.nx_pydot import write_dot


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
            required=True,
            type=str,
            help='The output dot file name.')
        arguments = vars(parser.parse_args())
        for key in arguments:
            self.__dict__.update({'_' + key: arguments[key]})

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
        # graphviz consider anything after ":" as port
        for task in task_list:
            task.name = task.name.replace(':', '#')
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
                    node, type=node_type, style='filled', fillcolor='red')
            else:
                graph.add_node(
                    node, type=node_type, style='filled', fillcolor='green')
                task = name_to_task[node]
                for dep, dep_kws in dep_attributes.items():
                    for dname in getattr(task, dep):
                        add_graph_node(
                            dname, dep_kws['node_type'])
                        if dep == 'targets':
                            edge = (dname, node)
                        else:
                            edge = (node, dname)
                        graph.add_edge(*edge, type=dep)
        for task_name in name_to_task:
            add_graph_node(task_name, 'task')
        return graph

    def main(self):
        task_list = self._get_task_list()
        graph = self._build_graph(task_list)
        write_dot(graph, self._dot_fn)


if __name__ == '__main__':
    PlottingTasks().main()
