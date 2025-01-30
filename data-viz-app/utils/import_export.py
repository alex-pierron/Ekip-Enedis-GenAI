import os 
import io 
import base64
import dash 
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import dcc, html

def export_table_to_excel(n_clicks, table_data):
    if n_clicks is None or n_clicks == 0 or not table_data:
        return dash.no_update

    # convert the data back to a DataFrame
    export_df = pd.DataFrame(table_data)
    
    # write it to xlsx file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)

    # prepare the file for download
    return dcc.send_bytes(output.read(), "data_table.xlsx")



def import_uploaded_pdf(contents, filenames, output_folder='output'):

    if contents is None:
        raise PreventUpdate

    n_files=0
    os.makedirs(output_folder, exist_ok=True)
    
    # iterate over given files
    for content, filename in zip(contents, filenames):
        content_type, content_string = content.split(',')
        decoded_pdf = base64.b64decode(content_string)

        # import it
        file_path = os.path.join(output_folder, filename)
        with open(file_path, 'wb') as f:
            f.write(decoded_pdf)
        
        n_files+=1
    
    if n_files > 1:
        success_str = f"{n_files} fichiers ont été importés !"
    else:
        success_str = f"{n_files} fichier a été importé !"

    return html.Button(success_str, className='btn btn-success')
