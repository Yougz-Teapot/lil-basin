# %% [markdown]
# # Librairies/Modules

# %%
import pandas as pd
import geopandas as gpd

# %%
import folium
from folium.plugins import Search, TagFilterButton
from folium import IFrame
from shapely.geometry import Point

# %%
import streamlit as st
from streamlit_folium import st_folium, folium_static

# %%
import poleemploi as pe

# %%
import os
from datetime import datetime
# from icecream import ic

# %%
from memory_profiler import profile

# %% [markdown]
# # Paramètres

# %% [markdown]
# ##### BMO

# %%
BMO_csv = "source_files/BMO/Base_open_data_23.csv"
BMO_csv = "source_files/BMO/Base_open_data_BMO_2024.csv"

#job_filter = ["A0Z40", "A0Z41"]
job_filter = ["E1Z41"]
#job_families_selection = ["Ouvriers des secteurs de l'industrie"]
#job_families_selection = ["Ouvriers de la construction et du bâtiment"]

# %% [markdown]
# ##### Etablissements

# %%
folder_ets = "source_files/etablissements/"
codes_naf = ["42", "41"]
extension = "-geocoded.csv"

fichiers_ets = [os.path.join(folder_ets, code_naf + extension) for code_naf in codes_naf]

filtre_tranches = ["21","22", "31", "32","41","42","51","52","53"]

# filtre_tranches = None

# %% [markdown]
# #### API Pôle Emploi

# %%
client_id = ""
cle_secrete = ""
scope = ""

# %%
codes_bassins = ['8428', '1126', '1126', '7532', '1127', '7514', '7514', '8413', '8413', '8405', '7617', '8432'] #, '1126', '2417', '9308', '1126', '2817', '9307', '5301', '1126', '5317', '7532', '9326', '9307', '1126', '1139', '1126', '9307', '7617', '1126', '2421', '2421', '1126', '1126', '1129', '8426', '2801', '8428', '9306', '1139', '9333', '1139', '4449', '1107', '2814', '1118', '7540', '5205', '1138', '3216', '5227', '1126', '1126', '2421', '1125', '1125', '3214', '1107', '1107', '1107', '1126', '1139', '9333', '1146', '1126', '2415', '8413', '1126', '1126', '7532', '9326', '9333', '5301', '7608', '1126', '7617', '8428', '8412', '5220', '9311', '5314', '7617', '9326', '8432', '1126', '9305', '7617', '1126', '9326', '1126']  
#["1126","1107"]     # certains codes (8244 par ex.) ne marchent pas, investiguer

type_activite = "CUMUL"
#type_activite = "ROME"     # pas basé sur les FAP 225 mais sur le ROME

activites = ["CUMUL",]
#activites = ["D1202","D1102"]

# %% [markdown]
# #### Streamlit config

# %%
st.set_page_config(layout="wide")
st.sidebar.title("Petit Bassin")
# st.sidebar.image("./source_files/logo-sextant-mini.png") #, use_column_width=True)

text = "_Etablissements (>50 employés) & Tensions de recrutement dans les bassins d'emploi_"
# st.sidebar.write(text)
st.sidebar.subheader(text)
st.sidebar.write("_> établissements des divisions 41 (Construction de bâtiment) et 42 (Génie civil)_")

st.sidebar.header("", divider="rainbow")

st.sidebar.subheader("Filtres")

# %% [markdown]
# # Construction des bases de données

# %% [markdown]
# ## Données : contours bassins (Base A)

# %%
@st.cache_data
def load_bassins_shapes():
    gdf_bassins_shapes = gpd.read_file("source_files/fonds/fond_bassins2021.json")
    gdf_bassins_shapes = gdf_bassins_shapes.rename(columns={"lib_bassin_BMO2021":"Bassin", "code_bassin_BMO2021":"Code_Bassin"})

    return gdf_bassins_shapes

# %% [markdown]
# gdf_bassins_shapes = load_bassins_shapes()

# %% [markdown]
# ## Données : BMO (base A)

# %% [markdown]
# ### Import

