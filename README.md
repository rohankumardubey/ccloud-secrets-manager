# Confluent Cloud Service Account and API Key Management Automation Package

Service accounts(SA) and API Keys(Keys) are used to interact with Confluent Cloud Kafka Clusters. These Kafka clusters exist in logical Environments. The SA are created at a Organization level and Keys are linked to an SA and Kafka Cluster. 

Currently, there are CLI and API tools available to generate and work with SA & API Keys but no direct path with CI/CD flows integration. This project aims to solve that. The core definitions of all the Service Accounts and necessary API Key bindings will be maintained in a single definitions file. This definitions file is a YAML structured file that will be used to maintain all definitions in a single location.

The project will use that definitions file to set up Service accounts as well as to generate API Keys. After generating API Key/Secret pair; it will also append the API Key/Secret combo to a Secret Management layer of your choice all while adding tags to the secret for quick management and search capability.

The long term aim of this integration is as follows:
- [X] Allow creation of Service Accounts using standardized YAML structure
- [X] Allow creation of API Keys for the corresponding SA automatically
- [X] Allow storing the SA & API Key details into a pluggable Secrets manager for ease of management and greater flexibility - Done for AWS Secrets Manager with more to follow.
- [ ] Enable Permission management for the pluggable Secret Manger, so that it can become one stop shop for Confluent Cloud secret management - Not started yet.
- [ ] Add API Key Rolling logic
- [ ] Add REST Proxy Access logic.
- [ ] Add Login and connectivity test logic for Secret Management framework.


## Quickstart

Ensure that you have the following installed on system that this utility will be run on:
* [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* [AWS Token signed in or environment variables set up as this utility will not make an attempt for AWS login.](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
*  [Install Confluent CLI](https://docs.confluent.io/confluent-cli/current/install.html)
```
https://github.com/waliaabhishek/ccloud-secrets-manager
pip install requirements.txt
python3 main_yaml_runner.py <<Additional Switches required as mentioned below>>
```

There is a Dockerfile that could be used to generate an image which will not modify your system, but will create a new python image and install the necessary utilities in that image to run the project. 

## Switches

The execution starts with base python file `main_yaml_runner.py`. This file has the following switches available: 

* `--csm-config-file-path`: This is the configuration file path that will provide connectivity and other config details. Sample file is available inside the configurations folder with name `config.yaml`
* `--csm-definitions-file-path`: This is the definition file path that will provide resource definitions for execution in CCloud. Sample file is available inside the configurations folder with name `definitions.yaml`
* `--csm-generate-definitions-file`: This switch can be used for initial runs where the team does not have a definitions file and would like to auto generate one from existing ccloud resource mappings. 
* `--dry-run`: This switch can be used to invoke a dry run and list all actions that will be preformed, but not performing them.
* `--disable-api-key-creation`: This switch can be used to disable API Key & Secret creation (if required)
* `--print-delete-eligible-api-keys`: This switch can be used to print the API keys which are not synced to the Secret store and (potentially) not used.

## File Descriptors

### Configuration File

Sample file : `./configurations/config.yaml`

NOTE: A point to note for all the following configs is that you can use environment variable replacement trigger by using the format `env::<ENV_VARIABLE_NAME>` to tell the program to find the environment variable by the name of ENV_VARIABLE_NAME and replace it before using it as the value. 

There are 2 main sections in the configurations file:
* `configs`: Contains configurations for Confluent Cloud and Secret Store
  * `ccloud_configs`: Contains all the configurations related to Confluent Cloud.
    * `api_key: <string>`: Confluent Cloud API Key that could be used to invoke the CCloud API. Also known as the `cloud` API Key. 
    * `api_secret: <string>`: Secret for the corresponding API key.
    * `ccloud_user: <string>`: The CCloud user are required till the time API Keys cannot be generated with its own API. The only way right now is to use the CCloud CLI and that needs an username/password combo for invocation.
    * `ccloud_password: <string>`: Password for the corresponding CCloud username.
    * `enable_sa_cleanup: <boolean>`: Service Account deletion is not enabled by default and could be enabled with this switch if desired.
    * `detect_ignore_ccloud_internal_accounts: <boolean>`: This configuration determines which service accounts were generated by the CCloud internal automations like fully managed ksqlDB cluster & Fully managed Connectors. This may or may not always be successful as Service Account naming scheme may change at anytime within Confluent Cloud; yet I will try to keep it as optimal as possible.
    * `ignore_service_account_list: <list<string>>`: These could be service account resource IDs that the team may not want this utility to track.
  * `secret_store`: Contains all configurations related to the Secret manager.
    * `enabled: <boolean>`: Secret Stores will only be enabled if this switch is turned to true. 
    * `type: <string>`: Currently can only take one value string `aws-secretsmanager`. More options will hopefully be available as I get more time to work on the utility.
    * `prefix: <string>`: If you would like to have a constant string prefixed to every secret path, this is the setting to use. Defaults to `""`
    * `separator: <string>`: If you would like to have a constant separating different tokens used in the secret path, this is the setting to use. Defaults to `/`
    * `configs: <list<name-value pairs>>`: This is a placeholder for any ancillary configurations that may be needed for any other Secret Management store. Currently not used. 

### Definitions File

Sample File : `./configurations/definitions.yaml`

This is a much simpler file at the moment. Here's the structure:
* `service_accounts: <list>`: Contains list of Service Accounts that will be created and its details. 
  * Repeating node:
    * `name: <string>`: This is the Display name of the Service account and serves as more like a primary key from a customer's perspective. When a Service Account is generated, a unique resource ID is created and linked to this Display Name. If you change this value, the program will try to create a new Service account instead of updating the existing one as there is no state maintained in the project.
    * `description: <string>`: You can provide the description to use here. If left empty, the project will generate a description for you.
    * `team_email_address: <string>`: Currently unused, but is planned to be used with an EMail utility to ship the freshly created API Key and Secret to the correct team.
    * `enable_rest_proxy_access: <boolean>`: Currently unused, but is planned to be used as the base for generating the Confluent REST Proxy username/password configurations for Basic Auth <-> Confluent kafka Auth. This could be used with K8s based Confluent REST Proxy deployments to enable automated access management for REST proxy instead of adding/removing users manually from the configurations every time it is desired. 
    * `api_key_access: <list<string>>`: This list can be used to tell the project to generate API Keys for Service Account linked to a specific Confluent Cloud Cluster. It needs Confluent Cloud Cluster Resource ID to understand the mapping properly. You can provide a ist of cluster IDs for which the API keys need to be generated -or- it also has a special keyword that could be used to automatically create API Keys linked to all clusters in every environment within CCloud for that Service Account. This could really come in handy if you have a lot of clusters and would like to provision API Keys for all clusters automatically. The keyword is `FORCE_ALL_CLUSTERS`. If the keyword is provided, all other cluster names are ignored. 