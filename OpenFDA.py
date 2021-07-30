import requests

class OpenFDA:
    def __init__(self, term):
        self.term = term
        self.data = self.run_query()

    def run_query(self):
        r = requests.get(
            f"https://api.fda.gov/drug/drugsfda.json?search={self.term}&limit=100"
        )
        return r.json()

    def get_ndas(self):
        ndas = []
        for i in self.data["results"]:
            if i["application_number"][0] == "N" or i["application_number"][0] == "B":
                ndas.append(i)
        return ndas

    def has_correct_dose(self, data, dose):
        products = data["products"]
        correct_dose = []
        for product in products:
            # NOTE: this is very basic and will require more
            for ing in product["active_ingredients"]:
                if str(dose) in ing["strength"]:
                    correct_dose.append(True)
                else:
                    correct_dose.append(False)

        if True in correct_dose:
            return True
        else:
            return False

    def has_correct_route(self, data, route):
        products = data["products"]
        correct_route = []
        for product in products:
            # NOTE: this is very basic and will require more
            try:
                if route.lower() in product["route"].lower():
                    correct_route.append(True)
                else:
                    correct_route.append(False)
            except Exception as e:
                correct_route.append(False)

        if True in correct_route:
            return True
        else:
            return False

    def get_correct_result(self, ndas, dose=None, route=None):
        """Returns the result with brand name == term name
        """
        correct = []
        for result in ndas:
            # NOTE: this is very basic and will require more
            if self.has_correct_dose(result, dose) or self.has_correct_route(
                result, route
            ):
                correct.append(result)
        return correct

    def get_latest_submission(self, nda):
        submissions = nda["submissions"]
        if len(submissions) == 1:
            return submissions
        else:
            highest = 0
            for submission in submissions:

                if int(submission["submission_number"]) > highest:
                    highest = int(submission["submission_number"])

            for submission in submissions:
                if int(submission["submission_number"]) == highest:
                    return submission

    def get_label_link(self, data):
        try:
            docs = data["application_docs"]
            for doc in docs:
                if doc["type"] == "Label":
                    return doc["url"]
        except Exception as e:
            return None

    def temp(self):
        labels = []
        for i in data["results"]:
            if i["application_number"][0] == "N":
                try:
                    d = data["results"][0]["submissions"]
                    df = pd.DataFrame.from_dict(d)
                    df["submission_number"] = (
                        df["submission_number"].astype(str).astype(int)
                    )
                    df = df.sort_values("submission_number")

                    for i in df.iloc[-1].application_docs:
                        if i["type"] == "Label":
                            labels.append(i["url"])
                        else:
                            labels.append("No label")
                except Exception as e:
                    labels.append("No label")
        return labels