# %%
@st.cache_data
def load_BMO_data(BMO_csv):
    data_BMO = pd.read_csv(BMO_csv, sep=";", encoding="utf-8")
    #data_BMO = pd.read_excel(BMO, sheet_name="BMO_2023_open_data")

    return data_BMO

# %% [markdown]
# data_BMO = load_BMO_data(BMO_csv)

# %% [markdown]
# ### Retraitements

# %%
@st.cache_data
def retreat_BMO_data(data_BMO):
    
    data_BMO = data_BMO.rename(columns={"NOMBE24":"Bassin", "BE24":"Code_Bassin"})

    data_BMO = data_BMO.drop(columns="smet").dropna()

    data_BMO['met'] = pd.to_numeric(data_BMO['met'], errors='coerce')
    data_BMO['xmet'] = pd.to_numeric(data_BMO['xmet'], errors='coerce')

    if "part_difficiles" in data_BMO.columns:
        data_BMO['part_difficiles'] = pd.to_numeric(data_BMO['part_difficiles'].str.replace(',', '.'), errors='coerce')
    else:
        data_BMO['part_difficiles'] = data_BMO['xmet'] / data_BMO['met']

    data_BMO['REG'] = data_BMO['REG'].astype(str)
    data_BMO['Code_Bassin'] = data_BMO['Code_Bassin'].astype(str)

    return data_BMO

# %% [markdown]
# data_BMO = retreat_BMO_data(data_BMO)

# %% [markdown]
# ## Base A interim : base BMO géographiée

# %% [markdown]
# ### Fusion données BMO & contours bassins

# %%
def merge_bassins_x_BMO(data_BMO, gdf_bassins_shapes):
    df_bassins_x_BMO = pd.merge(data_BMO, gdf_bassins_shapes, left_on="Code_Bassin", right_on="Code_Bassin", how='left')

    df_bassins_x_BMO[df_bassins_x_BMO["geometry"].isnull()]["Bassin_x"].unique()

    return df_bassins_x_BMO

# %% [markdown]
# df_bassins_x_BMO = merge_bassins_x_BMO(data_BMO, gdf_bassins_shapes)

# %% [markdown]
# ### Launch base

# %%
@st.cache_data
def launch_bassins_x_BMO():
    gdf_bassins_shapes = load_bassins_shapes()
    data_BMO = load_BMO_data(BMO_csv)
    data_BMO = retreat_BMO_data(data_BMO)
    df_bassins_x_BMO = merge_bassins_x_BMO(data_BMO, gdf_bassins_shapes)

    return df_bassins_x_BMO

# %%
df_bassins_x_BMO = launch_bassins_x_BMO()

# %% [markdown]
# ### Construction table correspondance métiers/familles métier

# %%
@st.cache_data
def map_job_jobfamilies(df_bassins_x_BMO):
    df_mapping_job_jobfam = df_bassins_x_BMO[["Code métier BMO", "Nom métier BMO", "Famille_met", "Lbl_fam_met"]]
    df_mapping_job_jobfam = df_mapping_job_jobfam.drop_duplicates(subset=["Code métier BMO"])
    mapping_job_jobfam = df_mapping_job_jobfam.set_index("Nom métier BMO").to_dict(orient='index')

    return mapping_job_jobfam

# %%
mapping_job_jobfam = map_job_jobfamilies(df_bassins_x_BMO)

# %% [markdown]
# ### Filtrage/Aggrégation des métiers sélectionnés

