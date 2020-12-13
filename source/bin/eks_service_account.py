from aws_cdk import (
    core,
    aws_iam as iam
    # aws_efs as efs
)
from aws_cdk.aws_secretsmanager import ISecret
from aws_cdk.aws_eks import ICluster
from bin.manifest_reader import *

class EksSAConst(core.Construct):

    def __init__(self,scope: core.Construct, id:str, eks_cluster: ICluster, secret: ISecret, **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)

# //************************************v*************************************************************//
# //***************************** SERVICE ACCOUNT, RBAC and IAM ROLES *******************************//
# //****** Associating IAM role to K8s Service Account to provide fine-grain security control ******//
# //***********************************************************************************************//
        # Cluster Auto-scaler
        self._scaler_sa = eks_cluster.add_service_account('AutoScalerSa', 
            name='cluster-autoscaler', 
            namespace='kube-system'
        )  
        _scaler_role = loadYamlLocal('../app_resources/autoscaler-iam-role.yaml')
        for statmt in _scaler_role:
            self._scaler_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmt))

        # ALB Ingress
        self._alb_sa = eks_cluster.add_service_account('ALBServiceAcct', 
            name='alb-aws-load-balancer-controller',
            namespace='kube-system'
        )
        _alb_role = loadYamlLocal('../app_resources/alb-iam-role.yaml')
        for statmt in _alb_role:
            self._alb_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmt))

        # External secret controller
        self._secrets_sa = eks_cluster.add_service_account('ExSecretController',
            name='external-secrets-controller',
            namespace="kube-system"
        )
        self._secrets_sa.node.add_dependency(secret)
        _secrets_role = loadYamlReplaceVarLocal('../app_resources/ex-secret-iam-role.yaml',
                        fields={"{{secretsmanager}}": secret.secret_arn+"*"}
                    )
        for statmt in _secrets_role:
            self._secrets_sa.add_to_principal_policy(iam.PolicyStatement.from_json(statmt))  