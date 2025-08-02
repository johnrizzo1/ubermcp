from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesPersistentVolumesTool(BaseTool):
    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            pvs = v1.list_persistent_volume(watch=False)
            pv_list = []
            for i in pvs.items:
                pv_list.append(
                    {
                        "name": i.metadata.name,
                        "capacity": i.spec.capacity,
                        "access_modes": i.spec.access_modes,
                        "status": i.status.phase,
                        "claim_ref": (
                            i.spec.claim_ref.name if i.spec.claim_ref else None
                        ),
                    }
                )
            return {"persistent_volumes": pv_list}
        except Exception as e:
            return {"error": str(e)}
