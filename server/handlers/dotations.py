from Simulation_engine.simulate_dotations import simulate


class Dotations(object):

    def check_field(self, node, field_name):
        if "field_name" not in node:
            return {
                "Error": "Missing '{0}' field in request body. Parent node is: {1}".format(
                    field_name, node
                    )
                }, 400
        pass

    def check_request_format(self, request_body):
        self.check_field(request_body, "reforme")
        self.check_field(request_body["reforme"], "dotations")
        self.check_field(request_body["reforme"]["dotations"], "montants")
        self.check_field(request_body["reforme"]["dotations"]["montants"], "dgf")
        self.check_field(request_body["reforme"]["dotations"], "communes")
        self.check_field(request_body, "description_cas_types")

    def simule_dotations(**params: dict) -> tuple:
        request_body = params["body"]
        self.check_request_format(request_body)

        # calculer
        simulation_result = simulate(request_body)

        # constuire la réponse
        return simulation_result, 200
