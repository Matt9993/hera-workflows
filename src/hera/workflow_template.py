"""The implementation of a Hera cron workflow for Argo-based cron workflows"""
from typing import Any, Optional, Tuple

import graphviz
from argo_workflows.models import IoArgoprojWorkflowV1alpha1WorkflowTemplate

from hera.global_config import GlobalConfig
from hera.workflow import Workflow


class WorkflowTemplate(Workflow):
    """A workflow template representation.

    See `hera.workflow.Workflow` for parameterization.

    Notes
    -----
    See: https://argoproj.github.io/argo-workflows/workflow-templates/
    """

    def build(self) -> IoArgoprojWorkflowV1alpha1WorkflowTemplate:
        """Builds the workflow"""
        spec = super()._build_spec()
        return IoArgoprojWorkflowV1alpha1WorkflowTemplate(
            api_version=GlobalConfig.api_version,
            kind=self.__class__.__name__,
            metadata=self._build_metadata(),
            spec=spec,
        )

    def create(self) -> "WorkflowTemplate":
        """Creates a workflow template"""
        if self.in_context:
            raise ValueError("Cannot invoke `create` when using a Hera context")
        self.service.create_workflow_template(self.build())
        return self

    def lint(self) -> "WorkflowTemplate":
        """Lint the workflow"""
        self.service.lint_workflow_template(self.build())
        return self

    def update(self) -> "WorkflowTemplate":
        """Updates an existing workflow template"""
        self.service.update_workflow_template(self.name, self.build())
        return self

    def delete(self) -> Tuple[object, int, dict]:
        """Deletes the workflow"""
        return self.service.delete_workflow_template(self.name)

    # extra function
    def visualize(self, format: str = "pdf", view: bool = False, is_test: bool = False) -> Optional[Any]:
        """
        Creates graphviz object for representing the current Workflow. This graphviz
        will be rendered in a new window. If a `filename` is provided, the object
        will not be rendered and instead saved to the location specified.
        For this feature Graphviz needs to be installed on your system.
        See the package here: https://pypi.org/project/graphviz/ .
        Args:
            - format (str, optional): A format specifying the output file type; defaults to 'pdf'.
              Refer to http://www.graphviz.org/doc/info/output.html for valid formats
            - view (bool): Attribute to trigger new window to pop up. Defaults to False.
            - is_test (bool): Used for testing without actually rendering a pdf.

        Raises:
            - ImportError: if `graphviz` is not installed

        Returns:
            - Optional[Any]: If called in test mode return the graph object
        """
        tasks = [e.__dict__ for e in self.dag.tasks]
        # flatten if nested
        for i, e in enumerate(tasks):
            if e.get("dag", None):
                last_not_exit_task = tasks[i - 1].get("name")
                for item in self.to_dict()["spec"]["templates"]:
                    if item.get("name") != self.name and item.get("dag", None):
                        tasks.extend(item["dag"]["tasks"])

        tasks = [d for d in tasks if d.get("dag", None) is None]
        # set name
        dot = graphviz.Digraph(comment=self.name)

        for el in tasks:
            dot.node(el.get("name"), el.get("name"))

        for i, e in enumerate(tasks):
            # set default style for indicating connection type
            style = "filled"
            color = "black"
            deps = None

            # get the head element
            head = e.get("name")

            if e.get("depends", None):
                # set different style for if condition
                if e.get("when", None):
                    style = "dotted"

                if "Succeeded" in e.get("depends"):
                    deps = [e.get("depends").split(".")[0]]
                    color = "green2"
                elif "Failed" in e.get("depends") or "Errored" in e.get("depends"):
                    deps = [e.get("depends").split(".")[0]]
                    color = "red2"
                elif "&&" in e.get("depends"):
                    deps = e.get("depends").split(" && ")

                else:
                    deps = [e.get("depends")]

            elif e.get("when"):
                if "Succeeded" in e.get("when"):
                    color = "green2"
                else:
                    color = "red2"
                deps = [last_not_exit_task]

            if deps:
                for dep in deps:
                    # set current dep as tail
                    tail = dep

                if head != tail:
                    dot.edge(tail_name=tail, head_name=head, style=style, color=color)

        if is_test:
            return dot
        else:
            dot.render(f"workflows-graph-output/{self.name}", view=view, format=format, cleanup=True)
            return dot
