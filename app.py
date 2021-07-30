import requests
import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
from OpenFDA import OpenFDA


def query_fda(term):
    ofda = OpenFDA(term)
    ndas = ofda.get_ndas()

    if len(ndas) == 0:
        print("No NDAs")
        return []

    correct = ofda.get_correct_result(ndas, dose=60, route="INTRAVENOUS")

    if len(correct) == 0:
        print("None correct")
        labels = []
        for res in ndas:
            latest = ofda.get_latest_submission(res)

            if type(latest) is list:
                latest = latest[0]

            label = ofda.get_label_link(latest)

            if label is not None:
                labels.append(label)
        return labels

    print(f"Number correct: {len(correct)}")

    labels = []
    for res in correct:
        latest = ofda.get_latest_submission(res)

        if type(latest) is list:
            latest = latest[0]

        label = ofda.get_label_link(latest)

        if label is not None:
            labels.append(label)
    return labels


def query_clin_trials():
    if st.session_state.query_value == "":
        return None

    r = requests.get(
        f"https://www.clinicaltrials.gov/api/query/full_studies?expr={st.session_state.query_value}&min_rnk=1&max_rnk=5&fmt=json&rslt=With"
    )

    if r.status_code != 200:
        st.warning("ERROR: Could not run query")
        return

    return r.json()


def process_data(data):
    st.markdown(
        f"`Total studies found: {data['FullStudiesResponse']['NStudiesFound']}`"
    )
    st.markdown(
        f"`Total studies showing: {data['FullStudiesResponse']['NStudiesReturned']}`"
    )
    st.markdown("""---""")
    for i in range(len(data["FullStudiesResponse"]["FullStudies"])):

        temp_data = data["FullStudiesResponse"]["FullStudies"][i]["Study"]

        # header
        nctid = temp_data["ProtocolSection"]["IdentificationModule"]["NCTId"]
        st.markdown(f"### [{nctid}](https://clinicaltrials.gov/ct2/show/{nctid})")

        title = temp_data["ProtocolSection"]["IdentificationModule"]["BriefTitle"]
        st.write(title)

        # interventions
        st.markdown("#### Interventions:")
        try:
            l = temp_data["ProtocolSection"]["ArmsInterventionsModule"][
                "InterventionList"
            ]["Intervention"]

            for k in l:
                # print(k["InterventionName"])
                dname = k["InterventionName"]
                try:
                    links = list(set(query_fda(dname)))
                except Exception as e:
                    links = ["No label"]
                # link = "#"

                intervention_type = k["InterventionType"]

                links = [f"[label] ({link})" for link in links if link != "No label"]

                st.write(f"- {intervention_type}: {dname} ({', '.join(links)})")

        except Exception as e:
            ...

        # refs
        st.markdown("#### References:")
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


if __name__ == "__main__":

    st.title("ClinTrials")

    query_value = st.text_input(
        "Query",
        key="query_value",
        help="Seperate multiple items by commas",
        on_change=None,
    )

    # st.selectbox(
    #     "Study Results",
    #     ["All Studies", "Studies With Results", "Studies Without Results"],
    # )

    search = st.button("Search")

    if search:
        data = query_clin_trials()

        if data is not None and data["FullStudiesResponse"]["NStudiesReturned"] != 0:
            process_data(data)
        else:
            st.warning("No results found")
