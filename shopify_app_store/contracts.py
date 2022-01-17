# -*- coding: utf-8 -*-

from scrapy.contracts import Contract
from scrapy.exceptions import ContractFail
import json


class MetaContract(Contract):
    """ Contract to set the meta arguments for the request.
    The value should be a JSON-encoded dictionary, e.g.:

        @meta {"key": "value"}
    """

    name = 'meta'

    def adjust_request_args(self, args):
        args['meta'] = json.loads(' '.join(self.args))
        return args


class OutputMatchesContract(Contract):
    """ Contract to assert the output items.
    The value should be a path (inside the /contracts/ directory) to the
    json file that contains expected output items.

        @output_matches parse_app/file.json
    """

    CONTRACTS_SPEC_DIR = './contracts/'

    name = 'output_matches'

    def post_process(self, output):
        contract_file_path = '{}{}'.format(self.CONTRACTS_SPEC_DIR, self.args[0])
        expected_output = json.load(open(contract_file_path, 'r'))
        actual_output = list(map(lambda item: self.skip_dynamic_keys(dict(item)), output))

        if expected_output != actual_output:
            raise ContractFail(
                "Output doesn't match. Actual: %s. Expected: %s" % (actual_output, expected_output))

    @staticmethod
    def skip_dynamic_keys(dictionary):
        dynamic_keys = {'id', 'pricing_plan_id'}
        return {k: dictionary[k] for k in dictionary.keys() - dynamic_keys}
