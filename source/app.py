#!/usr/bin/env python3
from aws_cdk import core
from bin.config_map import ConfigSectionMap
from lib.base_infra_stack import BaseEksInfraStack

app = core.App()

# Get environment vars for 'cdk synth -c env=develop'
target_env = app.node.try_get_context('env')
account = ConfigSectionMap(target_env)['account']
region = ConfigSectionMap(target_env)['region']
env = core.Environment(account=account, region=region)

eks_name = app.node.try_get_context('cluster_name') + '-' + ConfigSectionMap(target_env)['env_str']
eksadmin_name = app.node.try_get_context('cluster_admin_name')

# Spin up CDK stacks
eks_stack = BaseEksInfraStack(app, 'SparkOnEKS', eks_name, eksadmin_name, env=env)
# code_pipeline_stack = AWSAppResourcesPipeline(app, "ResourcesPipelineStack", env=env)

core.Tags.of(eks_stack).add('project', 'sqlbasedetl')
# core.Tags.of(code_pipeline_stack).add('project', 'sqlbasedetl')

app.synth()
