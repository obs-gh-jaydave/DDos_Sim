PROJECT_NAME=ddos-sim
AWS_REGION=us-west-2
ACCOUNT_ID=$(shell aws sts get-caller-identity --query Account --output text)
REPO_URI=$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(PROJECT_NAME)

build:
	docker build -t $(PROJECT_NAME) .

tag:
	@echo "Tagging image for ECR..."
	docker tag $(PROJECT_NAME):latest $(REPO_URI):latest

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(REPO_URI)

push: build tag ecr-login
	docker push $(REPO_URI):latest

deploy:
	kubectl apply -f k8s/ddos-cronjob.yaml