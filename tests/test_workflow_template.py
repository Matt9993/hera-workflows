from unittest import mock
from unittest.mock import Mock, patch

import pytest
from argo_workflows.models import IoArgoprojWorkflowV1alpha1WorkflowTemplate

from hera import Task, WorkflowTemplate


class TestWorkflowTemplate:
    def test_build_returns_expected_spec(self, setup):
        with WorkflowTemplate("test") as wt:
            template = wt.build()
            assert isinstance(template, IoArgoprojWorkflowV1alpha1WorkflowTemplate)
            assert hasattr(template, "api_version")
            assert template.api_version == "argoproj.io/v1alpha1"
            assert isinstance(template.api_version, str)
            assert hasattr(template, "kind")
            assert isinstance(template.kind, str)
            assert template.kind == "WorkflowTemplate"

    def test_create_calls_service_create(self, setup):
        with WorkflowTemplate("test") as wt:
            with pytest.raises(ValueError) as e:
                wt.create()
            assert str(e.value) == "Cannot invoke `create` when using a Hera context"

        with WorkflowTemplate("test") as wt:
            wt.dag = None
            with pytest.raises(ValueError) as e:
                wt.create()

        with WorkflowTemplate("test") as wt:
            wt.service = mock.Mock()
        wt.create()
        wt.service.create_workflow_template.assert_called_once()

    def test_update_calls_service_update(self, setup):
        with WorkflowTemplate("test") as wt:
            wt.service = mock.Mock()
        wt.update()
        wt.service.update_workflow_template.assert_called_once()

    def test_update_cals_service_delete(self, setup):
        s = mock.Mock()
        with WorkflowTemplate("test", service=s) as wt:
            wt.delete()
        wt.service.delete_workflow_template.assert_called_once()

    def test_lint(self):
        service = mock.Mock()
        service.lint_workflow_template = mock.Mock()
        with WorkflowTemplate("w", service=service) as w:
            w.lint()
        w.service.lint_workflow_template.assert_called_once_with(w.build())

    def test_workflow_template_visualize_generated_graph_structure(self, wt, no_op):
        with WorkflowTemplate("test") as wt:
            t1 = Task("t1", no_op)
            t2 = Task("t2", no_op)
            t1 >> t2

            h2 = Task("head2", no_op)
            h2 >> t1

        # call visualize()
        graph_obj = wt.visualize(is_test=True)
        assert graph_obj.comment == "test"

        # generate list of numbers with len of dot body elements
        # len(2) is a node (Task) and len(4) is an edge (dependency)
        element_len_list = [len(item.split(' ')) for item in graph_obj.body]
        print(element_len_list)
        # check number of nodes (Tasks)
        assert 3 == int(element_len_list.count(2))
        # check number of edge (dependency)
        assert 2 == int(element_len_list.count(5))

        h1 = Task("head1", no_op)
        h1 >> h2

        # call visualize again after new node (Task)
        # that is also a new head (new dependency)
        updated_graph_obj = wt.visualize(is_test=True)
        element_len_list_new = [len(item.split(' ')) for item in updated_graph_obj.body]

        # check number of nodes (Tasks)
        assert 3 == int(element_len_list_new.count(2))
        # check number of edge (dependency)
        assert 3 == int(element_len_list_new.count(5))

    def test_workflow_template_visualize_connection_style(self, wt, no_op):
        """
        Test for checking if the style (filled, dotted...)
        applied according to dependency.
        """
        r = Task("random", no_op)
        s = Task("success", no_op)
        f = Task("failure", no_op)

        # define dependency
        r.on_success(s)
        r.on_failure(f)

        # add tasks
        wt.add_tasks(r, s, f)

        # call visualize()
        graph_obj = wt.visualize(is_test=True)
        element_len_list = [item.split(' ') for item in graph_obj.body]

        # check the style for dependency
        assert element_len_list[-2][-2][7:13] == "green2"
        assert element_len_list[-1][-2][7:13] == "red2"
