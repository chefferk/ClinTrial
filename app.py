import requests
import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
from OpenFDA import OpenFDA
from ClinicalTrials import ClinicalTrials


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


def show():
    if "page" not in st.session_state:
        st.session_state.page = 1

    st.title("ClinTrials")
    form = st.form(key="query_form")
    query = form.text_input(label="Query")
    col1, col2 = form.beta_columns(2)
    study_type = col1.selectbox(
        "Study Type",
        [
            "All Studies",
            "Interventional Studies (Clinical Trials)",
            "Observational Studies",
            "Expanded Access Studies",
        ],
    )
    study_results = col2.selectbox(
        "Study Results",
        ["All Studies", "Studies With Results", "Studies Without Results"],
    )
    col1, col2 = form.beta_columns(2)
    study_status = col1.multiselect(
        "Study Status",
        [
            "Not yet recruiting",
            "Recruiting",
            "Enrolling by invitation",
            "Active, not recruiting",
            "Suspended",
            "Terminated",
            "Completed",
            "Withdrawn",
            "Unknown status",
        ],
    )
    phase = col2.multiselect(
        "Phase",
        [
            "Early Phase 1",
            "Phase 1",
            "Phase 2",
            "Phase 3",
            "Phase 4",
            "Not Applicable",
        ],
    )
    submit_button = form.form_submit_button(label="Search")

    if submit_button:
        end = st.session_state.page * 5
        start = end - 4
        # hack
        try:
            temp = phase
        except Exception as e:
            phase = []
        try:
            temp = status
        except Exception as e:
            status = []

        with st.spinner(text="Searching..."):
            ct = ClinicalTrials()
            full_studies = ct.get_filtered_full_studies(
                query,
                phase=phase,
                status=study_status,
                study_results=study_results,
                study_type=study_type,
                min_rank=start,
                max_rank=end,
            )

            try:
                studies = full_studies["FullStudiesResponse"]["FullStudies"]
            except Exception as e:
                st.warning("No results found, please try again.")
                return
            st.subheader("Results:")
            st.markdown(
                f"`Total studies found: {full_studies['FullStudiesResponse']['NStudiesFound']}`"
            )
            st.markdown("""---""")

            for study in studies:
                data = study["Study"]

                # header
                nctid = data["ProtocolSection"]["IdentificationModule"]["NCTId"]
                st.markdown(
                    f"### [{nctid}](https://clinicaltrials.gov/ct2/show/{nctid})"
                )

                try:
                    phase = data["ProtocolSection"]["DesignModule"]["PhaseList"][
                        "Phase"
                    ][0]
                except Exception as e:
                    print(e)
                    phase = "Unknown"
                # st.markdown(f"`{phase}`")

                study_typ = data["ProtocolSection"]["DesignModule"]["StudyType"]

                rec_status = data["ProtocolSection"]["StatusModule"]["OverallStatus"]
                status_color = {
                    "Not yet recruiting": "success",
                    "Recruiting": "success",
                    "Enrolling by invitation": "success",
                    "Active, not recruiting": "warning",
                    "Suspended": "danger",
                    "Terminated": "danger",
                    "Completed": "info",
                    "Withdrawn": "danger",
                    "Unknown status": "danger",
                    "No longer available": "danger",
                    "Approved for marketing": "warning",
                }

                st.markdown(
                    f'<span class="badge badge-pill badge-secondary"> {phase} </span> <span class="badge badge-pill badge-{status_color[rec_status]}"> {rec_status} </span> <span class="badge badge-pill badge-dark"> {study_typ} </span>',
                    unsafe_allow_html=True,
                )

                title = data["ProtocolSection"]["IdentificationModule"]["BriefTitle"]
                st.write(title)

                try:
                    sponsor = data["ProtocolSection"]["SponsorCollaboratorsModule"][
                        "LeadSponsor"
                    ]["LeadSponsorName"]
                except Exception as e:
                    sponsor = False

                if sponsor:
                    st.write("###### Sponsor:")
                    st.write(f"- {sponsor}")
                # st.markdown(
                #     f"""<div class='card' style='width: 100%'>
                #         <div class='card-body'>
                #             <h3 class='card-title'><a href='#'>{nctid}</a></h3>
                #             <span class="badge badge-pill badge-success"> {phase} </span> <span class="badge badge-pill badge-secondary"> {rec_status} </span>
                #             <h6 class='card-subtitle mb-2 text-muted'>{title}</h6>
                #             </div></div><br>
                #         """,
                #     unsafe_allow_html=True,
                # )

                with st.beta_expander("Interventions"):

                    l = data["ProtocolSection"]["ArmsInterventionsModule"][
                        "InterventionList"
                    ]["Intervention"]

                    for k in l:
                        dname = k["InterventionName"]
                        intervention_type = k["InterventionType"]
                        # st.write(f"- {intervention_type}: {dname}")

                        try:
                            links = list(set(query_fda(dname)))
                            if len(links) == 0:
                                links = ["No label"]
                        except Exception as e:
                            links = ["No label"]

                        if links[0] == "No label":
                            st.write(f"- {intervention_type}: {dname}")
                        else:
                            st.write(
                                f"- {intervention_type}: {dname} [label]({links[0]})"
                            )

                with st.beta_expander("References", expanded=False):
                    try:
                        refs = data["ProtocolSection"]["ReferencesModule"][
                            "ReferenceList"
                        ]["Reference"]
                    except Exception as e:
                        refs = []
                        st.write("- No publications associated with trial results")

                    for j in refs:
                        text = j["ReferenceCitation"]
                        try:
                            link = (
                                f"https://pubmed.ncbi.nlm.nih.gov/{j['ReferencePMID']}/"
                            )
                            st.write(f"- [{text}] ({link})")
                        except Exception as e:
                            st.write(f"- {text}")
                st.markdown("""---""")

            col1, col2, col3 = st.beta_columns(3)

            if st.session_state.page < 4:
                col3.button(">")
            else:
                col3.write("")  # this makes the empty column show up on mobile

            if st.session_state.page > 1:
                col1.button("<")
            else:
                col1.write("")  # this makes the empty column show up on mobile

            # TODO: we should rould up, not just convert to int
            print(int(full_studies["FullStudiesResponse"]["NStudiesFound"]))
            col2.write(
                f"Page {st.session_state.page} of {int(int(full_studies['FullStudiesResponse']['NStudiesFound'])/5)}"
            )


if __name__ == "__main__":
    st.markdown(
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">',
        unsafe_allow_html=True,
    )

    show()
