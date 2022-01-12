import pprint
from json import dumps, loads
from urllib import parse

import requests

import base_ccloud

pp = pprint.PrettyPrinter(indent=2)
SA_VALUE = {}


def cache_sa(url, params, value_dict):
    resp = requests.get(url=url, auth=base_ccloud.BASIC_AUTH, params=params)
    if resp.status_code == 200:
        out_json = resp.json()
        for item in out_json["data"]:
            value_dict[item["id"]] = item
        if 'next' in out_json['metadata']:
            query_params = parse.parse_qs(
                parse.urlsplit(out_json['metadata']['next']).query)
            params['page_token'] = str(query_params['page_token'][0])
            cache_sa(url=url, params=params, value_dict=value_dict)
    else:
        raise Exception("Could not connect to Confluent Cloud. Please check your settings. "
                        + resp.text)


def print_sa_table(sa_dict):
    for v in sa_dict.values():
        print("{:<15} {:<40} {:<50}".format(
            v["id"], v["display_name"], v["description"]))


def check_existing_sa(sa_name, sa_dict):
    for v in sa_dict.values():
        if sa_name in v["display_name"]:
            # print("Service Account already exists. Returning back the existing details.")
            return v
    return None


def create_sa(sa_name):
    print("No Existing Service Account found with name: " + sa_name)
    print("Creating a new Service Account with name: " + sa_name)
    payload = {
        "display_name": sa_name,
        "description": str("Account for " + sa_name + " created by CI/CD framework")
    }
    resp = requests.post(
        url=str(base_ccloud.CCLOUD_URL + base_ccloud.URI_LIST['sa']), json=payload, auth=base_ccloud.BASIC_AUTH, )
    sa_details = loads(resp.text)
    pp.pprint(sa_details)
    return sa_details


def run_sa_workflow(svc_account_name="", create_account=False, force_new_account=False):
    if not (svc_account_name):
        raise Exception('Service Account name is missing')

    sa_values = {}
    cache_sa(base_ccloud.CCLOUD_URL + base_ccloud.URI_LIST['sa'],
             {"page_size": 20}, value_dict=sa_values)
    # print(len(sa_values))
    # print_sa_table(sa_values)

    sa_details = check_existing_sa(svc_account_name, sa_values)
    if (force_new_account) and (sa_details is not None):
        print("Service Account found with name " + svc_account_name +
              " but --force-new-account flag is checked, so will try to create another account. ", )
        for i in range(1, 99999):
            temp_name = svc_account_name + str(i)
            sa_check = check_existing_sa(temp_name, sa_values)
            if sa_check is None:
                svc_account_name = temp_name
                sa_details = None
                break
            else:
                print("Service account exists with name " +
                      temp_name + " as well. Will keep retrying.")
    if sa_details is None:
        if create_account:
            sa_details = create_sa(svc_account_name)
        else:
            print("Could not find a Service Account with display name " +
                  svc_account_name + " and account creation was not allowed.")
    else:
        print("Service Account found with name " + svc_account_name)
        pp.pprint(sa_details)
    global SA_VALUE
    SA_VALUE = sa_details

    if sa_details:
        with open('sa_values.json', 'w', encoding="utf-8") as output_file:
            output_file.write(dumps(sa_details))
            print("The details of service account are added to " + output_file.name)
    else:
        print("Did not update/write the output file as service account was not found.")

    return SA_VALUE


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Command line arguments for controlling the application", add_help=True, )
    sa_args = parser.add_argument_group("sa-args", "Service Account Arguments")
    sa_args.add_argument('--service-account-name', type=str, default="",
                         help="Provide the name for which Service Account needs to be created.",)
    sa_args.add_argument('--create-service-account-if-necessary', action="store_true", default=False,
                         help="Provide the name for which Service Account needs to be created.",)
    sa_args.add_argument('--force-new-account', action="store_true", default=False,
                         help="Force Generate a new Service Account even if an account exists with the same Name",)
    sa_args.add_argument('--add-as-rest-proxy-user', action="store_true", default=False,
                         help="Add the Service Account to REST Proxy users",)

    args = parser.parse_args()

    base_ccloud.initial_setup(False)
    run_sa_workflow(args.service_account_name if hasattr(
        args, "service_account_name") else "", True, args.force_new_account)
