from aws_cdk import (
    Stack,
    aws_route53 as route53,
    CfnOutput,
    Fn
)
from constructs import Construct

class DashboardSubdomainZoneStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a public hosted zone specifically for 'dashboard.minoko.life'
        dashboard_hosted_zone = route53.PublicHostedZone(self, "DashboardMinokoLifeHostedZone",
                                                         zone_name="dashboard.minoko.life",
                                                         comment="Hosted zone for the dashboard subdomain of minoko.life"
                                                         # You can enable query logging if needed:
                                                         # query_logs_log_group_arn="arn:aws:logs:REGION:ACCOUNT_ID:log-group:YOUR_LOG_GROUP_NAME"
                                                         )

        # Output the Hosted Zone ID
        CfnOutput(self, "DashboardHostedZoneId",
                  value=dashboard_hosted_zone.hosted_zone_id,
                  description="Hosted Zone ID for dashboard.minoko.life"
                  )

        # Output the Name Servers for this new hosted zone.
        # These are the NS records that need to be added to the parent 'minoko.life' zone.
        CfnOutput(self, "DashboardNameServers",
                  value=Fn.join(",", dashboard_hosted_zone.hosted_zone_name_servers), # Use Fn.join for CDK token lists
                  description="Name servers for dashboard.minoko.life. Add these as NS records in the minoko.life zone."
                  )

        # Now you can add records within this 'dashboard.minoko.life' zone.
        # For example, an A record for dashboard.minoko.life itself (which is the zone apex here)
        # pointing to an IP address or an alias to an AWS resource.

        # Example: Adding an A record for dashboard.minoko.life pointing to an IP
        # route53.ARecord(self, "DashboardApexARecord",
        #     zone=dashboard_hosted_zone,
        #     # For the zone apex, record_name is implicitly the zone_name.
        #     # You can also explicitly set it to dashboard_hosted_zone.zone_name or leave it out.
        #     target=route53.RecordTarget.from_ip_addresses("192.0.2.42"), # Replace with actual IP
        #     comment="Apex A record for dashboard.minoko.life"
        # )

        # Example: Adding a CNAME for something like 'api.dashboard.minoko.life'
        # route53.CnameRecord(self, "ApiDashboardCname",
        #     zone=dashboard_hosted_zone,
        #     record_name="api", # This will become api.dashboard.minoko.life
        #     domain_name="your-api-endpoint.example.com" # Replace with actual target
        # )
