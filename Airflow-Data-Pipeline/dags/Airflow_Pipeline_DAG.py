from datetime import datetime, timedelta

from airflow.decorators import dag
from airflow.operators.dummy_operator import DummyOperator

from pluginsOperator.stage_redshift import StageToRedshiftOperator
from pluginsOperator.load_fact import LoadFactOperator
from pluginsOperator.load_dimension import LoadDimensionOperator
from pluginsOperator.data_quality import DataQualityOperator

from sql_statements.sql_statements import SqlQueries

default_args = {
    'owner': 'TingLu',
    'depends_on_past': False,
    'start_date': datetime(2018, 11, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
    'email_on_retry': False
}


@dag(
    default_args=default_args,
    description='Load and transform data in Redshift with Airflow',
    end_date=datetime(2018, 11, 2),
    schedule_interval='@hourly'
)
def Airflow_Pipeline_TL():

    start_operator = DummyOperator(task_id='Begin_execution')

    stage_events_to_redshift = StageToRedshiftOperator(
        task_id='Stage_events',
        table='staging_events',
        redshift_conn_id='redshift',
        aws_credentials_id='aws_credentials',
        s3_bucket='sparkify-airflow',
        s3_key='log-data'
    )

    stage_songs_to_redshift = StageToRedshiftOperator(
        task_id='Stage_songs',
        table='staging_songs',
        redshift_conn_id='redshift',
        aws_credentials_id='aws_credentials',
        s3_bucket='sparkify-airflow',
        s3_key='song-data/A/A/'
    )

    load_songplays_table = LoadFactOperator(
        task_id='Load_songplays_fact_table',
        redshift_conn_id='redshift',
        table='songplays',
        sql_query=SqlQueries.songplay_table_insert
    )

    load_user_dimension_table = LoadDimensionOperator(
        task_id='Load_user_dim_table',
        redshift_conn_id='redshift',
        table='users',
        sql_query=SqlQueries.user_table_insert,
        mode='truncate-insert'
    )

    load_song_dimension_table = LoadDimensionOperator(
        task_id='Load_song_dim_table',
        redshift_conn_id='redshift',
        table='songs',
        sql_query=SqlQueries.song_table_insert,
        mode='truncate-insert'
    )

    load_artist_dimension_table = LoadDimensionOperator(
        task_id='Load_artist_dim_table',
        redshift_conn_id='redshift',
        table='artists',
        sql_query=SqlQueries.artist_table_insert,
        mode='truncate-insert'
    )

    load_time_dimension_table = LoadDimensionOperator(
        task_id='Load_time_dim_table',
        redshift_conn_id='redshift',
        table='time',
        sql_query=SqlQueries.time_table_insert,
        mode='truncate-insert'
    )

    run_quality_checks = DataQualityOperator(
        task_id='Run_data_quality_checks',
        redshift_conn_id='redshift',
        tables=['songplays', 'users', 'songs', 'artists', 'time']
    )

    end_operator = DummyOperator(task_id='Stop_execution')

    start_operator >> stage_events_to_redshift
    start_operator >> stage_songs_to_redshift

    stage_events_to_redshift >> load_songplays_table
    stage_songs_to_redshift >> load_songplays_table

    load_songplays_table >> load_user_dimension_table
    load_songplays_table >> load_song_dimension_table
    load_songplays_table >> load_artist_dimension_table
    load_songplays_table >> load_time_dimension_table

    [load_user_dimension_table, load_song_dimension_table, load_artist_dimension_table, load_time_dimension_table] >> run_quality_checks

    run_quality_checks >> end_operator
    
Airflow_Pipeline_TL = Airflow_Pipeline_TL()