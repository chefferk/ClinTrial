from utils import json_handler


class ClinicalTrials:

    _BASE_URL = "https://clinicaltrials.gov/api/"
    _INFO = "info/"
    _QUERY = "query/"
    _JSON = "fmt=json"

    def __init__(self):
        self.api_info = self.__api_info()

    @property
    def study_fields(self):
        fields_list = json_handler(
            f"{self._BASE_URL}{self._INFO}study_fields_list?{self._JSON}"
        )
        return fields_list["StudyFields"]["Fields"]

    def __api_info(self):
        """Returns information about the API"""
        last_updated = json_handler(
            f"{self._BASE_URL}{self._INFO}data_vrs?{self._JSON}"
        )["DataVrs"]
        api_version = json_handler(f"{self._BASE_URL}{self._INFO}api_vrs?{self._JSON}")[
            "APIVrs"
        ]

        return api_version, last_updated

    def get_full_studies(self, search_expr, min_rank=1, max_rank=10):
        """Returns all content for a maximum of 100 study records.

        Retrieves information from the full studies endpoint, which gets all study fields.
        This endpoint can only output JSON (Or not-supported XML) format and does not allow
        requests for more than 100 studies at once.

        Args:
            search_expr (str): A string containing a search expression as specified by
                `their documentation <https://clinicaltrials.gov/api/gui/ref/syntax#searchExpr>`_.
            max_studies (int): An integer indicating the maximum number of studies to return.
                Defaults to 50.

        Returns:
            dict: Object containing the information queried with the search expression.

        Raises:
            ValueError: The number of studies can only be between 1 and 100
        """
        if max_rank > 100 or max_rank < 1:
            raise ValueError("The number of studies can only be between 1 and 100")

        req = f"full_studies?expr={search_expr}&min_rnk={min_rank}&max_rnk={max_rank}&{self._JSON}"

        full_studies = json_handler(f"{self._BASE_URL}{self._QUERY}{req}")

        return full_studies

    def get_study_fields(self, search_expr, fields, min_rank=1, max_rank=50):
        """Returns study content for specified fields

        Retrieves information from the study fields endpoint, which acquires specified information
        from a large (max 1000) studies. To see a list of all possible fields, check the class'
        study_fields attribute.

        Args:
            search_expr (str): A string containing a search expression as specified by
                `their documentation <https://clinicaltrials.gov/api/gui/ref/syntax#searchExpr>`_.
            fields (list(str)): A list containing the desired information fields.
            max_studies (int): An integer indicating the maximum number of studies to return.
                Defaults to 50.
            fmt (str): A string indicating the output format, csv or json. Defaults to csv.

        Returns:
            Either a dict, if fmt='json', or a list of records (e.g. a list of lists), if fmt='csv.
            Both containing the maximum number of study fields queried using the specified search expression.

        Raises:
            ValueError: The number of studies can only be between 1 and 1000
            ValueError: One of the fields is not valid! Check the study_fields attribute
                for a list of valid ones.
            ValueError: Format argument has to be either 'csv' or 'json'
        """
        if max_rank > 1000 or max_rank < 1:
            raise ValueError("The number of studies can only be between 1 and 1000")
        elif not set(fields).issubset(self.study_fields):
            # TODO: this could be more specific and tell user which field is invalid
            raise ValueError(
                "One of the fields is not valid! Check the study_fields attribute for a list of valid ones."
            )
        else:
            concat_fields = ",".join(fields)
            req = f"study_fields?expr={search_expr}&min_rnk={min_rank}&max_rnk={max_rank}&fields={concat_fields}"

            url = f"{self._BASE_URL}{self._QUERY}{req}&{self._JSON}"
            return json_handler(url)

    def get_filtered_full_studies(
        self,
        search_expr,
        min_rank=1,
        max_rank=5,
        study_type="All Studies",
        study_results="All Studies",
        phase=[],
        status=[],
    ):
        # 1. buid expression
        query = [search_expr]
        if len(phase) != 0:
            internal = []
            for p in phase:
                internal.append(f"AREA[Phase]{p}")
            phase_str = " OR ".join(internal)
            query.append(f"AND ({phase_str})")

        if study_type != "All Studies":
            query.append(f"AND AREA[StudyType]{study_type}")

        if len(status) != 0:
            internal = []
            for s in status:
                internal.append(f"AREA[OverallStatus]{s}")
            status_str = " OR ".join(internal)
            query.append(f"AND ({status_str})")

        if study_results != "All Studies":
            if study_results == "Studies With Results":
                query.append("NOT(AREA[ResultsFirstPostDate]MISSING)")
            else:
                query.append("AREA[ResultsFirstPostDate]MISSING")

        search_exp = " ".join(query)

        print(search_exp)

        # 2. call api
        full_studies = self.get_full_studies(
            search_exp, min_rank=min_rank, max_rank=max_rank
        )

        return full_studies

    def get_filtered_full_studies_old(
        self,
        search_expr,
        min_rank=1,
        max_rank=10,
        study_type="All Studies",
        study_results="All Studies",
        phase="All Phases",
        status="All Statuses",
    ):
        # 1. get study fields of expresion and above fields
        #    NOTE: will need to loop over these until we have fill coverage of NStudiesFound

        study_fields = self.get_study_fields(
            search_expr,
            fields=["Phase", "StudyType", "ResultsFirstSubmitDate", "OverallStatus"],
            max_rank=50,
        )

        # 2. get list of all ranks that match the given filters
        filtered_ranks = []
        for study in study_fields["StudyFieldsResponse"]["StudyFields"]:
            if phase == "All Phases":
                correct_phase = True
            else:
                correct_phase = study["Phase"][0][-1] == str(phase)

            if study_type == "All Studies":
                correct_type = True
            else:
                correct_type = study["StudyType"][0] == study_type

            if study_results == "All Studies":
                correct_result = True
            else:
                if study_results == "Studies With Results":
                    correct_result = len(study["ResultsFirstSubmitDate"]) != 0
                else:
                    correct_result = len(study["ResultsFirstSubmitDate"]) == 0

            if status == "All Statuses":
                correct_status = True
            else:
                correct_status = study["OverallStatus"][0] == status

            if correct_phase and correct_result and correct_status and correct_type:
                filtered_ranks.append(study["Rank"])

        # 3. call full studies with given ranks enough times to return max_rank
        full_studies = []
        for rank in filtered_ranks[:max_rank]:
            study = self.get_full_studies(search_expr, min_rank=rank, max_rank=rank)
            full_studies.append(study)

        return full_studies

    def get_filtered_study_fields_old(
        self,
        search_expr,
        min_rank=1,
        max_rank=10,
        study_type="All Studies",
        study_results="All Studies",
        phase="All Phases",
        status="All Statuses",
    ):
        # 1. get study fields of expresion and above fields
        #    NOTE: will need to loop over these until we have fill coverage of NStudiesFound

        study_fields = self.get_study_fields(
            search_expr,
            fields=[
                "Phase",
                "StudyType",
                "ResultsFirstSubmitDate",
                "OverallStatus",
                "BriefTitle",
                "NCTId",
            ],
            max_rank=50,
        )

        # 2. get list of all ranks that match the given filters
        filtered_studies = []
        for study in study_fields["StudyFieldsResponse"]["StudyFields"]:
            if phase == "All Phases":
                correct_phase = True
            else:
                correct_phase = study["Phase"][0][-1] == str(phase)

            if study_type == "All Studies":
                correct_type = True
            else:
                correct_type = study["StudyType"][0] == study_type

            if study_results == "All Studies":
                correct_result = True
            else:
                if study_results == "Studies With Results":
                    correct_result = len(study["ResultsFirstSubmitDate"]) != 0
                else:
                    correct_result = len(study["ResultsFirstSubmitDate"]) == 0

            if status == "All Statuses":
                correct_status = True
            else:
                correct_status = study["OverallStatus"][0] == status

            if correct_phase and correct_result and correct_status and correct_type:
                filtered_studies.append(study)

        return filtered_studies[:max_rank]
