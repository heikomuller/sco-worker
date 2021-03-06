# Standard Cortical Observer Worker Process - Changelog

### 0.1.0 - 2017-03-16

* Initial Version

### 0.2.0 - 2017-03-18

* Adjust worker to new format for model run requests and responses

### 0.2.1 - 2017-03-19

* Bug fix in rabbitmq_worker
* Add MongoDB database name as command line argument for rabbitmq_worker

### 0.3.0 - 2017-03-20

* Pass optional experiment fMRI data to model run as ground truth data

### 0.3.1 - 2017-03-21

* Fix minor bug in SCODataStoreWorker.run()


### 0.3.2 - 2017-05-04

* Adjust code to changes in sco-datastore 0.5

### 0.3.3 - 2017-05-19

* Add missing dependencies

### 0.3.4 - 2017-05-19

* Adjust upload to handle prediction result and attachments

### 0.4.0 - 2017-06-27

* Fix bug with sco_run
* Add handling of attachments that are defined as part of a model output

### 0.5.0 - 2017-06-29

* Adjust to merge of sco-models into sco-engine and other API changes

### 0.5.1 - 2017-07-02

* Adjust to new format of model run attachments

### 0.5.2 - 2017-07-03

* Fix bugs in remote worker
