### Import all required libraries

import tableauserverclient as t
import pandas as pd
import json
import ast
import re

### Connect to Tableau server using personal access token
tableau_auth = t.PersonalAccessTokenAuth("<API_TOKEN_NAME>", "<TOKEN_KEY>", 
                                           site_id="<YOUR_SITE>")
server = t.Server("https://dub01.online.tableau.com/", use_server_version=True)

with server.auth.sign_in(tableau_auth):
        print("Connected")

############### Get all the list of data sources on your Site

### Below is the query to get the list of all published data sources on the site. 
# We also get the owner of the data source and their email in case we want to know whom to contact later.
all_datasources_query = """ {
  publishedDatasources {
    name
    id
    owner {
    name
    email
    }
  }
}"""
with server.auth.sign_in(tableau_auth):
    result = server.metadata.query(
        all_datasources_query
    )

### We need to convert the response into dataframe for easy data manipulation

col_names = result['data']['publishedDatasources'][0].keys()
master_df = pd.DataFrame(columns=col_names)

for i in result['data']['publishedDatasources']:
    tmp_dt = {k:v for k,v in i.items()}
    master_df = pd.concat([master_df, pd.DataFrame.from_dict(tmp_dt, orient='index').T])

# Extract the owner name and email from the owner object
master_df['owner_name'] = master_df['owner'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)
master_df['owner_email'] = master_df['owner'].apply(lambda x: x.get('email') if isinstance(x, dict) else None)

master_df.reset_index(inplace=True)
master_df.drop(['index','owner'], axis=1, inplace=True)
print('There are ', master_df.shape[0] , ' datasources in your site')

############### Get the data sources and the table names from all the custom sql queries used on your Site

### Below is the query to get the list of all custom sqls used in the site along with their data sources.
# I have filtered the to get only 500 custom sql queries. 
# In case there are more in your org, you will have to use offset to get the next set of custom sql queries.

custom_table_query = """  {
  customSQLTablesConnection(first: 500){
    nodes {
        id
        name
        downstreamDatasources {
        name
        }
        query
    }
  }
}
"""

with server.auth.sign_in(tableau_auth):
    custom_table_query_result = server.metadata.query(
        custom_table_query
    )

### Convert the custom sql response into dataframe
col_names = custom_table_query_result['data']['customSQLTablesConnection']['nodes'][0].keys()
cs_df = pd.DataFrame(columns=col_names)

for i in custom_table_query_result['data']['customSQLTablesConnection']['nodes']:
    tmp_dt = {k:v for k,v in i.items()}

    cs_df = pd.concat([cs_df, pd.DataFrame.from_dict(tmp_dt, orient='index').T])

# Extract the data source name where the custom sql query was used
cs_df['data_source'] = cs_df.downstreamDatasources.apply(lambda x: x[0]['name'] if x and 'name' in x[0] else None)
cs_df.reset_index(inplace=True)
cs_df.drop(['index','downstreamDatasources'], axis=1,inplace=True)

### We need to extract the table names from the sql query. We know the table name comes after FROM or JOIN clause
# Note that the name of table can be of the format <data_warehouse>.<schema>.<table_name>
# Depending on the format of how table is called, you will have to modify the regex expression

def extract_tables(sql):
    # Regex to match database.schema.table or schema.table, avoid alias
    pattern = r'(?:FROM|JOIN)\s+((?:\[\w+\]|\w+)\.(?:\[\w+\]|\w+)(?:\.(?:\[\w+\]|\w+))?)\b'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return list(set(matches))  # Unique table names

cs_df['customSQLTables'] = cs_df['query'].apply(extract_tables)
cs_df = cs_df[['data_source','customSQLTables']]

# We need to merge datasources as there can be multiple custom sqls used in the same data source
cs_df = cs_df.groupby('data_source', as_index=False).agg({
    'customSQLTables': lambda x: list(set(item for sublist in x for item in sublist))  # Flatten & make unique
})

print('There are ', cs_df.shape[0], 'datasources with custom sqls used in it')

############### Get the data sources with the regular table names used in your site

### Its best to extract the tables information for every data source and then merge the results.
# Since we only get the table information nested under fields, in case there are hundreds of fields 
# used in a single data source, we will hit the response limits and will not be able to retrieve all the data.

data_source_list = master_df.name.tolist()

col_names = ['name', 'id', 'extractLastUpdateTime', 'fields']
ds_df = pd.DataFrame(columns=col_names)

with server.auth.sign_in(tableau_auth):
    for ds_name in data_source_list:
        query = """ {
            publishedDatasources (filter: { name: \""""+ ds_name + """\" }) {
            name
            id
            extractLastUpdateTime
            fields {
                name
                upstreamTables {
                    name
                }
            }
            }
        } """
        ds_name_result = server.metadata.query(
        query
        )
        for i in ds_name_result['data']['publishedDatasources']:
            tmp_dt = {k:v for k,v in i.items() if k != 'fields'}
            tmp_dt['fields'] = json.dumps(i['fields'])
        ds_df = pd.concat([ds_df, pd.DataFrame.from_dict(tmp_dt, orient='index').T])
        

ds_df.reset_index(inplace=True)

# Function to extract the values of fields and upstream tables in json lists
def extract_values(json_list, key):
    values = []
    for item in json_list:
        values.append(item[key])
    return values

ds_df["fields"] = ds_df["fields"].apply(ast.literal_eval)
ds_df['field_names'] = ds_df.apply(lambda x: extract_values(x['fields'],'name'), axis=1)
ds_df['upstreamTables'] = ds_df.apply(lambda x: extract_values(x['fields'],'upstreamTables'), axis=1)

# Function to extract the unique table names 
def extract_upstreamTable_values(table_list):
    values = set()
    for inner_list in table_list:
        for item in inner_list:
            if 'name' in item:
                values.add(item['name'])
    return list(values)

ds_df['upstreamTables'] = ds_df.apply(lambda x: extract_upstreamTable_values(x['upstreamTables']), axis=1)
ds_df.drop(["index","fields"], axis=1, inplace=True)

###### Join all the data together
master_data = pd.merge(master_df, ds_df, how="left", on=["name","id"])
master_data = pd.merge(master_data, cs_df, how="left", left_on="name", right_on="data_source")

# Save the results to analyse further
master_data.to_excel("Tableau Data Sources with Tables.xlsx", index=False)

### Function to filter for a specific table if used in data source or in its custom sql
def filter_rows_with_table(df, col1, col2, target_table):
    return df[
        df.apply(
            lambda row: 
                (isinstance(row[col1], list) and any(target_table in item for item in row[col1])) or
                (isinstance(row[col2], list) and any(target_table in item for item in row[col2])),
            axis=1
        )
    ]

# As an example 
# filter_rows_with_table(master_data, 'upstreamTables', 'customSQLTables', 'dim_date')
