from aws_cdk import (
    core,
    aws_iam    
)
from jsii._reference_map import _refs
from jsii._utils import Singleton
import jsii

@jsii.implements(core.IAspect)
class PermissionBoundaryAspect:

    def __init__(self, permission_boundary: jsii.Union[aws_iam.ManagedPolicy, str]) -> None:
        """
        :param permission_boundary: Either aws_iam.ManagedPolicy object or managed policy's ARN as string
        """
        self.permission_boundary = permission_boundary

    def visit(self, construct_ref: core.IConstruct) -> None:
        """
        construct_ref only contains a string reference to an object. To get the actual object, we need to resolve it using JSII mapping.
        :param construct_ref: ObjRef object with string reference to the actual object.
        :return: None
        """
        kernel = Singleton._instances[jsii._kernel.Kernel]
        resolve = _refs.resolve(kernel, construct_ref)

        def _walk(obj):
            if isinstance(obj, aws_iam.Role):
                cfn_role = obj.node.find_child('Resource')
                policy_arn = self.permission_boundary if isinstance(self.permission_boundary, str) else self.permission_boundary.managed_policy_arn
                cfn_role.add_property_override('PermissionsBoundary', policy_arn)
            else:
                if hasattr(obj, 'permissions_node'):
                    for c in obj.permissions_node.children:
                        _walk(c)
                if obj.node.children:
                    for c in obj.node.children:
                        _walk(c)

        _walk(resolve)