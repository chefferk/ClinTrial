import requests
import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

query = st.text_input("Query")
search = st.button("Search")


def search_button_pressed():
    ...


def query_fda(term):
    r = requests.get(f"https://api.fda.gov/drug/drugsfda.json?search={term}&limit=100")
    data = r.json()

    d = data["results"][0]["submissions"]
    df = pd.DataFrame.from_dict(d)
    df["submission_number"] = df["submission_number"].astype(str).astype(int)
    df = df.sort_values("submission_number")

    for i in df.iloc[-1].application_docs:
        if i["type"] == "Label":
            return i["url"]
        else:
            return "No label"


def get_data(query):
    # f"https://www.clinicaltrials.gov/api/query/full_studies?expr={query}&min_rnk=1&max_rnk=2&fmt=json"
    r = requests.get(
        f"https://www.clinicaltrials.gov/api/query/full_studies?expr={query}&min_rnk=1&max_rnk=10&fmt=json"
    )
    print(r.status_code)

    data = r.json()

    print(r.url)

    for i in range(len(data["FullStudiesResponse"]["FullStudies"])):

        temp_data = data["FullStudiesResponse"]["FullStudies"][i]["Study"]

        # header
        nctid = temp_data["ProtocolSection"]["IdentificationModule"]["NCTId"]
        st.write(f"[{nctid}](https://clinicaltrials.gov/ct2/show/{nctid})")

        title = temp_data["ProtocolSection"]["IdentificationModule"]["BriefTitle"]
        st.write(title)

        # interventions
        st.write("Drugs:")
        try:
            l = temp_data["ProtocolSection"]["ArmsInterventionsModule"][
                "InterventionList"
            ]["Intervention"]

            print(" ")
            print(l)
            print(" ")
            for k in l:
                # print(k["InterventionName"])
                dname = k["InterventionName"]
                # link = query_fda(dname)
                link = "#"

                print(dname, link)

                if link != "No label":
                    st.write(f"- [{dname}] ({link})")
                else:
                    st.write(f"- {dname} (no label)")
        except Exception as e:
            ...

        # refs
        st.write("References:")
        try:
            refs = temp_data["ProtocolSection"]["ReferencesModule"]["ReferenceList"][
                "Reference"
            ]
        except Exception as e:
            refs = []
            st.write("- No publications associated with trial results")

        for j in refs:
            text = j["ReferenceCitation"]
            try:
                link = f"https://pubmed.ncbi.nlm.nih.gov/{j['ReferencePMID']}/"
                st.write(f"- [{text}] ({link})")
            except Exception as e:
                st.write(f"- {text}")

        st.markdown("""---""")


if search:
    get_data(query)