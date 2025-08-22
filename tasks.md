# Tasks
* Create a Github action that will auto build a Java SDK used for building type safe graphql clients against the nf-graphql services.  It should be able to point to a given environment when building and should be kicked off manually on the nf-graphql-subgraph-template repository whenever we want a new SDK generated.
* Remove the top level shadowDom and fix styling issues due to this from imedia-header-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-firelight-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-ssc-client-accounts-list-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-beneficiaries-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-ssc-my-business-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-client-details-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-megamenu-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-agreement-details-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-account-header-mfe.
* Remove the top level shadowDom from the imedia-mfe-template repository.
* Update the pipeline documentation to explain how to use the Harness deployment pipeline for MFE deployment.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-header-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-firelight-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-ssc-client-accounts-list-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-beneficiaries-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-ssc-my-business-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-client-details-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-megamenu-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-agreement-details-mfe.
* Implement the template pipeline migration changes to GHA, this means migration to harness deployment,  for the MFE  imedia-account-header-mfe.
* Setup a Java Library repository to provide an annotation for launch darkly to populate a property in java very similarto how property loading works.
* Update the configuration and secrets used by nf-graphql-services to properly align with the new launch darkly configuration available.
* Update the imedia-wc-shared repository to include a new Launch Darkly component based on this: https://github.nwie.net/Nationwide/launch-darkly-angular?tab=readme-ov-file#angular-integration.  It should be configured to use the default Launch Darkly config file for SSC. If one doesn't exist yet we need to set it up for each environment in imedia-json.  We should use the shared library config service to retrieve it.
* Agreement Restrictions table in CPPF is not being returned for agreements today.  We should add that as a new field on agreement object and provide a dataloader pattern child fetcher for retrieval of that information.
 