# %%
def filter_aggregate_BMO_jobs(df_bassins_x_BMO, job_families_selection=None, jobs_selection=None):

    # FILTRAGE DES (FAMILLES) DE METIERS

    #df_bassins_x_BMO_jobFiltered = df_bassins_x_BMO[df_bassins_x_BMO["Code métier BMO"].isin(job_filter)]
    if job_families_selection != None:
        df_bassins_x_BMO_jobFiltered = df_bassins_x_BMO[df_bassins_x_BMO["Lbl_fam_met"].isin(job_families_selection)]
    elif jobs_selection != None:
        df_bassins_x_BMO_jobFiltered = df_bassins_x_BMO[df_bassins_x_BMO["Nom métier BMO"].isin(jobs_selection)]
    else:
        df_bassins_x_BMO_jobFiltered = df_bassins_x_BMO


    # AGGREGATION ET CALCUL DE LA TENSION MOYENNE PAR BASSIN

    df_bassins_x_BMO_jobFilteredAggregated = df_bassins_x_BMO_jobFiltered.groupby('Code_Bassin').agg({
    'xmet': 'sum', 
     'met': 'sum',
     'geometry':'first',
     'Bassin_y':'first',
     'NomDept':'first'
     })

    df_bassins_x_BMO_jobFilteredAggregated = df_bassins_x_BMO_jobFilteredAggregated.reset_index()

    df_bassins_x_BMO_jobFilteredAggregated['part_difficiles'] = df_bassins_x_BMO_jobFilteredAggregated['xmet'] / df_bassins_x_BMO_jobFilteredAggregated['met']

    # Optional: Fill NaN values with a default value (e.g., 0) if there are groups with no 'met' values
    df_bassins_x_BMO_jobFilteredAggregated['part_difficiles'].fillna(0, inplace=True)

    df_bassins_x_BMO_jobFilteredAggregated['part_difficiles_pourcentage'] = (df_bassins_x_BMO_jobFilteredAggregated['part_difficiles'] * 100).round().astype(int).astype(str) + '%'

    df_bassins_x_BMO_jobFilteredAggregated["Code_Bassin"] = df_bassins_x_BMO_jobFilteredAggregated['Code_Bassin'].str.zfill(4)

    gdf_BMO_jobFilteredAggregated = gpd.GeoDataFrame(df_bassins_x_BMO_jobFilteredAggregated, geometry="geometry")

    return gdf_BMO_jobFilteredAggregated

# %%
gdf_BMO_jobFilteredAggregated = filter_aggregate_BMO_jobs(df_bassins_x_BMO)

# %% [markdown]
# ## Données : Indicateurs de tension PE/DARES [DEV - Tests en cours] (Base A)
# 
# - Intégrer à la carto
# - Peut-être revoir la structuration des données à la source dans le module py poleemploi plutôt que de de pivoter la base ici ?

# %% [markdown]
# ### Extraction du geodataframe BMO des codes bassin à requêter

# %%
codes_bassins = gdf_BMO_jobFilteredAggregated["Code_Bassin"].unique().tolist()
codes_bassins = codes_bassins[0:2]

# %% [markdown]
# ### Requête des indicateurs de tension par bassin et par métier (ROME) via le module poleemploi (HTH)

# %%
def request_extra_tensionindicators():
    
    try:
        token = pe.auth_api_pôle_emploi(client_id, cle_secrete, scope)
        API_outputs_list = pe.requête_api_marché_du_travail(token, codes_bassins, type_activite, activites)
        df_extraindicateurs_tension = pe.api_output_to_df(API_outputs_list)
    except Exception as e:
        print(e)
        df_extraindicateurs_tension = pd.DataFrame()
        return df_extraindicateurs_tension

    ### Traitement du dataframe Pôle Emploi (pivotage des valeurs/indicateurs de lignes à colonnes)
    df_extraindicateurs_tension["ID"] = df_extraindicateurs_tension["Code bassin"] + "_" + df_extraindicateurs_tension["Année"]  #constitution d'un ID unique pour pivotage
    df_extraindicateurs_tension["Valeur"] = df_extraindicateurs_tension["Valeur"].astype("int")
    subdf_indicateurs_pivoté = df_extraindicateurs_tension.pivot_table(index='ID', columns='Indicateur', values='Valeur', aggfunc='first') # crée une sous-table avec les valeurs dépivotées
    df_extraindicateurs_tension = pd.merge(df_extraindicateurs_tension, subdf_indicateurs_pivoté, how='left', on='ID') # recollage de la sous-table
    df_extraindicateurs_tension = df_extraindicateurs_tension.drop_duplicates(subset="ID").drop(['Indicateur', 'Valeur'], axis=1) # suppression des doublons

    df_extraindicateurs_tension = df_extraindicateurs_tension[df_extraindicateurs_tension["Année"]=="2023"] # Filtrage des lignes non-pertinentes pour l'année en cours (mais peut-être inclure sous une forme à l'avenir)

    return df_extraindicateurs_tension

