import streamlit  as st 
import pandas as pd 
import numpy as np 
from io import BytesIO


st.set_page_config(layout='wide')

int_sx, int_dx = st.columns([6,1])
with int_sx:
    st.title('Carico macchine')
st.divider()
with int_dx:
    st.image('logo.png')


#Funzioni

def scarica_excel(df, filename):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1',index=False)
    writer.close()

    st.download_button(
        label="Download Excel workbook",
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.ms-excel"
    )

def elabora_tabella(df, numero_settimane, flat):
    '''
    df = tabella da elaborare,
    numero_settimane = settimane da visualizzare,
    flat = file statico con info isole
    '''
    # cambio dei nomi delle colonne e selezione del numero di settimane
    lista_colonne = list(df.columns)
    lista_colonne_new = []
    lista_colonne_sett = []

    for elemento in lista_colonne:
        if elemento[:4]=='Sett':
            elemento_new = str(elemento).replace('Settimana ','')
            elemento_new = elemento_new[:7]
            lista_colonne_sett.append(elemento_new)
            
        else:
            elemento_new = elemento
            lista_colonne_new.append(elemento_new)

    new_names = lista_colonne_new + lista_colonne_sett
    dic_new_names = dict(zip(lista_colonne,new_names))
    df = df.rename(columns=dic_new_names)
    lista_colonne_sett = lista_colonne_sett[:numero_settimane]
    colonne_new = lista_colonne_new + lista_colonne_sett
    df = df[colonne_new]

    # creazione mapping
    df['macchina'] = df['Centro di lavoro'].astype(str)+"-"+df.Macchina.astype(str)
    df = df.drop(columns=['Centro di lavoro','Macchina','Ore totali'])
    df = df.merge(flat, how='left', left_on='macchina', right_on='macchina')

    # calcolo giorni
    colonne_old = df.columns
    for i in range(numero_settimane):
        nome_nuova_colonna = str(colonne_old[i])+"[gg]"
        df[nome_nuova_colonna] = np.round(df[colonne_old[i]]/df.ore_disponibili,1)
        df.drop(columns=colonne_old[i], inplace=True)

    df['Giorni Totali'] = df[df.columns[(len(df.columns)-numero_settimane):]].sum(axis=1)
    df = df.sort_values(by='isole').reset_index(drop=True)
    df['ore_disponibili'] = df['ore_disponibili'].astype(str)
    col1 = df.pop('ore_disponibili')
    df.insert(0, 'ore_disponibili', col1)
    col2 = df.pop('isole')
    df.insert(1, 'isole', col2)

    return df

def highlight(s):
        if s.isole=='A' or s.isole=='C' or s.isole=='E'or s.isole=='G'or s.isole=='I'  or s.isole=='M' or s.isole=='O' or s.isole=='Q' :
            return ['background-color: #FFFF00']*len(s)
        else:
            return ['background-color: #46B1E1']*len(s)


# Caricamento dati =======================================================================================================================

numero_settimane = st.sidebar.number_input('Inserire il numero di settimane da visualizzare', min_value=4, max_value=24, step=1, value=12)

path_mapping = st.sidebar.file_uploader('Caricare il file "Flat_file.xlsx"')
if not path_mapping:
    st.warning('"Flat_file.xlsx" non caricato, aprire sidebar e caricare file')
    st.stop()
flat_file = pd.read_excel(path_mapping)


path_si_scorte = st.sidebar.file_uploader('Caricare il file "SI SCORTE"')
if not path_si_scorte:
    st.warning('File "SI SCORTE" non caricato')
    st.stop()
df_si_scorte = pd.read_excel(path_si_scorte)
df_si_scorte.drop(columns=['Ore prima','Ordine simulato', 'Potenziale medio ore','Ore oltre','Numero addetti'], inplace=True)

path_no_scorte = st.sidebar.file_uploader('Caricare il file "NO SCORTE"')
if not path_no_scorte:
    st.warning('File "NO SCORTE" non caricato')
    st.stop()
df_no_scorte = pd.read_excel(path_si_scorte)
df_no_scorte.drop(columns=['Ore prima','Ordine simulato', 'Potenziale medio ore','Ore oltre','Numero addetti'], inplace=True)

# Esecuzione =============================================================================================================================

df_si_scorte = elabora_tabella(df_si_scorte, numero_settimane, flat_file)

st.subheader('SI SCORTE')
st.dataframe(df_si_scorte.style.apply(highlight, axis=1).format("{:.1f}", subset=df_si_scorte.select_dtypes(include='number').columns), height=1000)
scarica_excel(df_si_scorte, 'si_scorte.xlsx')

df_no_scorte = elabora_tabella(df_no_scorte, numero_settimane, flat_file)
st.subheader('NO SCORTE')
st.dataframe(df_no_scorte.style.apply(highlight, axis=1).format("{:.1f}", subset=df_no_scorte.select_dtypes(include='number').columns), height=1000)
scarica_excel(df_no_scorte, 'no_scorte.xlsx')



