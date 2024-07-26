# %%
import requests
import json
import pandas as pd
from tqdm import tqdm

# %%
client_id = ""
cle_secrete = ""
scope = ""
#scope = "api_stats-informations-territoirev1 infosterritoire"

# %% [markdown]
# codes_bassin = ['8428', '1126', '1126', '7532', '1127', '7514', '7514', '8413', '8413', '8405', '7617', '8432'] #, '1126', '2417', '9308', '1126', '2817', '9307', '5301', '1126', '5317', '7532', '9326', '9307', '1126', '1139', '1126', '9307', '7617', '1126', '2421', '2421', '1126', '1126', '1129', '8426', '2801', '8428', '9306', '1139', '9333', '1139', '4449', '1107', '2814', '1118', '7540', '5205', '1138', '3216', '5227', '1126', '1126', '2421', '1125', '1125', '3214', '1107', '1107', '1107', '1126', '1139', '9333', '1146', '1126', '2415', '8413', '1126', '1126', '7532', '9326', '9333', '5301', '7608', '1126', '7617', '8428', '8412', '5220', '9311', '5314', '7617', '9326', '8432', '1126', '9305', '7617', '1126', '9326', '1126']  
# #["1126","1107"]     # certains codes (8244 par ex.) ne marchent pas, investiguer
# 
# type_activite = "CUMUL"
# #type_activite = "ROME"     # pas basé sur les FAP 225 mais sur le ROME
# 
# activites = ["CUMUL",]
# #activites = ["D1202","D1102"]

# %%
def auth_api_pôle_emploi(client_id, cle_secrete, scope):

    url = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=partenaire"

    payload = 'client_id=' + client_id + '&client_secret=' + cle_secrete + \
        '&grant_type=client_credentials&scope=' + scope
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # Vérifiez si la requête a réussi
    if response.status_code == 200:
        data = response.json()
        # print(data)
    else:
        print("Erreur lors de la récupération des données " +
              str(response.status_code))

    token = json.loads(response.text)['access_token']
    # print(tk)

    return token

# %% [markdown]
# token = auth_api_pôle_emploi(client_id, cle_secrete, scope)

# %%
def requête_api_marché_du_travail(token, codes_bassin, type_activite, activites):

    url = "https://api.pole-emploi.io/partenaire/stats-offres-demandes-emploi/v1/indicateur/"

    headers = {
            'Authorization': 'Bearer ' + str(token),
            'Accept': "application/json",
            'Content-Type': 'application/json'
        }

    GETurl = url + "stat-perspective-employeur"

    API_outputs_list = []

    # for code_bassin in tqdm(codes_bassin, "Requête des bassins (par métier sélectionné)"):
    for code_bassin in codes_bassin:
    
        for activite in activites :
        
            payload = {
                'codeTypeTerritoire':'BASBMO',
                'codeTerritoire': code_bassin,
                'codeTypeActivite': type_activite,
                'codeActivite': activite,
                "codeTypePeriode": "ANNEE",
                "codeTypeNomenclature": "TYPE_TENSION"
                #"dernierePeriode": True,
                }
            
            #print(payload)
            json_payload = json.dumps(payload)

            response = requests.request("POST", GETurl, headers=headers, data=json_payload)


            # Vérifiez si la requête a réussi
            if response.status_code == 200 or response.status_code == 206:
                data = response.json()
                #print(data)
                #print(type(data))
                API_outputs_list.append(data)
            else:
                # Affichez un message d'erreur si la requête n'a pas réussi
                error_message = ("Erreur lors de la récupération des données " + str(response.status_code) + "- code bassin = " + code_bassin + " / code activité = " + activite)
                data = error_message
                API_outputs_list.append(data)

                print(response.text)

    return API_outputs_list

# %% [markdown]
# data = requête_api_marché_du_travail(token, codes_bassin, type_activite, activites)

# %% [markdown]
# data

# %%
def api_output_to_df(API_outputs_list):

    if type(API_outputs_list) not in [dict,list]:
        #json_file = json.dumps({0:data})
        df = pd.DataFrame
        print("error")
        
    else:
        database_list = []
        for output in API_outputs_list:
            
            if output["listeValeursParPeriode"]:

                for elem in output["listeValeursParPeriode"]:
                    row = []
                    row = [elem["libNomenclature"],elem["codePeriode"],elem["codeTerritoire"], elem["libTerritoire"], elem["codeActivite"], elem["libActivite"], elem["valeurPrincipaleNom"]]

                    database_list.append(row)

        df = pd.DataFrame.from_records(database_list)

        df = df.rename(columns={
            0:"Indicateur", 
            1:"Année",
            2:"Code bassin",
            3:"Nom bassin",
            4:"Code activité",
            5:"Nom activité",
            6:"Valeur"
            })

    return df

# %%
def api_output_to_json(data):

    if type(data) != dict:
        json_file = json.dumps({0:data})
        
    else:
        dict_perspectives = {
            "Conditions de travail":[],
            "Durabilité de l'emploi":[],
            "Intensité d'embauche":[],
            "Manque de main d'oeuvre":[],
            "Inadéquation géographique":[],
            "Indicateur principal tension":[],
            "Lien formation - métier":[]
            }


        for elem in data["listeValeursParPeriode"]:
            
            dict_periode = {}

            dict_periode[elem["codePeriode"]] = elem["valeurPrincipaleNom"]

            dict_perspectives[elem["libNomenclature"]].append(dict_periode)
        
        #print(dict_perspectives)

        json_file = json.dumps(dict_perspectives, ensure_ascii=True)

    return json_file

# %% [markdown]
# def main():
#     token = auth_api_pôle_emploi(client_id, cle_secrete, scope)
#     API_outputs_list = requête_api_marché_du_travail(token, codes_bassin, type_activite, activites)
#     #json = api_output_to_json(data)
#     df = api_output_to_df(API_outputs_list)
# 
#     return df

# %% [markdown]
# if __name__ == "__main__":
#     main()

# %% [markdown]
# df = main()

# %% [markdown]
# df

# %%