# %%
df_extraindicateurs_tension = request_extra_tensionindicators()

# %%
if df_extraindicateurs_tension.empty:
    include_dares_data = False
else:
    include_dares_data = True

# %% [markdown]
# API_outputs_list[320]

# %% [markdown]
# for i, output in enumerate(API_outputs_list):
#     try:
#         elemx = output["listeValeursParPeriode"]
#     except Exception as e :
#         print()
#         print(f"ERREUR : \n{e}")
#         print(f"INDEX : {i}")
#         print(f"OUTPUT : \n{output}")
# 

# %% [markdown]
# ## Base A : Bassins avec indicateurs de tension (BMO + complémentaires PE/DARES)

# %% [markdown]
# ### Fusion geobase BMO + base indicateurs complémentaires PE/DARES

# %%
def fusion_BMO_x_indicateurs_PE_DARES(gdf_BMO_jobFilteredAggregated, df_extraindicateurs_tension):

    if df_extraindicateurs_tension.empty:
        df_tensionsBassins = gdf_BMO_jobFilteredAggregated
    else:
        df_tensionsBassins = pd.merge(gdf_BMO_jobFilteredAggregated, df_extraindicateurs_tension , how="left", left_on="Code_Bassin", right_on="Code bassin")
        df_tensionsBassins.drop(columns=["Code bassin", "Nom bassin"])

    gdf_tensionsBassins = gpd.GeoDataFrame(df_tensionsBassins, geometry="geometry", crs="EPSG:4326")

    return gdf_tensionsBassins

# %%
gdf_tensionsBassins = fusion_BMO_x_indicateurs_PE_DARES(gdf_BMO_jobFilteredAggregated, df_extraindicateurs_tension)

# %% [markdown]
# ### Essai de graph léger des indicateurs pour intégration aux étiquettes de cartes

# %% [markdown]
# import plotly.express as px
# 
# 
# radar_columns = gdf_tensionsBassins.columns[gdf_tensionsBassins.columns.get_loc('Conditions de travail'):]  # Selecting columns right of 'ID' for the radar chart
# 
# fig = px.line_polar(gdf_tensionsBassins, r=gdf_tensionsBassins[radar_columns].values[1], theta=radar_columns, line_close=True)  # Creating a radar chart using plotly
# 
# fig.update_layout(title='Radar Chart based on ID values', legend=dict(traceorder='reversed')) # Adding title and legend
# 
# fig.show() # Show the plot

# %%
# buffer = io.BytesIO()
# fig.write_image(buffer, format="png", width=100, height=100)

# image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

# html_radar_chart = fig.to_html(full_html=False)
# len(html_radar_chart)
# gdf_tensionsBassins["html_radar"] = f'data:image/png;base64,{image_base64}'
# gdf_tensionsBassins

# %% [markdown]
# ## Base B : Etablissements

# %% [markdown]
# ### .csv to df

# %%
@st.cache_data
def load_ets_data(fichiers_ets):

    concat_df_ets = pd.DataFrame()

    for fichier_ets in fichiers_ets:
    
        df_ets = pd.read_csv(fichier_ets, sep=";", encoding="utf-8")
        concat_df_ets = pd.concat([concat_df_ets, df_ets])

    concat_df_ets["denominationUniteLegale"] = concat_df_ets["denominationUniteLegale"].astype(str)
    concat_df_ets["result_label"] = concat_df_ets["result_label"].astype(str)

    return concat_df_ets

# %% [markdown]
# df_ets = load_ets_data(fichiers_ets)

# %% [markdown]
# ### Filtrage selon la taille

# %%
def filter_ets_data(df_ets, filtre_tranches):
    if filtre_tranches != None:
        df_ets_filtered = df_ets[df_ets['trancheEffectifsEtablissement'].isin(filtre_tranches)]
    else:
        df_ets_filtered = df_ets

    return df_ets_filtered

# %% [markdown]
# df_ets_filtered = filter_ets_data(df_ets, filtre_tranches)

