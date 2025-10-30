# note di sviluppo
# pareto fermate per macchina

# dopo aver messo il filtro
# pareto tipologie di fermata per macchina

# istogramma dei setup


import streamlit  as st 
import pandas as pd 
import numpy as np 
import datetime as dt
import plotly_express as px
import plotly.graph_objects as go
from io import BytesIO


st.set_page_config(layout='wide')
int_sx, int_dx = st.columns([6,1])
with int_sx:
    st.title('Dashboard fermi impianto')
st.divider()
with int_dx:
    st.image('logo.png')


#Configurazione
f_size = 18
f_angle =-45
stile = {
    'colore_barre':'#E3B14C',
    'colore_linea':'#CD3128',
    'name_bar':'Durata',
    'name_cum':'cum_pct',
    'y_name': 'Durata [h]',
    'y2_name': 'pct_cumulativa',
    'tick_size':16,
    'angle':-45
}

light_yellows = px.colors.sequential.YlOrBr[:5]

#Funzioni

def pareto(df, label, value ,stile):
    '''
    - La funzione crea l'aggregazione dei valori per categoria, ordina decrescente e calcola la pct cumulativa
    - Fa il grafico
    - Label è la colonna con la categoria da raggruppare
    - Value è il valore, che viene SOMMATO
    
    '''
    df_work = df[[label, value]].groupby(by=label, as_index=False).sum()

    df_work = df_work.sort_values(by=value, ascending=False)
    df_work['pct'] = df_work[value] / df_work[value].sum()
    df_work['pct_cum'] = df_work['pct'].cumsum()
    pareto = go.Figure()

    pareto.add_trace(go.Bar(
        x=df_work[label],
        y=df_work[value],
        name=stile['name_bar'],
        marker_color=stile['colore_barre']
    ))

    pareto.add_trace(go.Scatter(
        x=df_work[label],
        y=df_work['pct_cum'],
        yaxis='y2',
        name=stile['name_cum'],
        marker_color=stile['colore_linea']
        )
    )

    pareto.update_layout(
        showlegend=False,
        yaxis=dict(
            title=dict(text=stile['y_name'], font = dict(size=stile['tick_size'])),
            side="left",
            tickfont=dict(size=stile['tick_size'])
            
        ),
        yaxis2=dict(
            title=dict(text=stile['y2_name'], font = dict(size=stile['tick_size'])),
            side="right",
            range=[0, 1],
            overlaying="y",
            tickmode="sync",
            tickformat=".0%",
            tickfont=dict(size=stile['tick_size'])

        ),
        xaxis=dict(
            tickfont=dict(size=stile['tick_size']),
            tickangle=stile['angle']
        )
    )

    return pareto

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

def tree_chart(df, colore):

    tree = px.treemap(
        df,
        path = [px.Constant('Totale fermi impianto'),'isole','macchina'],
        values = 'Totale tempo macchina',
        color = 'Totale tempo macchina',
        color_continuous_scale=colore,
        template = 'plotly_white'
        
    )

    tree.data[0].texttemplate = "%{label}<br>%{value:.0f} Ore"  # etichetta + valore formattato con separatore di migliaia
    tree.data[0].textfont.size = 15                       # dimensione testo
    tree.data[0].textfont.color = "black" 
    return tree

# Caricamento dati

path_mapping = st.sidebar.file_uploader('Caricare il file "Flat_file.xlsx"')
if not path_mapping:
    st.warning('"Flat_file.xlsx" non caricato, aprire sidebar e caricare file')
    st.stop()
flat = pd.read_excel(path_mapping)

path_dati = st.sidebar.file_uploader('Caricare il file dei fermi impianto')
if not path_dati:
    st.warning('File con registrazione fermate non caricato')
    st.stop()
df = pd.read_excel(path_dati)

# pre-pulizia dati
df = df[df['Numero registrazione'] != 0]
df = df[df['Dipendente'].astype(str) == 'nan']
df['data'] = [data.date() for data in df['Data registrazione']]
df['macchina'] = df['Centro di lavoro'].astype(int).astype(str)+"-"+df.Macchina.astype(int).astype(str)
df = df.drop(columns=['Centro di lavoro','Macchina'])
df = df.merge(flat[['macchina','isole']], how='left', left_on='macchina', right_on='macchina')

if st.toggle('Escludi "Mancanza Operatore 1'):
    df = df[df.Descrizione != 'Mancanza Operatore 1']
if st.toggle('Escludi "Mancanza Commesse'):
    df = df[df.Descrizione != 'Mancanza Commesse']
# Filtri e selezioni
# filtri a cascata


date_range = st.slider('Selezionare intervallo date', df['data'].min(), df['data'].max(), (df['data'].min(), df['data'].max()))
df = df[(df['data'] >= date_range[0]) & (df['data'] <= date_range[1]) ]

