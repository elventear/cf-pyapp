# cloudfoundry-lite

Integrated enviroment to deploy the AppFirst collector on a bosh-lite Cloud Foundry deploy.

## Requirements

* Ruby 2.1
* [go](https://golang.org/)
* [Vagrant](https://www.vagrantup.com/) >= 1.6.3 
* [Virtualbox](https://www.virtualbox.org/) 

## Init enviroment

	> git submodule update --init
	> source .env
	> go get github.com/cloudfoundry-incubator/spiff
	> gem install bosh_cli

## Deploy CF

	> cd bosh-lite
	> vagrant up
	> ./bin/provision_cf 
        > ./bin/add-route

## Login to CF

        > cf api --skip-ssl-validation https://api.10.244.0.34.xip.io
        > cf auth admin admin
        > cf create-org me
        > cf target -o me
        > cf create-space development
        > cf target -s development

