"""Kubernetes events tool for viewing cluster events."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesEventsTool(BaseTool):
    """Tool for listing and filtering Kubernetes events."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            events = v1.list_event_for_all_namespaces(watch=False)
            event_list = []
            for i in events.items:
                event_list.append(
                    {
                        "message": i.message,
                        "reason": i.reason,
                        "type": i.type,
                        "namespace": i.metadata.namespace,
                        "involved_object_name": i.involved_object.name,
                        "involved_object_kind": i.involved_object.kind,
                        "event_time": str(i.event_time) if i.event_time else None,
                    }
                )
            return {"events": event_list}
        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
