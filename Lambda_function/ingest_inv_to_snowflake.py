import os
import json
import requests
import snowflake.connector as sf

def lambda_handler(event, context):
    
    # TODO implement
    url = os.environ['S3_URL']
    destination_folder = '/tmp'
    file_name = 'inventory.csv'
    file_path = '/tmp/inventory.csv'
    
    # Snowflake connection parameters
    account = os.environ['ACCOUNT']
    warehouse = os.environ['WAREHOUSE']
    database = os.environ['DATABASE']
    schema = os.environ['SCHEMA']
    table = 'inventory'
    user = os.environ['USER']
    password = os.environ['PASSWORD']
    role='accountadmin'
    stage_name = 'inv_Stage'

    # Download the data from the API endpoint
    response = requests.get(url)
    response.raise_for_status()
    
    
    # Save the data to the destination file in /tmp directory
    with open(file_path, 'wb') as file:
        file.write(response.content)
        
    with open(file_path, 'r') as file:
        file_content = file.read()


    # # Establish Snowflake connection
    conn = sf.connect(user = user, password = password, \
                    account = account, warehouse=warehouse, \
                    database=database,  schema=schema,  role=role)
    
    
    cursor = conn.cursor()
    
    #use database
    use_database = f"use database {database};"
    cursor.execute(use_database)
    
    # use schema
    use_schema = f"use schema {schema};"
    cursor.execute(use_schema)

    # create CSV format
    create_csv_format = f"CREATE or REPLACE FILE FORMAT COMMA_CSV TYPE ='CSV' FIELD_DELIMITER = ',';"
    cursor.execute(create_csv_format)
    
    
    create_stage_query = f"CREATE OR REPLACE STAGE {stage_name} FILE_FORMAT =COMMA_CSV"
    cursor.execute(create_stage_query)
    
    # Copy the file from local to the stage
    copy_into_stage_query = f"PUT 'file://{file_path}' @{stage_name}"
    cursor.execute(copy_into_stage_query)
    
    # List the stage
    list_stage_query = f"LIST @{stage_name}"
    cursor.execute(list_stage_query)
    
    # truncate table
    truncate_table = f"truncate table {schema}.{table};"  
    cursor.execute(truncate_table)    
    
    
    # Load the data from the stage into a table (example)
    copy_into_query = f"COPY INTO {schema}.{table} FROM @{stage_name}/{file_name} FILE_FORMAT =COMMA_CSV;" 
    cursor.execute(copy_into_query)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Snowflake_lambda!')
    }