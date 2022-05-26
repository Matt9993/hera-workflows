"""This example showcases conditional execution on success, failure, and error"""
from hera.task import Task
from hera.workflow import Workflow
from hera.workflow_service import WorkflowService


def random():
    import random

    p = random.random()
    if p <= 0.5:
        raise Exception('FAILURE')
    print('SUCCESS')


def success():
    print("SUCCESS")


def failure():
    print("FAILURE")


# TODO: replace the domain and token with your own
ws = WorkflowService(host='https://my-argo-server.com', token='my-auth-token')
w = Workflow("visualize-conditional", ws)

r = Task('random', random)
s = Task('success', success)
f = Task('failure', failure)

r.on_success(s)
r.on_failure(f)

w.add_tasks(r, s, f)

# Workflow visualize() function is called
g = w.visualize()