df_no_filter = df.copy()


tab1, tab2 = st.tabs(['Overview','Focus cambi stampo'])

with tab1:

    fil_1, fil_2 = st.columns([1,1])

    with fil_1:
        st.subheader('Treemap fermate', divider='yellow')
        treemap = st.empty()
        fil1_sx, fil1_dx = st.columns([1,1])
        with fil1_sx:
            tempo_totale = df['Totale tempo macchina'].sum()
            st.metric('Ore totali di femo impianti', value=f'{tempo_totale:.0f} Ore')



    with fil_2:
        st.subheader('Pareto causali', divider='yellow')
        fil2_sx, fil2_dx = st.columns([1,1])
        with fil2_sx:
            isola_selected = st.multiselect('Selezionare isole (nessuna isola selezionata = tutte le isole selezionate)', options=df.isole.unique())
            if isola_selected==[]:
                isola_selected = df.isole.unique()
            df = df[[ any(isola == check for isola in isola_selected) for check in df.isole.astype(str)]]

        with fil2_dx:
            macchina_selected = st.multiselect('Selezionare macchine (nessuna macchina selezionata = tutte le macchine selezionate)', options=df.macchina.unique())
            if macchina_selected==[]:
                macchina_selected = df.macchina.unique()
            df = df[[ any(macc == check for macc in macchina_selected) for check in df.macchina.astype(str)]]


        par = st.empty()

        causale_selected = st.multiselect('Seleziona causali', options=df.Descrizione.unique())
        if causale_selected == []:
            causale_selected = df.Descrizione.unique()
        
        df_macchine_causali = df[[ any(causale == check for causale in causale_selected) for check in df.Descrizione.astype(str)]]
        df_macchine_causali = df_macchine_causali.groupby(by='macchina').agg({'Totale tempo macchina':'sum'}).sort_values(by='Totale tempo macchina', ascending=False)
        df_macchine_causali
    

    # Grafici

    tree=tree_chart(df_no_filter, light_yellows)
    tree.update_traces(root_color='white')
    tree.update_layout(height=700, width=800, showlegend=False,coloraxis_showscale=False)
    treemap.plotly_chart(tree, use_container_width=True)


    pareto_test = pareto(df, 'Descrizione','Totale tempo macchina',stile)
    pareto_test.update_layout(height=800, width=800)
    par.plotly_chart(pareto_test, use_container_width=True)


    


with tab2: 
    macchina_selected_2 = st.multiselect('Selezionare macchine)', options=df.macchina.unique())
    if macchina_selected_2==[]:
        macchina_selected_2 = df.macchina.unique()
    df = df[[ any(macc == check for macc in macchina_selected_2) for check in df.macchina.astype(str)]]
     
    df_all = df_no_filter[df_no_filter.Descrizione == 'Cambio stampo 1']
    df_setup = df[df.Descrizione == 'Cambio stampo 1']

    df_all_count = df_all.groupby('macchina', as_index=False).agg({'Descrizione':'count', 'Totale tempo macchina':'sum'})
    df_all_count['Durata_media']=df_all_count['Totale tempo macchina'] / df_all_count['Descrizione']
    df_all_count.rename(columns={'Descrizione':'Conteggio setup'}, inplace=True)


    df_agg = df_setup.groupby('data', as_index=False).agg({'macchina':'count', 'Totale tempo macchina':'sum'})
    df_agg['Durata_media'] = df_agg['Totale tempo macchina'] / df_agg['macchina']
    df_agg['count_MA'] = df_agg['Durata_media'].rolling(5).mean()

    df_agg_nf = df_all.groupby('data', as_index=False).agg({'macchina':'count', 'Totale tempo macchina':'sum'})
    df_agg_nf['Durata_media'] = df_agg_nf['Totale tempo macchina'] / df_agg_nf['macchina']
    df_agg_nf['count_MA'] = df_agg_nf['Durata_media'].rolling(5).mean()


    confronto = go.Figure()

    confronto.add_trace(
        go.Scatter(x= df_agg_nf['data'] ,
                y=df_agg_nf.count_MA,
                line=dict(color='black'),
                name='Tutte le macchine')
    )
    confronto.add_trace(
        go.Scatter(x= df_agg['data'] ,
                y=df_agg.count_MA,
                line=dict(color='red'),
                name='Macchina selezionata')
    )
    

    setup_sx, setup_dx = st.columns([1,3])
    with setup_sx:
        st.subheader('Riepilogo setup per macchina')
        df_all_count
    with setup_dx:
        st.subheader('Andamento durata media setup | Confronto con la media di stabilimento')
        st.plotly_chart(confronto, use_container_width=True)



# setup
# andamento di tutto il reparto
# possibilità di confrontare due macchine | include la possibilità di confrontare una macchina con la media del reparto


# andamento del numero di setup
# andamento della durata dei setup
# 
