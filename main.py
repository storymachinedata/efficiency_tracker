import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots


st.set_page_config(layout="wide")
st.sidebar.header(" ")

# Date indentifiers
current_date =  datetime.now().strftime('%Y-%m-%d')
month_start  =   datetime.now().replace(day=1).strftime('%Y-%m-%d')


st.title(f'Data team efficiency tracker from {month_start} to {current_date}')


# read the metadata excel and get the projectids for each projects
# use the list of the ids and arrange the dataframe

metadata = pd.read_excel('projects_metadata.xlsx', sheet_name = 'metadata')
metadata.columns =  ['project', 'team', 'Director', 'Senior', 'Mid Level']
metadata = metadata.drop(columns=['team'])
metadata = metadata.melt(id_vars=['project'], var_name='level', value_name='Allocated Hours')

proj2Id_mapper = pd.read_excel('projects_metadata.xlsx', sheet_name = 'projectids')
proj2Id_mapper = dict(zip(proj2Id_mapper['id'],proj2Id_mapper['client'] ))




result_list = []
for proj_id in proj2Id_mapper.keys():
    url = f'https://storymachine.mocoapp.com/api/v1/activities?from={month_start}&to={current_date}&project_id={proj_id}'
    headers = {
        'Authorization': 'Token token=7293370628a1aa45f11c4a127db97356'
    }

    response = requests.get(url, headers=headers)
    response_df = pd.DataFrame(response.json())

    if not response_df.empty:
        result_list.append(response_df)
    
if result_list: 
    merged_df = pd.concat(result_list)  

#merged_df = pd.read_excel('text.xlsx')

merged_df = merged_df[merged_df.billable==True]

# cleaning the obtained dataframe
merged_df['level'] = merged_df.task.apply(lambda x: x['name'])
merged_df['level'] = merged_df['level'].replace(r'.*Mid.*', 'Mid Level', regex=True)
merged_df['level'] = merged_df['level'].replace(r'.*Director.*', 'Director', regex=True)
merged_df['level'] = merged_df['level'].replace(r'.*Senior.*', 'Senior', regex=True)
merged_df['level'] = merged_df['level'].replace(r'.*Senior.*', 'Senior', regex=True)
merged_df['proj_id'] = merged_df['project'].apply(lambda x: x['id'])
merged_df = merged_df[['proj_id', 'billable',  'hours', 'level']]
merged_df['project'] = merged_df.proj_id.apply(lambda x: proj2Id_mapper[x])
merged_df = merged_df.groupby(['project', 'level'])['hours'].agg('sum').unstack(level=1).fillna(0).reset_index()
merged_df = merged_df.melt(id_vars=['project'], var_name='level', value_name='Hours Worked')


# merge two dataframes for final graph
final_merge = pd.merge(merged_df, metadata, on=['project', 'level'])
grouped_df = final_merge.groupby('project')

# Define the number of columns for the grid layout
num_columns = 2

# Calculate the number of rows required based on the number of projects and columns
num_projects = len(grouped_df)
num_rows = (num_projects + num_columns - 1) // num_columns

# dummy labels to use as placeholders
dummy_labels = [f'Project {i}' for i in range(num_projects)]

# Create the subplot figure
fig = make_subplots(rows=num_rows, cols=num_columns,   subplot_titles=dummy_labels)

# Track the current row and column position
row = 1
col = 1

color_worked_hours = 'green'
color_allocated_hours = 'red'

# Iterate over each project and plot the bar chart in the corresponding subplot
for i, (project, group) in enumerate(grouped_df):
    # Calculate the subplot index
    subplot_idx = (row, col)
    
    # Add allocated hours trace
    fig.add_trace(go.Bar(
        x=group['level'],
        y=group['Allocated Hours'],
        name='Allocated Hours',
        marker=dict(color=color_allocated_hours)
    ), row=row, col=col)

    # Add hours worked trace
    fig.add_trace(go.Bar(
        x=group['level'],
        y=group['Hours Worked'],
        name='Hours Worked',
        marker=dict(color=color_worked_hours)  
    ), row=row, col=col)


    fig.layout.annotations[i]['text'] =  project
    # Update layout settings for the subplot
    fig.update_layout(
        barmode='group',
        height=400,
        showlegend=True,
        xaxis_title='Level',
        yaxis_title='Hours',
          
    )

    # Move to the next column
    col += 1

    # If the end of the row is reached, move to the next row and reset the column position
    if col > num_columns:
        col = 1
        row += 1

fig.update_layout(
    height=400 * num_rows,
    #legend=dict(orientation='h', yanchor='bottom', y=1.02,xanchor='right', x=1),
)

st.plotly_chart(fig, use_container_width=True)



data_as_csv= final_merge.to_csv(index=False).encode("utf-8")

submit = st.sidebar.button('View Raw Data')
st.sidebar.download_button(
    "Download Data as CSV", 
    data_as_csv, 
    "benchmark-tools.csv",
    "text/csv",
    key="download-tools-csv",
)

# Main content
if submit:
    st.write(final_merge)























