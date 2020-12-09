# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from aws_cdk import (
    core, 
    aws_eks as eks,
    aws_secretsmanager as secmger,
    aws_cdk.aws_elasticloadbalancingv2 as alb
)
from bin.network_sg import NetworkSgConst
from bin.iam_roles import IamConst
from bin.cloudfront import CloudFrontConst
from bin.eks_cluster import EksConst
from bin.eks_service_account import EksSAConst
from bin.eks_base_app import EksBaseAppConst
from bin.s3_app_code import S3AppCodeConst
from bin.spark_permission import SparkOnEksSAConst
from bin.manifest_reader import *
import json

class SparkOnEksStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, eksname: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Cloudformation input params
        datalake_bucket = core.CfnParameter(self, "datalakebucket", type="String",
            description="An existing S3 bucket to be accessed by Jupyter Notebook and ETL job",
            default=""
        )
        login_name = core.CfnParameter(self, "jhubuser", type="String",
            description="Your username login to jupyter hub",
            default="sparkoneks"
        )

        # Auto-generate a user login in secrets manager
        jhub_secret = secmger.Secret(self, 'jHubPwd', 
            generate_secret_string=secmger.SecretStringGenerator(
                exclude_punctuation=True,
                secret_string_template=json.dumps({'username': login_name.value_as_string}),
                generate_string_key="password")
        )

        # Setup EKS base infrastructure
        network_sg = NetworkSgConst(self,'network-sg', eksname)
        iam_role = IamConst(self,'iam_roles', eksname)
        eks_cluster = EksConst(self,'eks_cluster', eksname, network_sg.vpc, iam_role.managed_node_role)
        eks_security = EksSAConst(self, 'eks_sa', eks_cluster.my_cluster, jhub_secret)
        eks_base_app = EksBaseAppConst(self, 'eks_base_app', eks_cluster.my_cluster, self.region)
        # eks_base_app.node.add_dependency(eks_security)

        # Setup Spark On EKS
        app_s3 = S3AppCodeConst(self,'upload_app_code')
        app_security = SparkOnEksSAConst(self,'spark_service_account', 
            eks_cluster.my_cluster, 
            login_name.value_as_string,
            app_s3.code_bucket,
            datalake_bucket.value_as_string
        )
        
# //**************************************************************************************//
# //************************** 1. Setup Argo Workflow ***********************************//
# //******* K8s Native WF tool orchestrates containerized batch & streaming jobs ********//
# //***********************************************************************************//
        argo_install = eks_cluster.my_cluster.add_helm_chart('ARGOChart',
            chart='argo',
            repository='https://argoproj.github.io/argo-helm',
            release='argo',
            namespace='argo',
            create_namespace=True,
            values=loadYamlLocal('../app_resources/argo-values.yaml')
        )
        
        # Create a k8s cluster scope workflow template, required when manually submit Spark jobs
        submit_tmpl = eks_cluster.my_cluster.add_manifest('SubmitSparkWrktmpl',
            loadYamlLocal('../app_resources/spark-template.yaml')
        )
        submit_tmpl.node.add_dependency(argo_install)

# //*********************************************************************//
# //************************ 2. Setup Arc Jupyter ***********************//
# //********* interactive user interface to develop Spark ETL ***********//
# //*********************************************************************//
        jhub_install= eks_cluster.my_cluster.add_helm_chart('JHubChart',
            chart='jupyterhub',
            repository='https://jupyterhub.github.io/helm-chart',
            release='jhub',
            version='0.10.4',
            namespace='jupyter',
            create_namespace=False,
            values=loadYamlReplaceVarLocal('../app_resources/jupyter-values.yaml', 
                fields={
                    "{{codeBucket}}": app_s3.code_bucket,
                    "{{region}}": self.region 
                })
        )
        # jhub_install.node.add_dependency(app_security)

        # configure JupyterHub
        name_parts= core.Fn.split('-',jhub_secret.secret_name)
        name_no_suffix=core.Fn.join('-',[core.Fn.select(0, name_parts), core.Fn.select(1, name_parts)])

        config_hub = eks.KubernetesManifest(self,'JHubConfig',
            cluster=eks_cluster.my_cluster,
            manifest=loadYamlReplaceVarLocal('../app_resources/jupyter-config.yaml', 
                fields= {
                    "{{MY_SA}}": etl_security.jupyter_sa,
                    "{{REGION}}": self.region, 
                    "{{SECRET_NAME}}": name_no_suffix
                }, 
                multi_resource=True)
        )
        # config_hub.node.add_dependency(eks_security)
        config_hub.node.add_dependency(jhub_install)

# //******************************************************************************//
# //************* 3. Add CloudFront to enable HTTPS Endpoint (OPTIONAL) *********//
# //*************  to encrypt request between user and web apps ****************//
# //***************************************************************************//
        jhub_alb = alb.ApplicationLoadBalancer.from_lookup(self, "ALBJHub",
            load_balancer_tags={
                "ingress.k8s.aws/stack": "jupyter/jupyterhub",
                "elbv2.k8s.aws/cluster": eksname
            }
        ) 
        jhub_alb.node.add_dependency(config_hub)
        jhub_cf = CloudFrontConst(self,'jhubCloudFront', alb=jhub_alb, port=8000)
        
        argo_alb = alb.ApplicationLoadBalancer.from_lookup(self, "ALBArgo",
            load_balancer_tags={
                "ingress.k8s.aws/stack": "argo/argo-server",
                "elbv2.k8s.aws/cluster": eksname
            }
        )   
        argo_alb.node.add_dependency(argo_install)  
        argo_cf = CloudFrontConst(self,'argoCloudFront', alb=argo_alb, port=2746)

# //*********************************************************************//
# //*************************** Deployment Output ***********************//
# //*********************************************************************//

        # core.CfnOutput(self,'JUPYTER_ALB_URL', value='http://'+ jhub_alb.load_balancer_dns_name + ':8000')
        # core.CfnOutput(self,'ARGO_ALB_URL', value='http://'+ argo_alb.load_balancer_dns_name+ ':2746')

        core.CfnOutput(self,'JUPYTER_URL', value='https://'+ jhub_cf.distribution.distribution_domain_name)
        core.CfnOutput(self,'ARGO_URL', value='https://'+ argo_cf.distribution.distribution_domain_name)
        core.CfnOutput(self,'CODE_BUCKET', value=app_s3.code_bucket)