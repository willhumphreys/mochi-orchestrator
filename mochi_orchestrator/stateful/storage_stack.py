from aws_cdk import (
    Stack,
    aws_s3 as s3,
    CfnOutput,
    RemovalPolicy
    # Include other necessary imports
)
from constructs import Construct


class MochiStorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create buckets with unique names
        self.buckets = {}

        # Raw historical data bucket
        self.buckets['raw_historical_data'] = s3.Bucket(
            self,
            'RawHistoricalData',
            bucket_name='mochi-prod-raw-historical-data',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'RawHistoricalDataBucketName',
            value=self.buckets['raw_historical_data'].bucket_name,
            description='Name of the raw historical data bucket',
            export_name='MochiStorage-RawHistoricalDataBucketName'
        )
        CfnOutput(
            self,
            'RawHistoricalDataBucketArn',
            value=self.buckets['raw_historical_data'].bucket_arn,
            description='ARN of the raw historical data bucket',
            export_name='MochiStorage-RawHistoricalDataBucketArn'
        )

        # Prepared historical data bucket
        self.buckets['prepared_historical_data'] = s3.Bucket(
            self,
            'PreparedHistoricalData',
            bucket_name='mochi-prod-prepared-historical-data',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'PreparedHistoricalDataBucketName',
            value=self.buckets['prepared_historical_data'].bucket_name,
            description='Name of the prepared historical data bucket',
            export_name='MochiStorage-PreparedHistoricalDataBucketName'
        )
        CfnOutput(
            self,
            'PreparedHistoricalDataBucketArn',
            value=self.buckets['prepared_historical_data'].bucket_arn,
            description='ARN of the prepared historical data bucket',
            export_name='MochiStorage-PreparedHistoricalDataBucketArn'
        )

        # Backtest trades bucket
        self.buckets['backtest_trades'] = s3.Bucket(
            self,
            'BacktestTrades',
            bucket_name='mochi-prod-backtest-trades',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'BacktestTradesBucketName',
            value=self.buckets['backtest_trades'].bucket_name,
            description='Name of the backtest trades bucket',
            export_name='MochiStorage-BacktestTradesBucketName'
        )
        CfnOutput(
            self,
            'BacktestTradesBucketArn',
            value=self.buckets['backtest_trades'].bucket_arn,
            description='ARN of the backtest trades bucket',
            export_name='MochiStorage-BacktestTradesBucketArn'
        )

        # Backtest traders bucket
        self.buckets['backtest_traders'] = s3.Bucket(
            self,
            'BacktestTraders',
            bucket_name='mochi-prod-backtest-traders',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'BacktestTradersBucketName',
            value=self.buckets['backtest_traders'].bucket_name,
            description='Name of the backtest traders bucket',
            export_name='MochiStorage-BacktestTradersBucketName'
        )
        CfnOutput(
            self,
            'BacktestTradersBucketArn',
            value=self.buckets['backtest_traders'].bucket_arn,
            description='ARN of the backtest traders bucket',
            export_name='MochiStorage-BacktestTradersBucketArn'
        )

        # Aggregated trades bucket
        self.buckets['aggregated_trades'] = s3.Bucket(
            self,
            'AggregatedTrades',
            bucket_name='mochi-prod-aggregated-trades',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'AggregatedTradesBucketName',
            value=self.buckets['aggregated_trades'].bucket_name,
            description='Name of the aggregated trades bucket',
            export_name='MochiStorage-AggregatedTradesBucketName'
        )
        CfnOutput(
            self,
            'AggregatedTradesBucketArn',
            value=self.buckets['aggregated_trades'].bucket_arn,
            description='ARN of the aggregated trades bucket',
            export_name='MochiStorage-AggregatedTradesBucketArn'
        )

        # Athena query staging bucket
        self.buckets['athena_query_staging'] = s3.Bucket(
            self,
            'AthenaQueryStaging',
            bucket_name='mochi-prod-athena-query-staging',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'AthenaQueryStagingBucketName',
            value=self.buckets['athena_query_staging'].bucket_name,
            description='Name of the Athena query staging bucket',
            export_name='MochiStorage-AthenaQueryStagingBucketName'
        )
        CfnOutput(
            self,
            'AthenaQueryStagingBucketArn',
            value=self.buckets['athena_query_staging'].bucket_arn,
            description='ARN of the Athena query staging bucket',
            export_name='MochiStorage-AthenaQueryStagingBucketArn'
        )

        # Summary graphs bucket
        self.buckets['summary_graphs'] = s3.Bucket(
            self,
            'SummaryGraphs',
            bucket_name='mochi-prod-summary-graphs',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'SummaryGraphsBucketName',
            value=self.buckets['summary_graphs'].bucket_name,
            description='Name of the summary graphs bucket',
            export_name='MochiStorage-SummaryGraphsBucketName'
        )
        CfnOutput(
            self,
            'SummaryGraphsBucketArn',
            value=self.buckets['summary_graphs'].bucket_arn,
            description='ARN of the summary graphs bucket',
            export_name='MochiStorage-SummaryGraphsBucketArn'
        )

        # Trade extracts bucket
        self.buckets['trade_extracts'] = s3.Bucket(
            self,
            'TradeExtracts',
            bucket_name='mochi-prod-trade-extracts',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'TradeExtractsBucketName',
            value=self.buckets['trade_extracts'].bucket_name,
            description='Name of the trade extracts bucket',
            export_name='MochiStorage-TradeExtractsBucketName'
        )
        CfnOutput(
            self,
            'TradeExtractsBucketArn',
            value=self.buckets['trade_extracts'].bucket_arn,
            description='ARN of the trade extracts bucket',
            export_name='MochiStorage-TradeExtractsBucketArn'
        )

        # Trade performance graphs bucket
        self.buckets['trade_performance_graphs'] = s3.Bucket(
            self,
            'TradePerformanceGraphs',
            bucket_name='mochi-prod-trade-performance-graphs',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'TradePerformanceGraphsBucketName',
            value=self.buckets['trade_performance_graphs'].bucket_name,
            description='Name of the trade performance graphs bucket',
            export_name='MochiStorage-TradePerformanceGraphsBucketName'
        )
        CfnOutput(
            self,
            'TradePerformanceGraphsBucketArn',
            value=self.buckets['trade_performance_graphs'].bucket_arn,
            description='ARN of the trade performance graphs bucket',
            export_name='MochiStorage-TradePerformanceGraphsBucketArn'
        )

        # Final trader ranking bucket
        self.buckets['final_trader_ranking'] = s3.Bucket(
            self,
            'FinalTraderRanking',
            bucket_name='mochi-prod-final-trader-ranking',
            removal_policy=RemovalPolicy.RETAIN

        )
        CfnOutput(
            self,
            'FinalTraderRankingBucketName',
            value=self.buckets['final_trader_ranking'].bucket_name,
            description='Name of the final trader ranking bucket',
            export_name='MochiStorage-FinalTraderRankingBucketName'
        )
        CfnOutput(
            self,
            'FinalTraderRankingBucketArn',
            value=self.buckets['final_trader_ranking'].bucket_arn,
            description='ARN of the final trader ranking bucket',
            export_name='MochiStorage-FinalTraderRankingBucketArn'
        )

        # Keep existing references for backward compatibility
        self.input_bucket = self.buckets['raw_historical_data']
        self.output_bucket = self.buckets['prepared_historical_data']
