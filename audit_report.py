import psycopg2  # Import the psycopg2 module for working with PostgreSQL databases
import json  # Import the json module for working with JSON files
import csv  # Import the csv module for working with CSV files
from entity_report import Entity  # Import the Entity class from entity_rapport module
import os
def write_csv(results, csv_file):
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(results)
def build_map(cur, table):
    query = f"SELECT {table['primaryKey']}, {table['destColumn']} FROM {table['tableName']}"
    cur.execute(query)  # Execute the query
    data = cur.fetchall()  # Fetch all the rows returned by the query
    map = {}
    for line in data:
        id = line[0]
        name = line[1]
        map[id] = name
    return map
def generate_audit_report ():
    configs_folder = "configs"
    with open( os.path.join ( configs_folder, "global_config.json"), 'r', encoding='utf-8') as file:
        global_configs = json.load(file)
    ReportLines = [global_configs["columns_titles"]]  # Initialize the ReportLines list with column titles
    dbConfig = global_configs["databaseConnection"]  # Get the database connection configuration
    conn = psycopg2.connect(
        host=dbConfig["host"],
        port=dbConfig["port"],
        database=dbConfig["database"],
        user=dbConfig["user"],
        password=dbConfig["password"])
    cur = conn.cursor()  # Create a cursor object to execute database queries
    allMap = {}
    aux_tables = global_configs["aux_tables"]  # Get the database connection configuration
    mapPrincipal = {}
    for table in aux_tables:
        map = build_map(cur, table)
        allMap[table["foreignKey"]] = map
        if table["principal"] == True :
            mapPrincipal = map
    listConfig = global_configs["entities_configs"]
    for config in listConfig:
        entity = Entity(dbConfig,  os.path.join ( configs_folder, config), cur, global_configs["principalFK"], allMap, mapPrincipal) # Create an instance of the Entity class for the  entity
        ReportLines.extend(entity.getEntityLines())  # Retrieve entity lines and Add the result to the ReportLines list 
    cur.close()  # Close the cursor
    conn.close()  # Close the database connection
    write_csv( ReportLines, "audit_client_report.csv")  # Write the ReportLines data to a CSV file
    return "audit_client_report has been generated successfully"
generate_audit_report()