# %% [markdown]
# ### Ajout des intitulés à partir des codes : tranches d'effectif + code APE

# %% [markdown]
# #### intitulés tranches d'effectif

# %%
@st.cache_data
def load_intitulés_tranches_effectif():
    tranches_effectifs_path = "source_files/tables/Tranches_effectifs.csv"
    df_tranches = pd.read_csv(tranches_effectifs_path, sep=';')
    return df_tranches

# %%
df_tranches = load_intitulés_tranches_effectif()

# %% [markdown]
# df_ets_filtered_augment_w_effectifs = pd.merge(df_ets_filtered, df_tranches, "left" , left_on="trancheEffectifsEtablissement", right_on="CodeTranche")

# %% [markdown]
# #### intitulés APE

# %%
@st.cache_data
def load_intitulés_naf():
    # intitulés_naf_path = r"source_files/tables/table_NAF.xlsx"
    intitulés_naf_path = r"source_files/tables/table_NAF.csv"
    # df_intitulés_naf = pd.read_excel(intitulés_naf_path, sheet_name="Table_NAF")
    df_intitulés_naf = pd.read_csv(intitulés_naf_path, sep=';')

    return df_intitulés_naf

# %% [markdown]
# df_intitulés_naf = load_intitulés_naf()

# %% [markdown]
# df_ets_filtered_augment_w_intitulés = pd.merge(df_ets_filtered_augment_w_effectifs, df_intitulés_naf, how="left", left_on="activitePrincipaleEtablissement", right_on="code APE")

# %% [markdown]
# df_ets_filtered_augment_w_intitulés.drop() #évaluer ici quoi drop() si besoin d'alléger base

# %% [markdown]
# geometry = [Point(xy) for xy in zip(df_ets_filtered_augment_w_intitulés['longitude'], df_ets_filtered_augment_w_intitulés['latitude'])]
# gdf_etablissements = gpd.GeoDataFrame(df_ets_filtered_augment_w_intitulés, geometry=geometry, crs="EPSG:4326")

# %% [markdown]
# ### Launch base

# %%
@st.cache_data
def launch_ets():
    df_ets = load_ets_data(fichiers_ets)
    df_ets_filtered = filter_ets_data(df_ets, filtre_tranches)
    df_ets_filtered_augment_w_effectifs = pd.merge(df_ets_filtered, df_tranches, "left" , left_on="trancheEffectifsEtablissement", right_on="CodeTranche")
    df_intitulés_naf = load_intitulés_naf()
    df_ets_filtered_augment_w_intitulés = pd.merge(df_ets_filtered_augment_w_effectifs, df_intitulés_naf, how="left", left_on="activitePrincipaleEtablissement", right_on="code APE")
    
    geometry = [Point(xy) for xy in zip(df_ets_filtered_augment_w_intitulés['longitude'], df_ets_filtered_augment_w_intitulés['latitude'])]
    gdf_etablissements = gpd.GeoDataFrame(df_ets_filtered_augment_w_intitulés, geometry=geometry, crs="EPSG:4326")

    return gdf_etablissements

# %%
gdf_etablissements = launch_ets()

# %% [markdown]
# # Export HTML

# %%
def export_to_html(m) -> None:
    current_time = datetime.now().strftime("%Y-%m-%d %Hh%M")
    # export_folder = "./"
    export_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    export_name = f"Petit bassin export map {current_time}.html"
    export_path = os.path.join(export_folder, export_name)
    #print(export_path)
    m.save(export_path)

    st.sidebar.write(f"Export sauvegardé !\n\n{export_path}")

# %% [markdown]
# # Exploration carto / Streamlit main

# %% [markdown]
# ### Méthode 1 (principale à date) : Ajout etablissements via un folium.featureGroup en bouclant les rows du gdf. Permet :
# 1. d'attribuer des tags à chaque élément, nécessaire pour les boutons filtres a priori impossible via gpd.explore() ou folium.GeoJson()
# 2. accessoirement, une définition de taille de bulle plus simple qu'avec la solution trouvée depuis (style_function lambda)
# 3. mais la définition élément par élément de la couche Etablissement ne semble pas permettre de fournir un search_field à la fonction Search

# %% [markdown]
# #### UTILISER session_state pour reconstruire la dépendence des valeurs de la selectbox métiers aux valeurs de celle Famille métier
# #### cf. https://chat.openai.com/share/1b332429-00a7-4fd5-a8e3-63c934fc6e30

# %%
def generate_folium_map(include_dares_data=False):

    m = folium.Map(location=(45.7678, 2.6017), tiles="cartodb positron", zoom_start=6) # reset carte     # width="100%", height="80%", tiles="cartodb positron")


    # DYNAMIQUE DE FILTRE DES BASES

    codes_APE: list[str] = sorted(gdf_etablissements["Sous-classes (APE)"].unique().tolist())
    job_families : list[str] = sorted(df_bassins_x_BMO["Lbl_fam_met"].unique().tolist())
    jobs : list[str] = sorted(df_bassins_x_BMO["Nom métier BMO"].unique().tolist())
    etablissements : list[str] = sorted(gdf_etablissements["denominationUniteLegale"].unique().tolist())

    APE_selectbox = st.sidebar.multiselect("Code APE", options=codes_APE)
    job_families_selectbox = st.sidebar.multiselect("Famille pro", options=job_families)
    jobs_selectbox = st.sidebar.multiselect("Métier", options=jobs)
    st.sidebar.divider()
    etablissements_selectbox = st.sidebar.multiselect("Etablissements", options=etablissements)
    
    if APE_selectbox != []:
        gdf_etablissements_filtered = gdf_etablissements[gdf_etablissements["Sous-classes (APE)"].isin(APE_selectbox)]
    elif etablissements_selectbox != []:
        gdf_etablissements_filtered = gdf_etablissements[gdf_etablissements["denominationUniteLegale"].isin(etablissements_selectbox)]
    elif APE_selectbox != [] and etablissements_selectbox != []:
        gdf_etablissements_filtered = gdf_etablissements[gdf_etablissements["Sous-classes (APE)"].isin(APE_selectbox)]
        gdf_etablissements_filtered = gdf_etablissements_filtered[gdf_etablissements["denominationUniteLegale"].isin(etablissements_selectbox)]
    else:
        gdf_etablissements_filtered = gdf_etablissements

    
    if job_families_selectbox != [] and jobs_selectbox == []:

        gdf_BMO_jobFilteredAggregated = filter_aggregate_BMO_jobs(df_bassins_x_BMO, job_families_selection=job_families_selectbox)
        df_extraindicateurs_tension = request_extra_tensionindicators()
        gdf_tensionsBassins_filtered = fusion_BMO_x_indicateurs_PE_DARES(gdf_BMO_jobFilteredAggregated, df_extraindicateurs_tension)
        jobs_codes = [x for (x,y) in mapping_job_jobfam.items() if y["Lbl_fam_met"] in job_families_selectbox]

    elif jobs_selectbox != []:
    #elif job_families_selectbox != [] and jobs_selectbox != []:

        gdf_BMO_jobFilteredAggregated = filter_aggregate_BMO_jobs(df_bassins_x_BMO, jobs_selection=jobs_selectbox)
        df_extraindicateurs_tension = request_extra_tensionindicators()
        gdf_tensionsBassins_filtered = fusion_BMO_x_indicateurs_PE_DARES(gdf_BMO_jobFilteredAggregated, df_extraindicateurs_tension)

    else:
        gdf_tensionsBassins_filtered = gdf_tensionsBassins
    


    # CARTOGRAPHIE

    if include_dares_data:
        tooltip=["Code_Bassin", "Bassin_y", "met", "part_difficiles_pourcentage", "Conditions de travail", "Durabilité de l'emploi", "Inadéquation géographique", "Intensité d'embauche", "Lien formation - métier", "Manque de main d'oeuvre"]
        tooltip_kwds={
            "aliases": ["Code bassin d'emploi", "Bassin d'emploi", "Projets de recrutements déclarés", "Part déclarée difficile", "Conditions de travail (tension/5)", "Durabilité de l'emploi (tension/5)", "Inadéquation géographique (tension/5)", "Intensité d'embauche (tension/5)", "Lien formation - métier (tension/5)", "Manque de main d'oeuvre (tension/5)"],
            "style": """font-size: 13px;"""
        }
    else:
        tooltip=["Code_Bassin", "Bassin_y", "met", "part_difficiles_pourcentage"]
        tooltip_kwds={
            "aliases": ["Code bassin d'emploi", "Bassin d'emploi", "Projets de recrutements déclarés", "Part déclarée difficile"],
            "style": """font-size: 13px;"""
        }

    gdf_tensionsBassins_filtered.explore(
        m=m,
        column="part_difficiles",
        scheme="naturalbreaks",  # use mapclassify's natural breaks scheme
        cmap="YlOrRd", # 'viridis'
        legend=True,  # show legend
        k=10,  # use 10 bins

        #tooltip=False,  # hide tooltip
        tooltip=tooltip,
        tooltip_kwds=tooltip_kwds,

        # tooltip=tooltip,
        # tooltip_kwds=tooltip_kwds,
        legend_kwds=dict(caption="Part de recrutements difficiles", colorbar=True),  # display use colorbar,
        name="Bassins",  # name of the layer in the map
    )

    ets_layer = folium.FeatureGroup(name='Etablissements')

    ##### Add the circles to the feature group
    for idx, row in gdf_etablissements_filtered.iterrows():
        name = row["denominationUniteLegale"]+" ("+row['result_label']+")"
        if not row.geometry.is_empty:
            folium.CircleMarker(location=[row.geometry.y, row.geometry.x],
                                #radius=row['taille_bulle'],
                                radius=row["TailleBullePixels"],
                                fill=True,
                                color='#0091D3', # 'red'
                                tooltip=f"<div style='font-size: 13px;'><b>{row['denominationUniteLegale']}</b><br>{row['Intitulé sous-classe (code APE) <40 caractères']}<br>{row['Effectifs']}<br>{row['result_label']}</div>",
                                name=name,
                                tags=[row["activitePrincipaleEtablissement"], row["Effectifs"]]                  
                                #tooltip_kwds={
                                    #'aliases': ["Etablissement", "Tranche d'effectif", "Adresse"],
                                    #"style": """font-size: 12px;""",
                                    #'max_width': 800
                                    #},
                                ).add_to(ets_layer)
        

    ets_layer.add_to(m)


    search_bassin = Search(
        layer=ets_layer,
        geom_type="CircleMarker",
        placeholder="Rechercher des établissements",
        collapsed=False,
        #search_label=name,
        weight=3,
        ) #.add_to(m)


    tranches = gdf_etablissements_filtered["Effectifs"].unique().tolist()
    #tranches_triées = sorted(tranches_brut, key=lambda s: int(s.split(" à")[0].replace(" ", "")))
    mask = df_tranches['Effectifs'].isin(tranches)  # Step 1: Create a boolean mask by checking if values in the column match those in the list
    tranches_triées = df_tranches.loc[mask, 'Effectifs'].tolist()  # Step 2: Use the boolean mask to filter the DataFrame and retrieve the matching values

    APEs = gdf_etablissements_filtered["Sous-classes (APE)"].unique().tolist()

    filter_button_tranches = TagFilterButton(tranches_triées, clear_text="Effacer", open_popup_on_hover=True).add_to(m)
    # filter_button_APE = TagFilterButton(APEs, clear_text="Effacer").add_to(m)         # filtrage inopérant, à creuser


    ##### Add LayerControl to the map
    folium.LayerControl(collapsed=False).add_to(m)

    #st_data = st_folium(m, width=1000, height=800)
    st_data = folium_static(m, width=1000, height=800)


    return m



# %% [markdown]
# # Carte

# %%
m = generate_folium_map(include_dares_data = include_dares_data)

# %% [markdown]
# m

# %%
# st.sidebar.divider()
# if st.sidebar.button('> Export'):
#     export_to_html(m)

st.sidebar.header("", divider="rainbow")
st.sidebar.write("_:grey[Mars 2023  -  Hugo T.]_")


